# -*- coding: utf-8 -*-
"""Lê o .json de lançamentos do SAP (contrato lancamentos-pjecalc/1) e o traduz para chaves da PJE-BD da v3.41.

As telas continuam lendo a PJE-BD; este módulo só produz as linhas que faltam, no formato que elas já entendem.
Valor fora das listas do PJe-Calc recusa o pedido na porta; campo que a automação não conhece é ignorado e relatado.
"""
import csv
import json
import os
import re
import unicodedata
from datetime import datetime, timedelta
from pathlib import Path

from servico import config
from Calculo.leitura_planilha import data_da_planilha, numero_da_planilha, documento_da_planilha, opcao_de_municipio, UFS

CONTRATO = "lancamentos-pjecalc/1"
CATALOGO = json.loads((Path(__file__).with_name("catalogo_pjecalc.json")).read_text(encoding="utf-8"))
ORIGEM_EXCEL = datetime(1899, 12, 30)
PADRAO_CNJ = re.compile(r"^\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}$")
META = {"contrato", "geradoEm", "procedencia", "processo.numero"}
ORDEM = [
    "id_processo", "numero_processo", "valor_da_causa", "nome_parte1", "doc_parte1", "advogado_parte1", "nome_parte2",
    "doc_parte2", "advogado_parte2", "uf", "municipio", "data_admissao", "data_rescisao", "data_ajuizamento",
    "inicio_calculo", "termino_calculo", "aplicar_prescricao_verbas", "aplicar_prescricao_FGTS", "regime_trabalho",
    "maior_remuneracao", "ultima_remuneracao", "prazo_de_aviso_previo", "quantidade_dias_aviso_previo",
    "projetar_aviso_previo_indenizado", "limitar_avos_ao_periodo_do_calculo", "zerar_valor_negativo_padrao",
    "considerar_feriados_estaduais", "considerar_feriados_municipais", "carga_horaria", "sabado_como_dia_util",
    "comentarios_parametros", "ponto_facultutativo_sextafeirasanta", "ponto_facultutativo_corpuschristi",
    "ponto_facultutativo_carnaval", "destino_fgts", "compor_principal", "multa_fgts", "cont_social_aliquota_empregador",
    "processo_de_agroindustria", "empresa_enquadrada_simples", "empresa_com_desoneracao", "entidade_filantropica",
]
MINIMO_SEM_PLANILHA = {"nome_parte1": "reclamante", "nome_parte2": "reclamado", "uf": "UF", "municipio": "município",
                       "data_admissao": "admissão", "data_ajuizamento": "ajuizamento"}

TIPOS_HONORARIO = {
    "ADVOCATICIOS": "Honorários Advocatícios", "ASSISTENCIAIS": "Honorários Assistenciais",
    "CONTRATUAIS": "Honorários Contratuais", "PERICIAIS_CONTADOR": "Honorários Periciais - Contador",
    "PERICIAIS_DOCUMENTOSCOPIO": "Honorários Periciais - Documentoscópio",
    "PERICIAIS_ENGENHEIRO": "Honorários Periciais - Engenheiro", "PERICIAIS_INTERPRETE": "Honorários Periciais - Intérprete",
    "PERICIAIS_MEDICO": "Honorários Periciais - Médico", "PERICIAIS_OUTROS": "Honorários Periciais - Outros",
    "SUCUMBENCIAIS": "Honorários de Sucumbência", "LEILOEIRO": "Leiloeiro",
}
CREDOR_DEVEDOR_MULTA = {
    "RECLAMANTE_RECLAMADO": "Reclamante e Reclamado", "RECLAMADO_RECLAMANTE": "Reclamado e Reclamante",
    "TERCEIRO_RECLAMANTE": "Terceiro e Reclamante", "TERCEIRO_RECLAMADO": "Terceiro e Reclamado",
    "RECLAMANTE_E_RECLAMADO": "Reclamante e Reclamado", "RECLAMADO_E_RECLAMANTE": "Reclamado e Reclamante",
    "TERCEIRO_E_RECLAMANTE": "Terceiro e Reclamante", "TERCEIRO_E_RECLAMADO": "Terceiro e Reclamado",
}
CUSTAS_RECLAMADO = {"NAO_SE_APLICA": "Não se Aplica", "CALCULADA_2_POR_CENTO": "Calculada 2%", "INFORMADA": "Informada"}
DESTINO_FGTS = {"RECOLHER": "Recolher", "PAGAR": "Pagar"}
DEVEDOR = {"RECLAMADO": "RECLAMADA", "RECLAMANTE": "RECLAMANTE"}
COBRANCA = {"COBRAR": "COBRAR", "DESCONTAR": "DESCONTAR", "DESCONTAR_CREDITO": "DESCONTAR"}


class LancamentosIlegiveis(ValueError):
    """O arquivo não pôde ser lido como o contrato esperado; o pedido é recusado inteiro."""


def _sem_acento(texto):
    return unicodedata.normalize("NFKD", str(texto)).encode("ASCII", "ignore").decode("ASCII").lower()


def _serial(valor):
    data = data_da_planilha(valor)
    return (data - ORIGEM_EXCEL).days if data else None


def _texto(valor):
    return "True" if valor else "False"


def _sim_nao(valor):
    return "Sim" if valor else "Não"


class Interpretacao:

    def __init__(self, dados):
        self.dados = dados
        self.valores = {}
        self.familias = []
        self.usados = set()
        self.ignorados = {}
        self.avisos = []
        self.erros = []
        self.faltas = []
        self.ferias = []
        self.historicos = []
        self.arquivos = {}

    # --- registro ---
    def usar(self, caminho, chave, valor):
        if valor is None:
            return
        self.valores[chave] = valor
        self.usados.add(caminho)

    def ignorar(self, caminho, motivo):
        self.ignorados.setdefault(caminho, motivo)

    def erro(self, caminho, valor, mensagem, aceitos=None):
        item = {"campo": caminho, "valor": valor, "mensagem": mensagem}
        if aceitos:
            item["aceitos"] = list(aceitos)
        self.erros.append(item)

    def enumeracao(self, caminho, valor, tabela):
        """Código do .json → texto da tela; aceita também o próprio texto da tela."""
        if valor in tabela:
            return tabela[valor]
        if valor in tabela.values():
            return valor
        self.erro(caminho, valor, "valor não reconhecido", sorted(tabela))
        return None

    def data(self, caminho, valor):
        serial = _serial(valor)
        if serial is None:
            self.erro(caminho, valor, "data inválida: use AAAA-MM-DD")
        return serial

    # --- resultado ---
    def pares_avulsos(self):
        """(chave, valor) na ordem da v3.41: há chaves de disparo que precisam vir depois das outras."""
        ordenados = [(c, self.valores[c]) for c in ORDEM if c in self.valores]
        return ordenados + [(c, v) for c, v in self.valores.items() if c not in ORDEM]

    def pares(self):
        return self.pares_avulsos() + [par for _, familia in self.familias for par in familia]

    def faltando_para_criar(self):
        return [rotulo for chave, rotulo in MINIMO_SEM_PLANILHA.items() if chave not in self.valores]

    def resumo(self):
        return {
            "contrato": self.dados.get("contrato"),
            "usados": sorted(self.usados),
            "ignorados": dict(sorted(self.ignorados.items())),
            "avisos": self.avisos,
        }


