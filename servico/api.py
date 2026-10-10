# -*- coding: utf-8 -*-
"""Rotas HTTP do serviço: recebe pedidos de cálculo e expõe a fila e o resultado."""
import hmac
import json
import math
import os
import sqlite3
import urllib.error
import urllib.request
from datetime import date, datetime
from pathlib import Path

from flask import Blueprint, Flask, jsonify, request, send_file
from werkzeug.exceptions import HTTPException

from servico import banco, config, lancamentos
from Calculo.leitura_planilha import historicos_da_planilha_sap
from servico.executor import MODOS
from servico.fila import gerenciador

MODOS_VALIDOS = set(MODOS.values())

api = Blueprint("api", __name__, url_prefix="/api/v1")

LIMITE_TEXTO = 100
LIMITE_CHAVE_IDEMPOTENCIA = 200


class ParametroInvalido(ValueError):
    pass


def _erro(status_http, codigo, mensagem, **extra):
    return jsonify({"status": "erro", "erro": {"codigo": codigo, "mensagem": mensagem, **extra}}), status_http


def _token_da_requisicao():
    token = request.headers.get("X-API-Token", "")
    if not token:
        autorizacao = request.headers.get("Authorization", "")
        if autorizacao.lower().startswith("bearer "):
            token = autorizacao[7:]
    return token.strip()


@api.before_request
def _autenticar():
    if request.endpoint == "api.health":
        return None
    if not hmac.compare_digest(_token_da_requisicao().encode(), config.API_TOKEN.encode()):
        return _erro(401, "nao_autorizado", "Token ausente ou inválido. Envie o cabeçalho X-API-Token.")
    return None


def _dentro_de(caminho, raiz):
    raiz = os.path.normcase(os.path.abspath(raiz))
    caminho = os.path.normcase(os.path.abspath(caminho))
    try:
        return os.path.commonpath([caminho, raiz]) == raiz
    except ValueError:
        return False


def _validar_planilha(dados, campo, extensoes=config.EXTENSOES_PLANILHA, descricao="uma planilha Excel"):
    valor = dados.get(campo)
    if valor in (None, ""):
        return None
    if not isinstance(valor, str):
        raise ParametroInvalido(f"'{campo}' deve ser o caminho do arquivo, em texto.")
    caminho = os.path.normpath(valor.strip())
    if Path(caminho).suffix.lower() not in extensoes:
        raise ParametroInvalido(f"'{campo}' deve ser {descricao} ({', '.join(sorted(extensoes))}).")
    if config.RAIZES_PERMITIDAS and not any(_dentro_de(caminho, raiz) for raiz in config.RAIZES_PERMITIDAS):
        raise ParametroInvalido(f"'{campo}' está fora das pastas permitidas para o serviço.")
    if not os.path.isfile(caminho):
        raise ParametroInvalido(f"'{campo}' não foi encontrada: {caminho}")
    return caminho


def _texto_opcional(dados, campo):
    valor = dados.get(campo)
    if valor is None:
        return None
    if not isinstance(valor, str):
        raise ParametroInvalido(f"'{campo}' deve ser texto.")
    return valor.strip()[:LIMITE_TEXTO] or None


def _com_posicao(registro):
    if registro["status"] in (banco.STATUS_NA_FILA, banco.STATUS_EXECUTANDO):
        registro["posicao_na_fila"] = gerenciador.posicao(registro["id"])
    return registro


def _pjecalc_online():
    try:
        urllib.request.urlopen(config.PJECALC_URL, timeout=2)
        return True
    except urllib.error.HTTPError:
        return True
    except (urllib.error.URLError, OSError):
        return False


@api.get("/health")
def health():
    fila = gerenciador.estado()
    pjecalc_online = _pjecalc_online()
    permissao_ok = config.ARQUIVO_PERMISSAO.exists()
    motivos = []
    if not fila["worker_ativo"]:
        motivos.append("worker parado")
    if not pjecalc_online:
        motivos.append("PJe-Calc não responde em " + config.PJECALC_URL)
    if not permissao_ok:
        motivos.append(f"arquivo de permissão ausente: {config.ARQUIVO_PERMISSAO}")
    return jsonify({
        "status": "degradado" if motivos else "ok",
        "servico": "pjecalc-automacao",
        "motivos": motivos,
        "pjecalc_online": pjecalc_online,
        "fila": {"executando": fila["executando"], "aguardando": len(fila["na_fila"])},
    })


def _mostrar_payload(dados):
    """Mostra no console do serviço o corpo recebido em POST /calculos (não vai para o log da execução)."""
    if dados is None:
        corpo = request.get_data(as_text=True)[:2000] or "(vazio)"
    else:
        corpo = json.dumps(dados, ensure_ascii=False, indent=2)
    print(f"- [requisição] {datetime.now():%d/%m/%Y %H:%M:%S} POST /calculos de {request.remote_addr}:\n{corpo}")


