# -*- coding: utf-8 -*-
"""Persistência das execuções em SQLite, para a fila sobreviver a reinícios."""
import json
import sqlite3
import threading
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta

from servico import config

STATUS_NA_FILA = "na_fila"
STATUS_EXECUTANDO = "executando"
STATUS_CONCLUIDO = "concluido"
STATUS_FALHOU = "falhou"
STATUS_CANCELADO = "cancelado"
STATUS_VALIDOS = {STATUS_NA_FILA, STATUS_EXECUTANDO, STATUS_CONCLUIDO, STATUS_FALHOU, STATUS_CANCELADO}

NAVEGADOR_OCULTO = "oculto"
NAVEGADOR_INTERATIVO = "interativo"
NAVEGADORES_VALIDOS = {NAVEGADOR_OCULTO, NAVEGADOR_INTERATIVO}

_COLUNAS_ADICIONADAS = {
    "navegador": "TEXT NOT NULL DEFAULT 'oculto'",
    "captura": "TEXT",
    "lancamentos": "TEXT",
    "lancamentos_resumo": "TEXT",
    "pendencias": "TEXT",
}

_ESQUEMA = """
CREATE TABLE IF NOT EXISTS execucoes (
    id TEXT PRIMARY KEY,
    modo TEXT,
    planilha_base TEXT,
    planilha_verbas TEXT,
    solicitante TEXT,
    origem TEXT,
    chave_idempotencia TEXT UNIQUE,
    status TEXT NOT NULL,
    mensagem TEXT,
    erro TEXT,
    arquivos TEXT,
    criado_em TEXT NOT NULL,
    iniciado_em TEXT,
    concluido_em TEXT
);
CREATE TABLE IF NOT EXISTS execucao_log (
    execucao_id TEXT NOT NULL,
    seq INTEGER NOT NULL,
    hora TEXT NOT NULL,
    mensagem TEXT NOT NULL,
    PRIMARY KEY (execucao_id, seq)
);
"""

_trava = threading.Lock()


def agora():
    return datetime.now().isoformat(timespec="seconds")


@contextmanager
def _conectar():
    conexao = sqlite3.connect(config.DB_PATH, timeout=10)
    conexao.row_factory = sqlite3.Row
    try:
        with conexao:
            yield conexao
    finally:
        conexao.close()


def inicializar():
    with _trava, _conectar() as conexao:
        conexao.execute("PRAGMA journal_mode=WAL")
        conexao.executescript(_ESQUEMA)
        existentes = {linha["name"] for linha in conexao.execute("PRAGMA table_info(execucoes)")}
        for coluna, definicao in _COLUNAS_ADICIONADAS.items():
            if coluna not in existentes:
                conexao.execute(f"ALTER TABLE execucoes ADD COLUMN {coluna} {definicao}")


def _para_dict(linha):
    if linha is None:
        return None
    registro = dict(linha)
    registro["arquivos"] = json.loads(registro["arquivos"]) if registro["arquivos"] else []
    registro["lancamentos_resumo"] = json.loads(registro["lancamentos_resumo"]) if registro.get("lancamentos_resumo") else None
    registro["pendencias"] = json.loads(registro["pendencias"]) if registro.get("pendencias") else []
    registro.pop("chave_idempotencia", None)
    registro["duracao_seg"] = None
    if registro["iniciado_em"]:
        fim = datetime.fromisoformat(registro["concluido_em"]) if registro["concluido_em"] else datetime.now()
        registro["duracao_seg"] = int((fim - datetime.fromisoformat(registro["iniciado_em"])).total_seconds())
    return registro


def criar(planilha_base, planilha_verbas, solicitante, origem, chave_idempotencia, navegador=NAVEGADOR_OCULTO,
          lancamentos=None, lancamentos_resumo=None):
    execucao_id = uuid.uuid4().hex[:12]
    resumo = json.dumps(lancamentos_resumo, ensure_ascii=False) if lancamentos_resumo is not None else None
    with _trava, _conectar() as conexao:
        conexao.execute(
            "INSERT INTO execucoes (id, planilha_base, planilha_verbas, solicitante, origem,"
            " chave_idempotencia, navegador, lancamentos, lancamentos_resumo, status, criado_em)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (execucao_id, planilha_base, planilha_verbas, solicitante, origem,
             chave_idempotencia, navegador, lancamentos, resumo, STATUS_NA_FILA, agora()),
        )
    return obter(execucao_id)


def obter(execucao_id):
    with _conectar() as conexao:
        linha = conexao.execute("SELECT * FROM execucoes WHERE id = ?", (execucao_id,)).fetchone()
    return _para_dict(linha)


def obter_por_chave(chave_idempotencia):
    with _conectar() as conexao:
        linha = conexao.execute(
            "SELECT * FROM execucoes WHERE chave_idempotencia = ?", (chave_idempotencia,)
        ).fetchone()
    return _para_dict(linha)


