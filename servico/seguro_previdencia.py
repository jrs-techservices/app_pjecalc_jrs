"""seguroDesemprego e previdenciaPrivada do .json → operações das telas Seguro-desemprego e Previdência Privada (PJe-Calc 2.16).

Campo ausente = padrão da tela. A porta valida e guarda na PJE-BD (`seguro_desemprego_ops`, `previdencia_privada_ops`) a lista
de operações, que a tela aplica e confere: ["caixa", id, bool] · ["radio", id, rótulo] · ["lista", id, opção] ·
["texto", id, valor] · ["mais", "historico", nome] · ["mais", "verba", [descrição, "Sim"|"Não"]] · ["periodo", ini, fim, alíquota].
"""
import json
import re

from servico.verbas_pedido import normalizar_descricao

SOLICITACOES = {"PRIMEIRA": "Primeira Solicitação", "SEGUNDA": "Segunda Solicitação", "DEMAIS": "Demais Solicitações"}
TIPOS_VALOR = {"INFORMADO": "Informado", "CALCULADO": "Calculado"}
# a lista da tela varia com o cálculo (no teste não havia "Última Remuneração"): a tela interrompe se a opção não existir
SALARIOS_PAGOS = {"NENHUM": "Nenhum", "ULTIMA_REMUNERACAO": "Última Remuneração", "MAIOR_REMUNERACAO": "Maior Remuneração",
                  "HISTORICO_SALARIAL": "Histórico Salarial"}
CAMPOS_SEGURO = {"apurar", "empregadoDomestico", "tipoSolicitacao", "tipoValor", "comporPrincipal", "valor", "parcelas",
                 "salariosPagos", "salariosDevidos"}
COMPETENCIA = re.compile(r"^(\d{4})-(0[1-9]|1[0-2])$")