def _folhas(dados, prefixo=""):
    """Caminhos de todos os campos do .json, com listas como 'bloco[]'."""
    if isinstance(dados, dict):
        for chave, valor in dados.items():
            yield from _folhas(valor, f"{prefixo}.{chave}" if prefixo else chave)
    elif isinstance(dados, list) and dados and all(isinstance(i, dict) for i in dados):
        for item in dados:
            yield from _folhas(item, f"{prefixo}[]")
    else:
        yield prefixo


# ---------------------------------------------------------------- blocos do documento anterior (dadosDoCalculo, …)

def _dados_do_calculo(r):
    bloco = r.dados.get("dadosDoCalculo") or {}
    processo = r.dados.get("processo") or {}
    if processo.get("id") not in (None, ""):
        r.usar("processo.id", "id_processo", int(processo["id"]) if str(processo["id"]).isdigit() else processo["id"])
    numero = bloco.get("numeroProcesso") or processo.get("numero")
    if numero:
        if PADRAO_CNJ.match(str(numero)):
            r.usar("dadosDoCalculo.numeroProcesso", "numero_processo", str(numero))
        else:
            r.erro("dadosDoCalculo.numeroProcesso", numero, "número CNJ fora do formato 0000000-00.0000.0.00.0000")
    for i, parte in enumerate(bloco.get("partes") or []):
        polo = str(parte.get("polo", "")).upper()
        sufixo = {"ATIVO": "1", "PASSIVO": "2"}.get(polo)
        if not sufixo:
            r.erro(f"dadosDoCalculo.partes[{i}].polo", parte.get("polo"), "polo não reconhecido", ["ATIVO", "PASSIVO"])
            continue
        if parte.get("nome"):
            r.usar("dadosDoCalculo.partes[].nome", f"nome_parte{sufixo}", str(parte["nome"])[:150])
        if parte.get("documento"):
            r.usar("dadosDoCalculo.partes[].documento", f"doc_parte{sufixo}", documento_da_planilha(parte["documento"]))
        else:
            r.usados.add("dadosDoCalculo.partes[].documento")
        r.usados.add("dadosDoCalculo.partes[].polo")
    for campo, chave in (("dataAdmissao", "data_admissao"), ("dataDemissao", "data_rescisao"),
                         ("dataAjuizamento", "data_ajuizamento"), ("dataInicioCalculo", "inicio_calculo"),
                         ("dataTerminoCalculo", "termino_calculo")):
        if bloco.get(campo):
            r.usar(f"dadosDoCalculo.{campo}", chave, r.data(f"dadosDoCalculo.{campo}", bloco[campo]))
    if bloco.get("atividadeEconomica"):
        r.usar("dadosDoCalculo.atividadeEconomica", "cont_social_aliquota_empregador", str(bloco["atividadeEconomica"]).strip())
    if bloco.get("vara"):
        r.usados.add("dadosDoCalculo.vara")
        _municipio_da_vara(r, str(bloco["vara"]))
    for campo, motivo in (("identificacao", "só identifica o processo no SAP"), ("classe", "sem campo no PJe-Calc"),
                          ("tipoRescisao", "sem campo na tela Dados do Cálculo")):
        if campo in bloco:
            r.ignorar(f"dadosDoCalculo.{campo}", motivo)


def _municipio_da_vara(r, vara):
    """'19ª VARA DO TRABALHO DO RECIFE-PE' → RECIFE / PE, conferido na lista do PJe-Calc."""
    telas_dados = (r.dados.get("telas") or {}).get("dados-do-calculo") or {}
    if "municipio" in r.valores or telas_dados.get("municipio"):
        return
    achado = re.search(r"^(.*?)\s*[-/]\s*([A-Za-z]{2})\s*$", vara.strip())
    if not achado or achado.group(2).upper() not in UFS:
        r.avisos.append(f"Município não identificado na vara '{vara}'.")
        return
    uf = achado.group(2).upper()
    palavras = achado.group(1).split()
    for inicio in range(len(palavras)):
        candidato = " ".join(palavras[inicio:])
        opcao = opcao_de_municipio(candidato, CATALOGO["municipios"].get(uf, []))
        if opcao and _sem_acento(opcao) == _sem_acento(" ".join(candidato.upper().split())):
            r.usar("dadosDoCalculo.vara", "uf", uf)
            r.usar("dadosDoCalculo.vara", "municipio", opcao)
            r.avisos.append(f"Município e UF tirados da vara: {opcao}/{uf}. Mande 'municipio' e 'uf' para não depender disso.")
            return
    r.avisos.append(f"Município não identificado na vara '{vara}'.")


def _fgts(r):
    bloco = r.dados.get("fgts") or {}
    if "destino" in bloco:
        r.usar("fgts.destino", "destino_fgts", r.enumeracao("fgts.destino", bloco["destino"], DESTINO_FGTS))
    if "multaDoFgts" in bloco:
        r.usar("fgts.multaDoFgts", "multa_fgts", _sim_nao(bool(bloco["multaDoFgts"])))


def _codigo(texto):
    """'Principal (-) Contribuição Social' → 'PRINCIPAL_MENOS_CONTRIBUICAO_SOCIAL' (a forma dos códigos do XML)."""
    texto = _sem_acento(texto).upper().replace("(-)", " MENOS ")
    return re.sub(r"[^A-Z0-9]+", "_", texto).strip("_")


def _opcao_da_tela(r, caminho, valor, opcoes):
    """Aceita o texto da lista do PJe-Calc ou o código equivalente (com ou sem o '_MENOS_')."""
    if valor in opcoes:
        return valor
    alvo = _codigo(valor or "")
    for opcao in opcoes:
        codigo = _codigo(opcao)
        if alvo and alvo in (codigo, codigo.replace("_MENOS", "")):
            return opcao
    r.erro(caminho, valor, "valor não reconhecido", opcoes)
    return None


def _fracao(r, caminho, valor):
    numero = numero_da_planilha(valor)
    if numero is None or not 0 < numero <= 1:
        r.erro(caminho, valor, "alíquota em FRAÇÃO, entre 0 e 1 (0.05 = 5%)")
        return None
    return float(numero)


def _custas(r):
    bloco = r.dados.get("custas") or {}
    if not bloco:
        return
    tipo = None
    if "tipoDeCustasDeConhecimentoDoReclamado" in bloco:
        tipo = r.enumeracao("custas.tipoDeCustasDeConhecimentoDoReclamado", bloco["tipoDeCustasDeConhecimentoDoReclamado"], CUSTAS_RECLAMADO)
    vencimento_informado, valor_informado = "-", "-"
    if tipo == "Informada":
        vencimento_informado = r.data("custas.dataVencimentoConhecimentoDoReclamado", bloco.get("dataVencimentoConhecimentoDoReclamado"))
        valor_informado = numero_da_planilha(bloco.get("valorConhecimentoDoReclamado"))
        if valor_informado is None:
            r.erro("custas.valorConhecimentoDoReclamado", bloco.get("valorConhecimentoDoReclamado"), "valor obrigatório em custas INFORMADA")
        if None in (vencimento_informado, valor_informado):
            tipo = None
        else:
            r.usados.update({"custas.dataVencimentoConhecimentoDoReclamado", "custas.valorConhecimentoDoReclamado"})
    pagas = bloco.get("custasPagasDoReclamado") or []
    if tipo is None and not pagas:
        return
    familia = []
    if tipo:
        r.usados.add("custas.tipoDeCustasDeConhecimentoDoReclamado")
        familia += [("custas_reclamado_conhecimento", tipo), ("custas_recda_conhecimento_info_vcto", vencimento_informado),
                    ("custas_recda_conhecimento_info_valor", valor_informado)]
    familia.append(("qtd_custas_recolhidas", len(pagas)))
    for n, paga in enumerate(pagas, start=1):
        valor = numero_da_planilha(paga.get("valor"))
        vencimento = _serial(paga.get("dataVencimento") or paga.get("vencimento"))
        r.usados.add("custas.custasPagasDoReclamado[].valor")
        if vencimento is None:
            r.avisos.append(f"Custa recolhida nº {n} (R$ {valor}) sem data de vencimento: não será lançada. Mande 'dataVencimento'.")
        else:
            r.usados.add("custas.custasPagasDoReclamado[].dataVencimento")
        familia += [(f"custas_recolhidas_rcdo{n}_vencimento", vencimento if vencimento is not None else "-"),
                    (f"custas_recolhidas_rcdo{n}_valor", valor if valor is not None and vencimento is not None else "-")]
    r.familias.append(("custas", familia))