@api.post("/calculos")
def criar_calculo():
    dados = request.get_json(silent=True)
    _mostrar_payload(dados)
    if not isinstance(dados, dict):
        return _erro(400, "parametro_invalido", "O corpo precisa ser um objeto JSON.")

    chave = request.headers.get("Idempotency-Key", "").strip() or None
    if chave and len(chave) > LIMITE_CHAVE_IDEMPOTENCIA:
        return _erro(400, "parametro_invalido", f"Idempotency-Key com mais de {LIMITE_CHAVE_IDEMPOTENCIA} caracteres.")
    if chave:
        existente = banco.obter_por_chave(chave)
        if existente:
            return jsonify({"status": "existente", "execucao": _com_posicao(existente)}), 200

    try:
        planilha_base = _validar_planilha(dados, "planilha_base")
        planilha_verbas = _validar_planilha(dados, "planilha_verbas")
        arquivo_lancamentos = _validar_planilha(dados, "lancamentos", {".json"}, "o .json de lançamentos")
        solicitante = _texto_opcional(dados, "solicitante")
        origem = _texto_opcional(dados, "origem")
        navegador = dados.get("navegador") or banco.NAVEGADOR_OCULTO
        if not isinstance(navegador, str) or navegador not in banco.NAVEGADORES_VALIDOS:
            raise ParametroInvalido(f"'navegador' deve ser um de: {', '.join(sorted(banco.NAVEGADORES_VALIDOS))}.")
    except ParametroInvalido as erro:
        return _erro(400, "parametro_invalido", str(erro))
    if planilha_base:
        try:
            historicos = historicos_da_planilha_sap(planilha_base)
        except ValueError as erro:
            return _erro(400, "planilha_invalida", str(erro))
        if historicos == []:
            return _erro(400, "planilha_em_branco",
                         "A planilha base está em branco: a aba 'PJe Histórico' não tem nenhum histórico salarial nomeado "
                         "(a Ficha Financeira não foi preenchida). Preencha, salve no Excel e envie de novo.")

    interpretacao = None
    if arquivo_lancamentos:
        try:
            interpretacao = lancamentos.interpretar(arquivo_lancamentos)
        except lancamentos.LancamentosIlegiveis as erro:
            return _erro(400, "lancamentos_invalido", str(erro))
        if getattr(interpretacao, "verbas_pedido", None):
            from servico.verbas_pedido import conferir_historicos
            if planilha_verbas:
                interpretacao.verbas_pedido = None
                interpretacao.ignorados["verbas"] = "a planilha de verbas do pedido prevalece"
            elif planilha_base:
                conferir_historicos(interpretacao, historicos)  # None (planilha v3.41) = não dá para conferir aqui
            else:
                conferir_historicos(interpretacao, [nome for nome, _ in interpretacao.historicos])
        if interpretacao.erros:
            return _erro(400, "lancamentos_invalido",
                         f"{len(interpretacao.erros)} campo(s) do .json de lançamentos com valor não aceito.",
                         erros=interpretacao.erros)
    if not planilha_base and not planilha_verbas and not interpretacao:
        return _erro(400, "parametro_invalido", "Informe 'planilha_base', 'planilha_verbas' ou 'lancamentos'.")
    if not planilha_base and interpretacao and interpretacao.faltando_para_criar():
        faltando = interpretacao.faltando_para_criar()
        return _erro(400, "lancamentos_incompleto",
                     f"Sem planilha base, o .json precisa trazer: {', '.join(faltando)}.", faltando=faltando)
    if planilha_base and planilha_verbas and os.path.normcase(planilha_base) == os.path.normcase(planilha_verbas):
        return _erro(400, "parametro_invalido", "'planilha_base' e 'planilha_verbas' apontam para o mesmo arquivo.")

    try:
        registro = banco.criar(planilha_base, planilha_verbas, solicitante, origem, chave, navegador,
                               arquivo_lancamentos, interpretacao.resumo() if interpretacao else None)
    except sqlite3.IntegrityError:
        return jsonify({"status": "existente", "execucao": _com_posicao(banco.obter_por_chave(chave))}), 200

    posicao = gerenciador.enfileirar(registro["id"])
    return jsonify({
        "status": "aceito",
        "mensagem": "Cálculo na fila.",
        "execucao": registro,
        "posicao_na_fila": posicao,
        "acompanhar_em": f"{api.url_prefix}/calculos/{registro['id']}",
    }), 202


def _inteiro(nome, padrao, minimo, maximo):
    try:
        return min(max(int(request.args.get(nome, padrao)), minimo), maximo)
    except ValueError:
        raise ParametroInvalido(f"'{nome}' deve ser um número inteiro.")


def _data(nome):
    valor = request.args.get(nome) or None
    if not valor:
        return None
    try:
        return date.fromisoformat(valor)
    except ValueError:
        raise ParametroInvalido(f"'{nome}' deve estar no formato AAAA-MM-DD.")