def _seguro_desemprego(r):
    bloco = r.dados.get("seguroDesemprego")
    if bloco is None:
        return
    base = "seguroDesemprego"
    erros_antes = len(r.erros)
    if not isinstance(bloco, dict):
        r.erro(base, bloco, "deve ser um objeto { apurar, tipoValor, ... }")
        return
    for campo in bloco:
        if campo not in CAMPOS_SEGURO:
            r.erro(f"{base}.{campo}", bloco[campo], "campo não reconhecido", sorted(CAMPOS_SEGURO))
    b = {k: v for k, v in bloco.items() if v is not None}

    def booleano(campo):
        if campo in b and not isinstance(b[campo], bool):
            r.erro(f"{base}.{campo}", b[campo], "use true ou false")
            return None
        return b.get(campo)

    apurar = booleano("apurar")
    ops = []
    if apurar is not None:
        ops.append(["caixa", "apurarSeguroDesemprego", apurar])
    if apurar is not True:
        sobra = [c for c in b if c != "apurar" and c in CAMPOS_SEGURO]
        if sobra:
            r.erro(f"{base}.{sobra[0]}", b[sobra[0]], "só com apurar true (a tela desabilita tudo sem ele)")
        return _guardar(r, base, "seguro_desemprego_ops", ops, erros_antes)
    domestico = booleano("empregadoDomestico")
    if domestico is not None:
        ops.append(["caixa", "apurarEmpregadoDomestico", domestico])
    tipo = b.get("tipoValor", "CALCULADO")
    if tipo not in TIPOS_VALOR:
        r.erro(f"{base}.tipoValor", tipo, "valor não reconhecido", sorted(TIPOS_VALOR))
        tipo = None
    elif "tipoValor" in b:
        ops.append(["radio", "valor", TIPOS_VALOR[tipo]])
    compor = booleano("comporPrincipal")
    if compor is not None:
        ops.append(["radio", "comporPrincipal", "Sim" if compor else "Não"])
    if "tipoSolicitacao" in b:
        if b["tipoSolicitacao"] not in SOLICITACOES:
            r.erro(f"{base}.tipoSolicitacao", b["tipoSolicitacao"], "valor não reconhecido", sorted(SOLICITACOES))
        else:
            ops.append(["lista", "solicitacao", SOLICITACOES[b["tipoSolicitacao"]]])
    # INFORMADO: só o valor
    if tipo == "INFORMADO":
        valor = b.get("valor")
        if isinstance(valor, bool) or not isinstance(valor, (int, float)) or valor <= 0:
            r.erro(f"{base}.valor", valor, "obrigatório com tipoValor INFORMADO: número positivo")
        else:
            ops.append(["texto", "valorInformado", f"{valor:.2f}".replace(".", ",")])
        for campo in ("parcelas", "salariosPagos", "salariosDevidos"):
            if campo in b:
                r.erro(f"{base}.{campo}", b[campo], "só com tipoValor CALCULADO")
        return _guardar(r, base, "seguro_desemprego_ops", ops, erros_antes)
    if "valor" in b:
        r.erro(f"{base}.valor", b["valor"], "só com tipoValor INFORMADO")
    if "parcelas" in b:
        parcelas = b["parcelas"]
        if isinstance(parcelas, bool) or not isinstance(parcelas, int) or not 1 <= parcelas <= 10:
            r.erro(f"{base}.parcelas", parcelas, "número inteiro de parcelas (1 a 10)")
        else:
            ops.append(["texto", "numeroDeParcelas", str(parcelas)])
    if domestico is True:
        for campo in ("salariosPagos", "salariosDevidos"):
            if campo in b:
                r.erro(f"{base}.{campo}", b[campo], "não existe para empregado doméstico (a tela esconde a remuneração)")
        return _guardar(r, base, "seguro_desemprego_ops", ops, erros_antes)
    pagos = b.get("salariosPagos")
    if pagos is not None:
        if not isinstance(pagos, dict) or pagos.get("tipo") not in SALARIOS_PAGOS or not set(pagos) <= {"tipo", "historicos"}:
            r.erro(f"{base}.salariosPagos", pagos, "deve ser { tipo, historicos }", sorted(SALARIOS_PAGOS))
        else:
            ops.append(["radio", "tipoSalarioPago", SALARIOS_PAGOS[pagos["tipo"]]])
            historicos = pagos.get("historicos")
            if pagos["tipo"] != "HISTORICO_SALARIAL":
                if historicos:
                    r.erro(f"{base}.salariosPagos.historicos", historicos, "só com tipo HISTORICO_SALARIAL")
            elif not isinstance(historicos, list) or not historicos or not all(isinstance(h, str) and h.strip() for h in historicos):
                # a tela recusa salvar: "Deve haver pelo menos um registro de Histórico."
                r.erro(f"{base}.salariosPagos.historicos", historicos, "obrigatório com HISTORICO_SALARIAL: lista de nomes de histórico")
            else:
                nomes = {h[0].strip().upper() for h in r.historicos}
                for nome in historicos:
                    if nome.strip().upper() not in nomes:
                        r.erro(f"{base}.salariosPagos.historicos", nome, "não há histórico salarial com este nome no pedido",
                               sorted(nomes))
                    else:
                        ops.append(["mais", "historico", nome.strip().upper()])
    devidos = b.get("salariosDevidos")
    if devidos is not None:
        descricoes = {v.get("id"): normalizar_descricao(v.get("descricao") or "") for v in (r.dados.get("verbas") or [])
                      if isinstance(v, dict)}
        if not isinstance(devidos, list):
            r.erro(f"{base}.salariosDevidos", devidos, "deve ser uma lista de { verba, integralizar }")
        else:
            vistas = set()
            for n, item in enumerate(devidos):
                caminho = f"{base}.salariosDevidos[{n}]"
                if not isinstance(item, dict) or not set(item) <= {"verba", "integralizar"} or "verba" not in item:
                    r.erro(caminho, item, "deve ser { verba: <id de verbas[]>, integralizar }")
                elif item["verba"] not in descricoes:
                    r.erro(f"{caminho}.verba", item["verba"], "não há verba com este id no pedido", sorted(k for k in descricoes if k))
                elif item["verba"] in vistas:
                    r.erro(f"{caminho}.verba", item["verba"], "verba repetida")
                elif "integralizar" in item and not isinstance(item["integralizar"], bool):
                    r.erro(f"{caminho}.integralizar", item["integralizar"], "use true ou false")
                else:
                    vistas.add(item["verba"])
                    ops.append(["mais", "verba", [descricoes[item["verba"]], "Sim" if item.get("integralizar") else "Não"]])
    return _guardar(r, base, "seguro_desemprego_ops", ops, erros_antes)


def _competencia(r, caminho, valor):
    m = COMPETENCIA.match(str(valor or ""))
    if not m:
        r.erro(caminho, valor, "use AAAA-MM")
        return None
    return int(m.group(1)), int(m.group(2))