# Honorário CALCULADO vai pela família 'contratuais' da tela: ela pula tipo com '-' (os periciais) e aplica .title()
# ao tipo (o que estraga 'Honorários de Sucumbência'); por isso só estes quatro.
TIPOS_HONORARIO_CALCULADO = {"Honorários Advocatícios", "Honorários Assistenciais", "Honorários Contratuais", "Leiloeiro"}


def _honorarios(r):
    itens = r.dados.get("honorarios")
    if itens is None:
        return
    informados, calculados = [], []
    for n, item in enumerate(itens):
        base = f"honorarios[{n}]"
        tipo_valor = str(item.get("tipoValor", "INFORMADO")).upper()
        if tipo_valor not in ("INFORMADO", "CALCULADO"):
            r.erro(f"{base}.tipoValor", item.get("tipoValor"), "valor não reconhecido", ["INFORMADO", "CALCULADO"])
            continue
        descricao = str(item.get("descricao") or "").strip()
        if len(descricao) > 50 and tipo_valor == "INFORMADO":
            r.avisos.append(f"{base}.descricao: tem {len(descricao)} caracteres; no honorário INFORMADO o PJe-Calc guarda os 50 "
                            f"primeiros ({descricao[:50].upper()!r})")
        if not descricao or "-" in descricao:
            r.erro(f"{base}.descricao", item.get("descricao"), "descrição obrigatória e sem '-' (a automação usa '-' para 'bloco vazio')")
            continue
        tipo = r.enumeracao(f"{base}.tipoHonorario", item.get("tipoHonorario"), TIPOS_HONORARIO)
        devedor = r.enumeracao(f"{base}.tipoDeDevedor", item.get("tipoDeDevedor"), DEVEDOR)
        cobranca = r.enumeracao(f"{base}.tipoCobrancaReclamante", item.get("tipoCobrancaReclamante", "COBRAR"), COBRANCA)
        credor = str(item.get("nomeCredor") or "")
        if tipo_valor == "INFORMADO":
            vencimento = r.data(f"{base}.dataVencimento", item.get("dataVencimento"))
            valor = numero_da_planilha(item.get("valor"))
            if valor is None:
                r.erro(f"{base}.valor", item.get("valor"), "valor obrigatório em honorário INFORMADO")
            if None not in (tipo, devedor, cobranca, vencimento, valor):
                informados.append((tipo, descricao, devedor, cobranca, vencimento, valor, credor))
                r.usados.update(f"honorarios[].{c}" for c in item)
            continue
        if tipo and tipo not in TIPOS_HONORARIO_CALCULADO:
            r.erro(f"{base}.tipoHonorario", item.get("tipoHonorario"), "honorário CALCULADO deste tipo ainda não suportado",
                   sorted(k for k, v in TIPOS_HONORARIO.items() if v in TIPOS_HONORARIO_CALCULADO))
            continue
        if item.get("outroIndiceDeCorrecao") or "OUTRO" in _codigo(item.get("tipoDeIndiceDeCorrecao") or ""):
            r.erro(f"{base}.outroIndiceDeCorrecao", item.get("outroIndiceDeCorrecao") or item.get("tipoDeIndiceDeCorrecao"),
                   "índice de correção próprio em honorário CALCULADO ainda não suportado (sai o índice trabalhista)")
            continue
        aliquota = _fracao(r, f"{base}.aliquota", item.get("aliquota"))
        base_apuracao = _opcao_da_tela(r, f"{base}.baseParaApuracao", item.get("baseParaApuracao"),
                                       CATALOGO["telas"]["honorarios"]["listas"]["baseParaApuracao"])
        if None not in (tipo, devedor, cobranca, aliquota, base_apuracao):
            calculados.append((tipo, descricao, devedor, "DEDUZIR" if cobranca == "DESCONTAR" else "COBRAR", aliquota, base_apuracao, credor))
            r.usados.update(f"honorarios[].{c}" for c in item)

    familia = [("qtd_honorarios_periciais", len(informados))]
    for n, (tipo, descricao, devedor, cobranca, vencimento, valor, credor) in enumerate(informados, start=1):
        familia += [(f"honorarios_periciais_tipo_pericia_pje_calc_{n}", tipo), (f"honorarios_periciais_descricao_{n}", descricao),
                    (f"honorarios_periciais_devedor_{n}", devedor), (f"honorarios_periciais_pgto_rcte_{n}", cobranca),
                    (f"honorarios_periciais_data_{n}", vencimento), (f"honorarios_periciais_valor_{n}", valor),
                    (f"honorarios_periciais_nome_credor_{n}", credor), (f"honorarios_periciais_cm_{n}", "<branco>")]
    familia.append(("qtd_honorarios_contratuais", len(calculados)))
    for n, (tipo, descricao, devedor, participacao, aliquota, base_apuracao, credor) in enumerate(calculados, start=1):
        familia += [(f"honorarios_contratuais_tipob_{n}", tipo), (f"honorarios_contratuais_descricao_{n}", descricao),
                    (f"honorarios_contratuais_devedor_{n}", devedor), (f"honorarios_contratuais_partic_{n}", participacao),
                    (f"honorarios_contratuais_tipo_{n}", "CALCULADO"), (f"honorarios_contratuais_alíquota_{n}", aliquota),
                    (f"honorarios_contratuais_base_{n}", base_apuracao), (f"honorarios_contratuais_nome_{n}", credor)]
    r.familias.append(("honorarios", familia))