def _filtros_sql(status=None, modo=None, busca=None, criado_de=None, criado_ate=None):
    condicoes, parametros = [], []
    if status:
        condicoes.append("status = ?")
        parametros.append(status)
    if modo:
        condicoes.append("modo = ?")
        parametros.append(modo)
    if busca:
        termo = "%" + busca.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
        colunas = ("id", "planilha_base", "planilha_verbas", "lancamentos", "solicitante", "origem", "mensagem")
        condicoes.append("(" + " OR ".join(f"{c} LIKE ? ESCAPE '\\'" for c in colunas) + ")")
        parametros.extend([termo] * len(colunas))
    if criado_de:
        condicoes.append("criado_em >= ?")
        parametros.append(criado_de.isoformat())
    if criado_ate:
        condicoes.append("criado_em < ?")
        parametros.append((criado_ate + timedelta(days=1)).isoformat())
    return (" WHERE " + " AND ".join(condicoes)) if condicoes else "", parametros


def listar(limite=50, pagina=1, **filtros):
    """Devolve (execuções da página, total que atende aos filtros), da mais recente à mais antiga."""
    onde, parametros = _filtros_sql(**filtros)
    with _conectar() as conexao:
        total = conexao.execute(f"SELECT COUNT(*) FROM execucoes{onde}", parametros).fetchone()[0]
        linhas = conexao.execute(
            f"SELECT * FROM execucoes{onde} ORDER BY criado_em DESC, rowid DESC LIMIT ? OFFSET ?",
            (*parametros, limite, (pagina - 1) * limite),
        ).fetchall()
    return [_para_dict(linha) for linha in linhas], total


def indicadores():
    hoje = datetime.now().date().isoformat()
    with _conectar() as conexao:
        por_status = dict(conexao.execute("SELECT status, COUNT(*) FROM execucoes GROUP BY status").fetchall())
        hoje_por_status = dict(conexao.execute(
            "SELECT status, COUNT(*) FROM execucoes WHERE criado_em >= ? GROUP BY status", (hoje,)
        ).fetchall())
        media = conexao.execute(
            "SELECT AVG((julianday(concluido_em) - julianday(iniciado_em)) * 86400) FROM ("
            " SELECT iniciado_em, concluido_em FROM execucoes WHERE status = ? AND iniciado_em IS NOT NULL"
            " ORDER BY concluido_em DESC LIMIT 50)",
            (STATUS_CONCLUIDO,),
        ).fetchone()[0]
    concluidas = por_status.get(STATUS_CONCLUIDO, 0)
    finalizadas = concluidas + por_status.get(STATUS_FALHOU, 0)
    return {
        "total": sum(por_status.values()),
        "por_status": {s: por_status.get(s, 0) for s in sorted(STATUS_VALIDOS)},
        "hoje": {"total": sum(hoje_por_status.values()),
                 "por_status": {s: hoje_por_status.get(s, 0) for s in sorted(STATUS_VALIDOS)}},
        "taxa_sucesso": round(concluidas / finalizadas, 4) if finalizadas else None,
        "duracao_media_seg": int(media) if media is not None else None,
    }


def atualizar(execucao_id, **campos):
    for chave in ("arquivos", "pendencias"):
        if chave in campos:
            campos[chave] = json.dumps(campos[chave], ensure_ascii=False)
    atribuicoes = ", ".join(f"{nome} = ?" for nome in campos)
    with _trava, _conectar() as conexao:
        conexao.execute(f"UPDATE execucoes SET {atribuicoes} WHERE id = ?", (*campos.values(), execucao_id))


def adicionar_log(execucao_id, seq, mensagem):
    with _trava, _conectar() as conexao:
        conexao.execute(
            "INSERT INTO execucao_log (execucao_id, seq, hora, mensagem) VALUES (?, ?, ?, ?)",
            (execucao_id, seq, datetime.now().strftime("%H:%M:%S"), mensagem),
        )


def log_desde(execucao_id, desde=0):
    with _conectar() as conexao:
        linhas = conexao.execute(
            "SELECT seq, hora, mensagem FROM execucao_log WHERE execucao_id = ? AND seq > ? ORDER BY seq",
            (execucao_id, desde),
        ).fetchall()
    return [dict(linha) for linha in linhas]


def recuperar_na_subida():
    """Marca como falha o que estava executando e devolve os ids ainda na fila, em ordem."""
    with _trava, _conectar() as conexao:
        conexao.execute(
            "UPDATE execucoes SET status = ?, mensagem = ?, concluido_em = ? WHERE status = ?",
            (STATUS_FALHOU, "Interrompida por reinício do serviço.", agora(), STATUS_EXECUTANDO),
        )
        linhas = conexao.execute(
            "SELECT id FROM execucoes WHERE status = ? ORDER BY criado_em, rowid", (STATUS_NA_FILA,)
        ).fetchall()
    return [linha["id"] for linha in linhas]