def _previdencia_privada(r):
    bloco = r.dados.get("previdenciaPrivada")
    if bloco is None:
        return
    base = "previdenciaPrivada"
    erros_antes = len(r.erros)
    if not isinstance(bloco, dict):
        r.erro(base, bloco, "deve ser um objeto { apurar, aliquotas }")
        return
    for campo in bloco:
        if campo not in ("apurar", "aliquotas"):
            r.erro(f"{base}.{campo}", bloco[campo], "campo não reconhecido", ["apurar", "aliquotas"])
    apurar = bloco.get("apurar")
    if apurar is not None and not isinstance(apurar, bool):
        r.erro(f"{base}.apurar", apurar, "use true ou false")
        return
    ops = [] if apurar is None else [["caixa", "apurarPrevidenciaPrivada", apurar]]
    aliquotas = bloco.get("aliquotas")
    if apurar is not True:
        if aliquotas:
            r.erro(f"{base}.aliquotas", aliquotas, "só com apurar true")
        return _guardar(r, base, "previdencia_privada_ops", ops, erros_antes)
    if not isinstance(aliquotas, list) or not aliquotas:
        r.erro(f"{base}.aliquotas", aliquotas, "obrigatória com apurar true: [{ competenciaInicial, competenciaFinal, aliquota }]")
        return
    # o PJe-Calc não liquida sem isso: "Para apurar Previdência Privada, marque a incidência correspondente em pelo menos
    # uma das verbas registradas no cálculo."
    # só as verbas principais (reflexo manual com a incidência não foi testado na tela)
    itens = [i for i in (r.dados.get("verbas") or []) if isinstance(i, dict)]
    if not any((i.get("incidencias") or {}).get("previdenciaPrivada") is True for i in itens if isinstance(i.get("incidencias"), dict)):
        r.erro(f"{base}.apurar", True, "o PJe-Calc só liquida com pelo menos uma verba com "
                                       "incidencias.previdenciaPrivada true")
    admissao = str((r.dados.get("dadosDoCalculo") or {}).get("dataAdmissao") or "")[:7]
    periodos = []
    for n, item in enumerate(aliquotas):
        caminho = f"{base}.aliquotas[{n}]"
        if not isinstance(item, dict) or not set(item) <= {"competenciaInicial", "competenciaFinal", "aliquota"}:
            r.erro(caminho, item, "deve ser { competenciaInicial, competenciaFinal, aliquota }")
            continue
        ini = _competencia(r, f"{caminho}.competenciaInicial", item.get("competenciaInicial"))
        fim = _competencia(r, f"{caminho}.competenciaFinal", item.get("competenciaFinal"))
        aliquota = item.get("aliquota")
        if isinstance(aliquota, bool) or not isinstance(aliquota, (int, float)) or not 0 < aliquota <= 100:
            r.erro(f"{caminho}.aliquota", aliquota, "percentual entre 0 e 100 (5.0 = 5%)")
            continue
        if not ini or not fim:
            continue
        if fim < ini:
            r.erro(f"{caminho}.competenciaFinal", item["competenciaFinal"], "anterior à competência inicial")
            continue
        if COMPETENCIA.match(admissao) and ini < (int(admissao[:4]), int(admissao[5:7])):
            # a tela recusa: "O valor do campo Competência Inicial deve ser igual ou maior que Data de Admissão"
            r.erro(f"{caminho}.competenciaInicial", item["competenciaInicial"], f"anterior à admissão ({admissao})")
            continue
        for outro_n, (o_ini, o_fim) in periodos:
            if ini <= o_fim and o_ini <= fim:
                r.erro(f"{caminho}.competenciaInicial", item["competenciaInicial"], f"sobrepõe o período de aliquotas[{outro_n}]")
                break
        else:
            periodos.append((n, (ini, fim)))
            ops.append(["periodo", f"{ini[1]:02d}/{ini[0]}", f"{fim[1]:02d}/{fim[0]}", f"{aliquota:.2f}".replace(".", ",")])
    return _guardar(r, base, "previdencia_privada_ops", ops, erros_antes)


def _guardar(r, base, chave, ops, erros_antes):
    if len(r.erros) > erros_antes:
        return
    if ops:
        r.usar(base, chave, json.dumps(ops, ensure_ascii=False))
    else:
        r.usados.add(base)


def interpretar_seguro_e_previdencia(r):
    _seguro_desemprego(r)
    _previdencia_privada(r)