def _multas(r):
    itens = r.dados.get("multas")
    if itens is None:
        return
    if len(itens) > 9:
        r.erro("multas", len(itens), "no máximo 9 multas por pedido (limitação da leitura por nome de chave)")
        return
    familia = [("multas_indenizacoes_qtd", len(itens))]
    for n, item in enumerate(itens, start=1):
        base = f"multas[{n - 1}]"
        tipo = str(item.get("tipoValorDaMulta", "INFORMADO")).upper()
        if tipo not in ("INFORMADO", "CALCULADO"):
            r.erro(f"{base}.tipoValorDaMulta", item.get("tipoValorDaMulta"), "valor não reconhecido", ["INFORMADO", "CALCULADO"])
            continue
        credor = r.enumeracao(f"{base}.tipoCredorDevedor", item.get("tipoCredorDevedor"), CREDOR_DEVEDOR_MULTA)
        terceiro = "-"
        if credor and credor.startswith("Terceiro"):
            terceiro = str(item.get("nomeTerceiro") or "").strip() or None
            if terceiro is None:
                r.erro(f"{base}.nomeTerceiro", item.get("nomeTerceiro"), "nome do terceiro obrigatório quando o credor/devedor é um terceiro")
        cobranca = r.enumeracao(f"{base}.tipoCobrancaReclamante", item.get("tipoCobrancaReclamante", "COBRAR"), COBRANCA)
        descricao = str(item.get("descricao") or "").strip()
        if not descricao:
            r.erro(f"{base}.descricao", item.get("descricao"), "descrição obrigatória")
        vencimento, valor, base_multa, aliquota, juros_desde = "-", "-", "-", "-", "-"
        juros = bool(item.get("aplicarJurosSobreMulta"))
        if tipo == "INFORMADO":
            vencimento = r.data(f"{base}.dataVencimentoMulta", item.get("dataVencimentoMulta"))
            valor = numero_da_planilha(item.get("valorMulta"))
            if valor is None:
                r.erro(f"{base}.valorMulta", item.get("valorMulta"), "valor obrigatório em multa INFORMADA")
            if juros:
                juros_desde = _serial(item.get("dataJurosAPartirDe"))
                if juros_desde is None:
                    r.erro(f"{base}.aplicarJurosSobreMulta", True, "com juros, mande 'dataJurosAPartirDe' (AAAA-MM-DD)")
        else:
            if juros:
                r.erro(f"{base}.aplicarJurosSobreMulta", True, "juros em multa CALCULADA ainda não suportados")
                juros_desde = None
            aliquota = _fracao(r, f"{base}.aliquotaMulta", item.get("aliquotaMulta"))
            base_multa = _opcao_da_tela(r, f"{base}.tipoBaseMulta", item.get("tipoBaseMulta"),
                                        CATALOGO["telas"]["multas-e-indenizacoes"]["listas"]["tipoBaseMulta"])
        if None in (credor, terceiro, cobranca, vencimento, valor, juros_desde, aliquota, base_multa) or not descricao:
            continue
        familia += [(f"multas_indenizacoes_descricao_{n}", descricao), (f"multas_indenizacoes_credor_{n}", credor),
                    (f"multas_indenizacoes_form_pagto_{n}", cobranca), (f"multas_indenizacoes_terceiro_{n}", terceiro),
                    (f"multas_indenizacoes_tipo_{n}", tipo), (f"multas_indenizacoes_vcto_{n}", vencimento),
                    (f"multas_indenizacoes_valor_{n}", valor), (f"multas_indenizacoes_base_pje-calc_{n}", base_multa),
                    (f"multas_indenizacoes_aliquota_{n}", aliquota), (f"multas_indenizacoes_aplicar_juros_{n}", "SIM" if juros else "NÃO"),
                    (f"multas_indenizacoes_a_partir_de_{n}", juros_desde)]
        r.usados.update(f"multas[].{c}" for c in item)
    r.familias.append(("multas", familia))


# ---------------------------------------------------------------- bloco novo: advogados

LIMITE_OAB = 9  # o campo OAB da tela do PJe-Calc aceita 9 caracteres
OAB = re.compile(r"^\d{1,6}[A-Z]?/[A-Z]{2}$")
TIPOS_DOCUMENTO_ADVOGADO = {"CPF": 11, "CNPJ": 14, "CEI": 12}


def cpf_valido(digitos):
    if len(digitos) != 11 or digitos == digitos[0] * 11:
        return False
    for tamanho in (9, 10):
        soma = sum(int(d) * (tamanho + 1 - i) for i, d in enumerate(digitos[:tamanho]))
        if (soma * 10 % 11) % 10 != int(digitos[tamanho]):
            return False
    return True


def cnpj_valido(digitos):
    if len(digitos) != 14 or digitos == digitos[0] * 14:
        return False
    for tamanho, pesos in ((12, [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]), (13, [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])):
        resto = sum(int(d) * p for d, p in zip(digitos[:tamanho], pesos)) % 11
        if (0 if resto < 2 else 11 - resto) != int(digitos[tamanho]):
            return False
    return True


def _advogados(r):
    """Bloco `advogados`: { reclamante: [...], reclamado: [...] } → família por parte, lançada em Dados do Cálculo."""
    from servico.verbas_pedido import normalizar_descricao

    bloco = r.dados.get("advogados")
    if bloco is None:
        return
    if not isinstance(bloco, dict):
        r.erro("advogados", bloco, "deve ser um objeto { reclamante: [...], reclamado: [...] }")
        return
    for parte in bloco:
        if parte not in ("reclamante", "reclamado"):
            r.ignorar(f"advogados.{parte}", "parte não reconhecida (use reclamante ou reclamado)")
    for parte in ("reclamante", "reclamado"):
        itens = bloco.get(parte)
        if itens is None:
            continue
        base = f"advogados.{parte}"
        if not isinstance(itens, list):
            r.erro(base, itens, "deve ser uma lista")
            continue
        if len(itens) > 10:
            r.erro(base, len(itens), "no máximo 10 advogados por parte")
            continue
        familia, documentos, erros_antes = [(f"advogados_{parte}_qtd", len(itens))], set(), len(r.erros)
        for n, item in enumerate(itens, start=1):
            caminho = f"{base}[{n - 1}]"
            if not isinstance(item, dict):
                r.erro(caminho, item, "deve ser um objeto { nome, oab, tipoDocumento, documento }")
                continue
            nome = normalizar_descricao(item.get("nome") or "")
            if not nome:
                r.erro(f"{caminho}.nome", item.get("nome"), "obrigatório")
            elif len(nome) > 150:
                r.erro(f"{caminho}.nome", item.get("nome"), "até 150 caracteres (limite da tela)")
            oab = str(item.get("oab") or "").strip().upper().replace(" ", "")
            if oab and (len(oab) > LIMITE_OAB or not OAB.match(oab)):
                r.erro(f"{caminho}.oab", item.get("oab"), f"use NUMERO/UF, até {LIMITE_OAB} caracteres (ex.: 12345/PE, 12345A/PE)")
            elif oab and oab.split("/")[1] not in UFS:
                r.erro(f"{caminho}.oab", item.get("oab"), "UF da OAB não reconhecida")
            tipo = item.get("tipoDocumento")
            documento = documento_da_planilha(item.get("documento")) if item.get("documento") not in (None, "") else None
            if (tipo in (None, "")) != (documento is None):
                r.erro(f"{caminho}.documento", item.get("documento"), "tipoDocumento e documento vêm juntos ou não vêm")
            elif tipo is not None:
                if tipo not in TIPOS_DOCUMENTO_ADVOGADO:
                    r.erro(f"{caminho}.tipoDocumento", tipo, "valor não reconhecido", sorted(TIPOS_DOCUMENTO_ADVOGADO))
                elif (len(documento) != TIPOS_DOCUMENTO_ADVOGADO[tipo]
                      or (tipo == "CPF" and not cpf_valido(documento)) or (tipo == "CNPJ" and not cnpj_valido(documento))):
                    r.erro(f"{caminho}.documento", item.get("documento"), f"{tipo} inválido (tamanho ou dígito verificador)")
                elif documento in documentos:
                    # o PJe-Calc não inclui o segundo advogado com o mesmo documento na mesma parte, e não avisa
                    r.erro(f"{caminho}.documento", item.get("documento"), "documento repetido nesta parte: o PJe-Calc não inclui o segundo")
                documentos.add(documento)
            familia += [(f"advogado_{parte}_{n}_nome", nome), (f"advogado_{parte}_{n}_oab", oab or "-"),
                        (f"advogado_{parte}_{n}_tipodoc", tipo or "-"), (f"advogado_{parte}_{n}_doc", documento or "-")]
        if len(r.erros) == erros_antes and itens:
            r.familias.append((f"advogados_{parte}", familia))
            r.usados.add(base)