@api.get("/calculos")
def listar_calculos():
    try:
        situacao = request.args.get("situacao") or None
        if situacao and situacao not in banco.STATUS_VALIDOS:
            raise ParametroInvalido(f"'situacao' deve ser uma de: {', '.join(sorted(banco.STATUS_VALIDOS))}.")
        modo = request.args.get("modo") or None
        if modo and modo not in MODOS_VALIDOS:
            raise ParametroInvalido(f"'modo' deve ser um de: {', '.join(sorted(MODOS_VALIDOS))}.")
        limite = _inteiro("limite", 50, 1, 200)
        pagina = _inteiro("pagina", 1, 1, 100000)
        filtros = {
            "status": situacao, "modo": modo,
            "busca": (request.args.get("busca") or "").strip()[:LIMITE_TEXTO] or None,
            "criado_de": _data("de"), "criado_ate": _data("ate"),
        }
    except ParametroInvalido as erro:
        return _erro(400, "parametro_invalido", str(erro))
    registros, total_geral = banco.listar(limite=limite, pagina=pagina, **filtros)
    execucoes = [_com_posicao(r) for r in registros]
    return jsonify({
        "total": len(execucoes),
        "total_geral": total_geral,
        "pagina": pagina,
        "paginas": max(math.ceil(total_geral / limite), 1),
        "limite": limite,
        "execucoes": execucoes,
    })


@api.get("/indicadores")
def ver_indicadores():
    return jsonify({"indicadores": banco.indicadores(), "fila": gerenciador.estado()})


@api.get("/calculos/<execucao_id>")
def obter_calculo(execucao_id):
    registro = banco.obter(execucao_id)
    if not registro:
        return _erro(404, "nao_encontrado", "Execução não encontrada.")
    try:
        desde = max(int(request.args.get("desde", 0)), 0)
    except ValueError:
        return _erro(400, "parametro_invalido", "'desde' deve ser um número inteiro.")
    log = banco.log_desde(execucao_id, desde)
    registro["log"] = log
    registro["log_ultimo_seq"] = log[-1]["seq"] if log else desde
    return jsonify({"execucao": _com_posicao(registro)})


@api.get("/calculos/<execucao_id>/arquivos/<int:indice>")
def baixar_arquivo(execucao_id, indice):
    registro = banco.obter(execucao_id)
    if not registro:
        return _erro(404, "nao_encontrado", "Execução não encontrada.")
    if indice >= len(registro["arquivos"]):
        return _erro(404, "nao_encontrado", f"A execução tem {len(registro['arquivos'])} arquivo(s); índice {indice} não existe.")
    caminho = Path(registro["arquivos"][indice])
    if not caminho.is_file():
        return _erro(410, "arquivo_indisponivel", f"O arquivo não está mais no local registrado: {caminho}")
    return send_file(caminho, as_attachment=True, download_name=caminho.name)


@api.get("/calculos/<execucao_id>/captura")
def ver_captura(execucao_id):
    registro = banco.obter(execucao_id)
    if not registro:
        return _erro(404, "nao_encontrado", "Execução não encontrada.")
    if not registro["captura"]:
        return _erro(404, "sem_captura", "Esta execução não tem captura de tela.")
    caminho = Path(registro["captura"]).resolve()
    if not caminho.is_relative_to(config.CAPTURAS_DIR.resolve()) or not caminho.is_file():
        return _erro(410, "arquivo_indisponivel", "A captura não está mais disponível.")
    return send_file(caminho, mimetype="image/png", as_attachment=request.args.get("baixar") == "1",
                     download_name=caminho.name)


@api.post("/calculos/<execucao_id>/cancelar")
def cancelar_calculo(execucao_id):
    registro = banco.obter(execucao_id)
    if not registro:
        return _erro(404, "nao_encontrado", "Execução não encontrada.")
    if gerenciador.cancelar(execucao_id):
        return jsonify({"mensagem": "Execução cancelada.", "execucao": banco.obter(execucao_id)})
    if registro["status"] == banco.STATUS_EXECUTANDO:
        return _erro(409, "em_execucao", "A execução já começou e não pode ser interrompida com segurança.")
    return _erro(409, "ja_finalizada", f"A execução já terminou com status '{registro['status']}'.")


@api.get("/fila")
def ver_fila():
    return jsonify({"fila": gerenciador.estado()})


def criar_app():
    app = Flask(__name__, static_folder="painel", static_url_path="/painel")
    app.config["MAX_CONTENT_LENGTH"] = 64 * 1024
    app.json.ensure_ascii = False
    app.register_blueprint(api)

    @app.get("/")
    def painel():
        return app.send_static_file("index.html")

    @app.after_request
    def _utf8_explicito(resposta):
        if resposta.mimetype == "application/json":
            resposta.headers["Content-Type"] = "application/json; charset=utf-8"
        return resposta

    @app.errorhandler(HTTPException)
    def _erro_http(erro):
        codigos = {404: "rota_inexistente", 405: "metodo_nao_permitido", 413: "corpo_grande_demais"}
        return _erro(erro.code, codigos.get(erro.code, f"http_{erro.code}"), erro.description)

    @app.errorhandler(Exception)
    def _erro_interno(erro):
        app.logger.exception(erro)
        return _erro(500, "erro_interno", "Erro interno do serviço.")

    return app