# ---------------------------------------------------------------- bloco novo: arquivos (CSV)

CABECALHO_FALTAS = ["INICIO", "FIM", "JUSTIFICADA", "REINICIAR_PER_AQ", "JUSTIFICATIVA"]
CABECALHO_FERIAS = ["RELATIVAS", "PRAZO", "SITUACAO", "DOBRA", "ABONO", "QTD_DIAS_ABONO",
                    "G1INI", "G1FIM", "G1DOBRA", "G2INI", "G2FIM", "G2DOBRA", "G3INI", "G3FIM", "G3DOBRA"]
ARQUIVOS_CONHECIDOS = ("faltas", "ferias", "historico-salarial", "cartao-de-ponto")
DATA_BR = re.compile(r"^\d{2}/\d{2}/\d{4}$")


def _caminho_do_arquivo(r, chave, valor, pasta_do_json):
    caminho = os.path.normpath(str(valor).strip())
    if not os.path.isabs(caminho):
        caminho = os.path.normpath(os.path.join(pasta_do_json, caminho))
    base = f"arquivos.{chave}"
    if Path(caminho).suffix.lower() != ".csv":
        r.erro(base, valor, "deve ser o caminho de um arquivo .csv")
        return None
    if config.RAIZES_PERMITIDAS:
        absoluto = os.path.normcase(os.path.abspath(caminho))
        if not any(absoluto.startswith(os.path.normcase(os.path.abspath(raiz)) + os.sep) for raiz in config.RAIZES_PERMITIDAS):
            r.erro(base, valor, "fora das pastas permitidas para o serviço")
            return None
    if not os.path.isfile(caminho):
        r.erro(base, valor, "arquivo não encontrado")
        return None
    return caminho


def _linhas_do_csv(caminho):
    bruto = Path(caminho).read_bytes()
    try:
        texto = bruto.decode("utf-8-sig")
    except UnicodeDecodeError:
        texto = bruto.decode("cp1252")
    return list(csv.reader(texto.splitlines(), delimiter=";"))


def _ler_csv_da_tela(r, chave, caminho, cabecalho, obrigatoria, colunas_data):
    """Faltas e Férias: o .csv já vem no layout das abas PJeFaltas/PJeFérias; devolve as linhas na ordem do cabeçalho."""
    base = f"arquivos.{chave}"
    try:
        linhas = _linhas_do_csv(caminho)
    except OSError as erro:
        r.erro(base, caminho, f"não foi possível ler o arquivo: {erro}")
        return []
    if not linhas:
        r.erro(base, caminho, "arquivo vazio")
        return []
    titulos = [t.strip().lstrip("\ufeff").upper() for t in linhas[0]]
    faltam = [c for c in cabecalho if c not in titulos]
    if faltam:
        r.erro(base, caminho, f"cabeçalho sem as colunas: {', '.join(faltam)}", cabecalho)
        return []
    posicao = {c: titulos.index(c) for c in cabecalho}
    resultado = []
    for numero, linha in enumerate(linhas[1:], start=2):
        if not any(c.strip() for c in linha):
            continue
        celulas = {c: (linha[posicao[c]].strip() if posicao[c] < len(linha) else "") for c in cabecalho}
        if not celulas[obrigatoria]:
            r.erro(base, caminho, f"linha {numero}: '{obrigatoria}' vazio")
            continue
        for coluna in colunas_data:
            if celulas[coluna] and not DATA_BR.match(celulas[coluna]):
                r.erro(base, caminho, f"linha {numero}: '{coluna}' = {celulas[coluna]!r}; use dd/mm/aaaa")
        resultado.append([celulas[c] or None for c in cabecalho])
    return resultado


FLAG_SN = re.compile(r"^[SN]$")
VALOR_BR = re.compile(r"^-?\d+(?:\.\d{3})*(?:,\d+)?$|^-?\d+(?:\.\d+)?$")
COMPETENCIA = re.compile(r"^(0[1-9]|1[0-2])/\d{4}$")
MAXIMO_ERROS_POR_ARQUIVO = 5


def _ler_historico_csv(r, chave, caminho):
    """Histórico salarial no layout da importação do PJe-Calc: MES_ANO;<NOME>;FGTS;FGTS_REC.;CONTRIBUICAO_SOCIAL;CONTRIBUICAO_SOCIAL_REC.

    A 2ª coluna traz o nome do histórico (o SAP manda o próprio nome; o exemplo do PJe-Calc manda 'VALOR').
    Devolve (nome, caminho) ou None se o arquivo tiver erro.
    """
    base = f"arquivos.{chave}"
    try:
        linhas = _linhas_do_csv(caminho)
    except OSError as erro:
        r.erro(base, caminho, f"não foi possível ler o arquivo: {erro}")
        return None
    if not linhas or len(linhas[0]) < 2 or not linhas[0][1].strip():
        r.erro(base, caminho, "cabeçalho inválido: a 1ª coluna é a competência (MM/AAAA) e a 2ª traz o nome do histórico salarial")
        return None
    nome = linhas[0][1].strip().lstrip("\ufeff")[:120]
    if nome.upper() == "VALOR":
        r.erro(base, caminho, "o t\u00edtulo da 2\u00aa coluna \u00e9 o NOME do hist\u00f3rico salarial (ex.: 'ADICIONAL NOTURNO'); "
                              "'VALOR' \u00e9 o t\u00edtulo gen\u00e9rico do exemplo do PJe-Calc")
        return None
    erros_antes, validas = len(r.erros), 0
    for numero, linha in enumerate(linhas[1:], start=2):
        if not any(c.strip() for c in linha):
            continue
        celulas = [c.strip() for c in linha] + [""] * 6
        problema = None
        if not COMPETENCIA.match(celulas[0]):
            problema = f"competência {celulas[0]!r}; use MM/AAAA"
        elif not VALOR_BR.match(celulas[1]):
            problema = f"valor {celulas[1]!r}; use número, com vírgula decimal (1234,56)"
        else:
            ruins = [c for c in celulas[2:6] if c and not FLAG_SN.match(c.upper())]
            if ruins:
                problema = f"marcas FGTS/INSS {ruins!r}; use S ou N"
        if problema:
            if len(r.erros) - erros_antes < MAXIMO_ERROS_POR_ARQUIVO:
                r.erro(base, caminho, f"linha {numero}: {problema}")
            continue
        validas += 1
    if validas == 0 and len(r.erros) == erros_antes:
        r.erro(base, caminho, "arquivo sem nenhuma linha de competência")
    return None if len(r.erros) > erros_antes else (nome, caminho)


def _conferir_periodos_de_ferias(r, chave, caminho, linhas):
    """O PJe-Calc recusa a importação inteira se um período aquisitivo terminar depois da demissão/data final
    ("As férias definidas no arquivo não podem ser anterior a Data de Admissão e nem posterior a Data de Demissão/Data Final")."""
    admissao = r.valores.get("data_admissao")
    final = r.valores.get("termino_calculo") or r.valores.get("data_rescisao")
    if not isinstance(admissao, int) or not isinstance(final, int):
        return
    d_admissao, d_final = ORIGEM_EXCEL + timedelta(days=admissao), ORIGEM_EXCEL + timedelta(days=final)
    for numero, linha in enumerate(linhas, start=2):
        achado = re.match(r"^(\d{4})/(\d{4})$", str(linha[0] or ""))
        if not achado:
            r.erro(f"arquivos.{chave}", caminho, f"linha {numero}: RELATIVAS {linha[0]!r}; use AAAA/AAAA")
            continue
        ano = int(achado.group(1))
        dia = 28 if (d_admissao.month, d_admissao.day) == (2, 29) else d_admissao.day
        inicio = datetime(ano, d_admissao.month, dia)
        fim = datetime(ano + 1, d_admissao.month, dia) - timedelta(days=1)
        if inicio < d_admissao or fim > d_final:
            r.erro(f"arquivos.{chave}", caminho,
                   f"linha {numero}: período aquisitivo {linha[0]} ({inicio:%d/%m/%Y} a {fim:%d/%m/%Y}) fora do contrato "
                   f"({d_admissao:%d/%m/%Y} a {d_final:%d/%m/%Y}); o PJe-Calc recusa o arquivo inteiro. "
                   "As férias proporcionais o PJe-Calc calcula sozinho: não as mande no .csv")


SITUACOES_DE_FERIAS = {"G": "Gozadas", "GP": "Gozadas Parcialmente", "I": "Indenizadas", "P": "Perdidas"}


def _conferir_situacoes_de_ferias(r, chave, caminho, linhas):
    """Só G, GP, I e P têm significado no PJe-Calc 2.16.0. Outros códigos ou são recusados por ele ou viram GOZADAS:
    "NG" é aceito e gravado como GOZADAS (testado na tela em 13/10/2026) — o oposto de "não gozadas"."""
    posicao = CABECALHO_FERIAS.index("SITUACAO")
    for numero, linha in enumerate(linhas, start=2):
        situacao = str(linha[posicao] or "").strip().upper()
        if situacao and situacao not in SITUACOES_DE_FERIAS:
            r.erro(f"arquivos.{chave}", caminho,
                   f"linha {numero}: SITUACAO {situacao!r}; use G, GP, I ou P (o PJe-Calc grava {situacao!r} como Gozadas). "
                   "Férias não gozadas e já vencidas: I (indenizadas)", sorted(SITUACOES_DE_FERIAS))


def _arquivos(r, caminho_json):
    bloco = r.dados.get("arquivos")
    if not bloco:
        return
    if not isinstance(bloco, dict):
        r.erro("arquivos", bloco, "deve ser um objeto { faltas, ferias, historico-salarial, cartao-de-ponto }")
        return
    pasta = os.path.dirname(os.path.abspath(caminho_json))
    for chave, valor in bloco.items():
        base = f"arquivos.{chave}"
        if chave not in ARQUIVOS_CONHECIDOS:
            r.ignorar(base, "arquivo sem correspondente na automação")
            continue
        if valor in (None, ""):
            continue
        if chave == "historico-salarial" and isinstance(valor, list) and valor and all(isinstance(v, str) for v in valor):
            caminhos = valor
        elif isinstance(valor, str):
            caminhos = [valor]
        else:
            r.erro(base, valor, "deve ser o caminho do arquivo, em texto")
            continue
        if chave != "historico-salarial" and len(caminhos) != 1:
            r.erro(base, valor, "deve ser o caminho de um único arquivo")
            continue
        resolvidos = [_caminho_do_arquivo(r, chave, v, pasta) for v in caminhos]
        if None in resolvidos:
            continue
        caminho = resolvidos[0]
        if chave == "historico-salarial":
            com_cs = []
            for um in resolvidos:
                lido = _ler_historico_csv(r, chave, um)
                if lido and lido[0].upper() in (h[0].upper() for h in r.historicos):
                    r.erro(base, um, f"já há outro histórico salarial chamado {lido[0]!r} neste pedido")
                elif lido:
                    r.historicos.append(lido)
                    if any(len(l) > 4 and l[4].strip().upper() == "S" for l in _linhas_do_csv(um)[1:]):
                        com_cs.append(lido[0])
            if r.historicos and not com_cs:
                r.avisos.append("arquivos.historico-salarial: nenhum histórico com CONTRIBUICAO_SOCIAL = S; o PJe-Calc usa a última "
                                "remuneração como salário pago na Contribuição Social (marque S nas parcelas do salário de contribuição)")
            r.usados.add(base)
        elif chave == "faltas":
            r.faltas = _ler_csv_da_tela(r, chave, caminho, CABECALHO_FALTAS, "INICIO", ("INICIO", "FIM"))
            r.usados.add(base)
        elif chave == "ferias":
            r.ferias = _ler_csv_da_tela(r, chave, caminho, CABECALHO_FERIAS, "RELATIVAS",
                                        ("G1INI", "G1FIM", "G2INI", "G2FIM", "G3INI", "G3FIM"))
            _conferir_periodos_de_ferias(r, chave, caminho, r.ferias)
            _conferir_situacoes_de_ferias(r, chave, caminho, r.ferias)
            r.usados.add(base)
        else:
            r.arquivos[chave] = caminho
            r.ignorar(base, "arquivo recebido, mas esta importação ainda não é feita pela automação")


# ---------------------------------------------------------------- bloco novo: telas

def _telas(r):
    telas = r.dados.get("telas") or {}
    dados = telas.get("dados-do-calculo") or {}
    base = "telas.dados-do-calculo"
    simples = {"reclamante_nome": "nome_parte1", "reclamado_nome": "nome_parte2"}
    for campo, chave in simples.items():
        if dados.get(campo):
            r.usar(f"{base}.{campo}", chave, str(dados[campo])[:150])
    for campo, chave in (("reclamante_cpf", "doc_parte1"), ("reclamado_cnpj", "doc_parte2"), ("reclamado_cpf", "doc_parte2")):
        if dados.get(campo):
            r.usar(f"{base}.{campo}", chave, documento_da_planilha(dados[campo]))
    if dados.get("numero_processo"):
        if PADRAO_CNJ.match(str(dados["numero_processo"])):
            r.usar(f"{base}.numero_processo", "numero_processo", str(dados["numero_processo"]))
        else:
            r.erro(f"{base}.numero_processo", dados["numero_processo"], "número CNJ fora do formato 0000000-00.0000.0.00.0000")
    for campo, chave in (("admissao", "data_admissao"), ("demissao", "data_rescisao"), ("ajuizamento", "data_ajuizamento"),
                         ("data_inicial", "inicio_calculo"), ("data_final", "termino_calculo")):
        if dados.get(campo):
            r.usar(f"{base}.{campo}", chave, r.data(f"{base}.{campo}", dados[campo]))
    for campo, chave in (("ultima_remuneracao", "ultima_remuneracao"), ("maior_remuneracao", "maior_remuneracao"),
                         ("valor_da_causa", "valor_da_causa")):
        if campo in dados:
            valor = numero_da_planilha(dados[campo])
            if valor is None:
                r.erro(f"{base}.{campo}", dados[campo], "valor em reais deve ser número")
            r.usar(f"{base}.{campo}", chave, valor)
    if "carga_horaria" in dados:
        achado = re.search(r"\d+(?:[.,]\d+)?", str(dados["carga_horaria"]))
        if achado:
            r.usar(f"{base}.carga_horaria", "carga_horaria", float(achado.group(0).replace(",", ".")))
        else:
            r.erro(f"{base}.carga_horaria", dados["carga_horaria"], "carga horária sem número")
    marcacoes = {
        "prescricao_quinquenal": "aplicar_prescricao_verbas", "prescricao_fgts": "aplicar_prescricao_FGTS",
        "projetar_aviso_indenizado": "projetar_aviso_previo_indenizado", "limitar_avos": "limitar_avos_ao_periodo_do_calculo",
        "zerar_valor_negativo": "zerar_valor_negativo_padrao", "feriados_estaduais": "considerar_feriados_estaduais",
        "feriados_municipais": "considerar_feriados_municipais",
        "ponto_facultativo_sexta_feira_santa": "ponto_facultutativo_sextafeirasanta",
        "ponto_facultativo_corpus_christi": "ponto_facultutativo_corpuschristi", "ponto_facultativo_carnaval": "ponto_facultutativo_carnaval",
    }
    for campo, chave in marcacoes.items():
        if campo in dados:
            if isinstance(dados[campo], bool):
                r.usar(f"{base}.{campo}", chave, _texto(dados[campo]))
            else:
                r.erro(f"{base}.{campo}", dados[campo], "use true ou false")
    prazo = None
    if dados.get("prazo_aviso_previo"):
        aceitos = CATALOGO["telas"]["dados-do-calculo"]["listas"]["apuracaoPrazoDoAvisoPrevio"]
        prazo = next((a for a in aceitos if _sem_acento(a) == _sem_acento(dados["prazo_aviso_previo"])), None)
        if prazo is None:
            r.erro(f"{base}.prazo_aviso_previo", dados["prazo_aviso_previo"], "valor não reconhecido", aceitos)
        r.usar(f"{base}.prazo_aviso_previo", "prazo_de_aviso_previo", prazo)
    if "dias_aviso_previo" in dados:
        dias = numero_da_planilha(dados["dias_aviso_previo"])
        if dias is None or dias != int(dias) or dias <= 0:
            r.erro(f"{base}.dias_aviso_previo", dados["dias_aviso_previo"], "número inteiro de dias")
        else:
            r.usar(f"{base}.dias_aviso_previo", "quantidade_dias_aviso_previo", int(dias))
    if prazo == "Informado" and "quantidade_dias_aviso_previo" not in r.valores and not any(
            e["campo"] == f"{base}.dias_aviso_previo" for e in r.erros):
        # O PJe-Calc recusa o formulário ("Campo obrigatório: Quantidade") se o prazo é Informado e não há dias.
        fim_aviso, rescisao = _serial(dados.get("aviso_previo_indenizado")), r.valores.get("data_rescisao")
        if fim_aviso and rescisao and 0 < fim_aviso - rescisao <= 90:
            r.usar(f"{base}.aviso_previo_indenizado", "quantidade_dias_aviso_previo", fim_aviso - rescisao)
            r.avisos.append(f"Dias do aviso prévio deduzidos de aviso_previo_indenizado menos a demissão: {fim_aviso - rescisao}. "
                            "Mande 'dias_aviso_previo' para não depender disso.")
        else:
            r.erro(f"{base}.dias_aviso_previo", dados.get("dias_aviso_previo"),
                   "prazo_aviso_previo 'Informado' exige a quantidade de dias: mande 'dias_aviso_previo' (inteiro)")
    if dados.get("comentarios"):
        if len(str(dados["comentarios"])) > 255:
            r.avisos.append(f"comentarios tem {len(str(dados['comentarios']))} caracteres; o PJe-Calc aceita 255 e o resto foi cortado.")
        r.usar(f"{base}.comentarios", "comentarios_parametros", str(dados["comentarios"])[:255])
    if "sabado_dia_util" in dados:
        r.usar(f"{base}.sabado_dia_util", "sabado_como_dia_util", _texto(bool(dados["sabado_dia_util"])))
    if dados.get("regime") or dados.get("regime_trabalho"):
        campo = "regime" if dados.get("regime") else "regime_trabalho"
        aceitos = CATALOGO["telas"]["dados-do-calculo"]["listas"]["tipoDaBaseTabelada"]
        if dados[campo] in aceitos:
            r.usar(f"{base}.{campo}", "regime_trabalho", dados[campo])
        else:
            r.erro(f"{base}.{campo}", dados[campo], "valor não reconhecido", aceitos)
    if dados.get("uf") and dados.get("estado") and str(dados["uf"]).upper() != str(dados["estado"]).upper():
        r.erro(f"{base}.estado", dados["estado"], f"'estado' diferente de 'uf' ({dados['uf']}); mande só 'uf'")
    elif dados.get("estado"):
        r.usados.add(f"{base}.estado")
    if dados.get("uf") or dados.get("estado") or dados.get("municipio"):
        uf, municipio = str(dados.get("uf") or dados.get("estado") or "").upper(), dados.get("municipio")
        if uf not in UFS:
            r.erro(f"{base}.uf", dados.get("uf"), "UF não reconhecida", sorted(UFS))
        else:
            opcao = opcao_de_municipio(municipio or "", CATALOGO["municipios"].get(uf, []))
            if opcao is None:
                r.erro(f"{base}.municipio", municipio, f"município não está na lista do PJe-Calc para {uf}")
            else:
                r.valores.pop("municipio", None)
                r.usar(f"{base}.uf", "uf", uf)
                r.usar(f"{base}.municipio", "municipio", opcao)

    fgts = telas.get("fgts") or {}
    if "fgts_destino" in fgts:
        texto = _sem_acento(fgts["fgts_destino"])
        destino = "Pagar" if "pagar" in texto else "Recolher" if "recolher" in texto else None
        if destino is None:
            r.erro("telas.fgts.fgts_destino", fgts["fgts_destino"], "valor não reconhecido", ["Pagar", "Recolher à conta vinculada"])
        r.usar("telas.fgts.fgts_destino", "destino_fgts", destino)
    if "fgts_calcular_multa" in fgts:
        r.usar("telas.fgts.fgts_calcular_multa", "multa_fgts", _sim_nao(bool(fgts["fgts_calcular_multa"])))

    custas = telas.get("custas-judiciais") or {}
    if "custas_reclamado" in custas:
        texto = _sem_acento(custas["custas_reclamado"])
        tipo = ("Não se Aplica" if "nao se aplica" in texto else "Calculada 2%" if "2%" in texto
                else "Informada" if "informad" in texto else None)
        if tipo is None:
            r.erro("telas.custas-judiciais.custas_reclamado", custas["custas_reclamado"], "valor não reconhecido",
                   CATALOGO["telas"]["custas-judiciais"]["opcoes"]["tipoDeCustasDeConhecimentoDoReclamado"])
        elif tipo == "Informada":
            r.erro("telas.custas-judiciais.custas_reclamado", custas["custas_reclamado"], "custas informadas ainda não suportadas pelo .json")
        elif "custas" not in r.dados:
            r.usados.add("telas.custas-judiciais.custas_reclamado")
            r.familias.append(("custas", [("custas_reclamado_conhecimento", tipo), ("custas_recda_conhecimento_info_vcto", "-"),
                                          ("custas_recda_conhecimento_info_valor", "-")]))
        else:
            r.ignorar("telas.custas-judiciais.custas_reclamado", "o bloco 'custas' já define as custas do reclamado")

    contribuicao = telas.get("contribuicao-social") or {}
    if contribuicao.get("cs_atividade_economica"):
        atividade = str(contribuicao["cs_atividade_economica"]).strip()
        anterior = r.valores.get("cont_social_aliquota_empregador")
        if anterior and anterior != atividade:
            r.erro("telas.contribuicao-social.cs_atividade_economica", atividade,
                   f"diferente de dadosDoCalculo.atividadeEconomica ('{anterior}'); mande a mesma atividade nos dois")
        else:
            r.usar("telas.contribuicao-social.cs_atividade_economica", "cont_social_aliquota_empregador", atividade)

    correcao = telas.get("correcao-juros-multa") or {}
    if "cj_correcao" in correcao:
        aceitos = CATALOGO["telas"]["correcao-juros-multa"]["listas"]["indiceTrabalhista"]
        valor = str(correcao["cj_correcao"])
        entre_parenteses = re.search(r"\(([^)]+)\)\s*$", valor)
        indice = valor if valor in aceitos else entre_parenteses.group(1) if entre_parenteses and entre_parenteses.group(1) in aceitos else None
        if indice is None:
            r.erro("telas.correcao-juros-multa.cj_correcao", valor, "índice não reconhecido", aceitos)
        r.usar("telas.correcao-juros-multa.cj_correcao", "indice_trabalhista", indice)

    for tela, campos in telas.items():
        for campo in (campos or {}):
            caminho = f"telas.{tela}.{campo}"
            if caminho not in r.usados and not any(e["campo"] == caminho for e in r.erros):
                if tela in ("salario-familia", "seguro-desemprego", "previdencia-privada", "pensao-alimenticia",
                            "imposto-de-renda", "cartao-de-ponto"):
                    r.ignorar(caminho, "tela ainda não automatizada")
                else:
                    r.ignorar(caminho, "campo sem correspondente na automação")


# Chave que diz se a planilha já traz a família (na v3.41 os blocos vazios têm '-' nela).
PORTADORES = {
    "honorarios": re.compile(r"^(honorarios_periciais_descricao|honorarios_contratuais_tipob)_\d+$"),
    "multas": re.compile(r"^multas_indenizacoes_credor_\d+$"),
    "custas": re.compile(r"^(custas_reclamado_conhecimento|custas_recolhidas_rcdo\d+_valor)$"),
    # a planilha da casa traz um advogado por parte (advogado_parte1/2): se ela traz, prevalece a parte inteira
    "advogados_reclamante": re.compile(r"^advogado_parte1$"),
    "advogados_reclamado": re.compile(r"^advogado_parte2$"),
}


def combinar_com_planilha(interpretacao, existentes):
    """Planilha + .json: devolve (complemento, forçados, avisos).

    Campo avulso: a planilha manda; o .json só preenche o que ela deixou vazio.
    Família (honorários, multas, custas): é um bloco inteiro. Se a planilha já a traz, prevalece inteira; se não,
    a do .json substitui o bloco todo — inclusive os '0' e o 'qtd' da v3.41, que senão sairiam misturados.
    """
    from Calculo.leitura_planilha import valor_vazio

    avisos = []
    complemento = interpretacao.pares_avulsos()
    for chave, valor in complemento:
        atual = existentes.get(chave)
        if chave in existentes and not valor_vazio(atual) and not valor_vazio(valor) and str(atual) != str(valor):
            avisos.append(f"a planilha prevaleceu em '{chave}' (planilha={atual!r}; .json={valor!r})")
    forcados = []
    for nome, familia in interpretacao.familias:
        if any(PORTADORES[nome].match(chave) and not valor_vazio(valor) for chave, valor in existentes.items()):
            avisos.append(f"a planilha já traz {nome}; os do .json foram ignorados")
        else:
            forcados += familia
    return complemento, forcados, avisos


def criar_planilha_do_pedido(caminho_json, pares, execucao_id, faltas=None, ferias=None, historicos=None):
    """Pedido sem planilha: monta, ao lado do .json, uma planilha mínima que os fluxos já sabem ler.

    PJE-BD com as chaves traduzidas; Faltas e Férias com as linhas dos .csv (ou vazias, 'Excluir Linha'); e a aba SEM_HISTORICO, que faz o
    Histórico Salarial e a base do INSS serem pulados com aviso. O PDF e o .PJC saem na mesma pasta (a do .json).
    """
    import openpyxl
    from Calculo.leitura_planilha import ABA_SEM_HISTORICO, ABA_CSV_HISTORICO

    destino = Path(caminho_json).with_name(f"{execucao_id}_automacao_pedido.xlsx")
    livro = openpyxl.Workbook()
    aba = livro.active
    aba.title = "PJE-BD"
    aba.append([])
    aba.append(["IDENTIFICADOR", "INFORMACAO"])
    for chave, valor in pares:
        aba.append([chave, valor])
    livro.create_sheet("PJeFaltas").append(["INICIO", "FIM", "JUSTIFICADA", "REINICIAR_PER_AQ", "JUSTIFICATIVA"])
    for linha in faltas or [["Excluir Linha"]]:
        livro["PJeFaltas"].append(linha)
    livro.create_sheet("PJeFérias").append(["RELATIVAS", "PRAZO", "SITUACAO", "DOBRA", "ABONO", "QTD_DIAS_ABONO",
                                            "G1INI", "G1FIM", "G1DOBRA", "G2INI", "G2FIM", "G2DOBRA", "G3INI", "G3FIM", "G3DOBRA"])
    for linha in ferias or [["Excluir Linha"]]:
        livro["PJeFérias"].append(linha)
    livro.create_sheet(ABA_SEM_HISTORICO).append(["Pedido montado só com o .json de lançamentos, sem histórico salarial."])
    if historicos:
        # a tela do Histórico Salarial importa estes .csv (nome do histórico, caminho) no lugar da grade da planilha
        aba_csv = livro.create_sheet(ABA_CSV_HISTORICO)
        for nome, arquivo in historicos:
            aba_csv.append([nome, arquivo])
    livro.save(destino)
    return str(destino)


def interpretar(caminho):
    """Lê e traduz o .json. Levanta LancamentosIlegiveis se o arquivo não for do contrato; erros de campo ficam em .erros."""
    try:
        dados = json.loads(Path(caminho).read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as erro:
        raise LancamentosIlegiveis(f"não foi possível ler o .json de lançamentos: {erro}")
    if not isinstance(dados, dict):
        raise LancamentosIlegiveis("o .json de lançamentos precisa ser um objeto { … }")
    contrato = str(dados.get("contrato") or "")
    if contrato != CONTRATO and not contrato.startswith(CONTRATO + "."):
        raise LancamentosIlegiveis(f"contrato '{contrato}' não suportado; esperado '{CONTRATO}'")

    r = Interpretacao(dados)
    _dados_do_calculo(r)
    _fgts(r)
    _custas(r)
    _honorarios(r)
    _multas(r)
    _telas(r)
    _advogados(r)
    _arquivos(r, caminho)
    if "cont_social_aliquota_empregador" in r.valores:
        # A CNAE só é lida quando a leitura chega em entidade_filantropica; sem valor, nenhuma das três opções é marcada.
        for gatilho in ("processo_de_agroindustria", "empresa_enquadrada_simples", "empresa_com_desoneracao", "entidade_filantropica"):
            r.valores.setdefault(gatilho, "<nao_preenchido>")
    from servico.verbas_pedido import interpretar_verbas
    interpretar_verbas(r)
    for folha in _folhas({k: v for k, v in dados.items() if k not in ("telas", "verbas", "arquivos", "reflexosManuais", "advogados")}):
        if folha and folha not in META and folha not in r.usados and not folha.endswith("contrato"):
            r.ignorar(folha, "campo não reconhecido")
    return r
