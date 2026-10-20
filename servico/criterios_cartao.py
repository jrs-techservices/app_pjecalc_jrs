"""cartaoDePonto.criterios do .json → operações da tela Cartão de Ponto › Novo (Critérios de Apuração), PJe-Calc 2.16.

Campo ausente = padrão da tela. A porta valida tudo (lista fechada, formatos, dependências e combinações que a tela
não aceita juntas) e guarda na PJE-BD, em `cartao_ponto_criterios`, a lista de operações em ordem:
["radio", id, rótulo] · ["caixa", id, true/false] · ["texto", id, valor] · ["lista", id, opção].
"""
import json
import re

HORA = re.compile(r"^\d{2}:[0-5]\d$")

FORMAS = {
    "NAO_APURAR": "Não apurar horas extras",
    "EXCEDENTE_DIARIA": "Horas extras excedentes da jornada diária",
    "MAIS_FAVORAVEL": "Horas extras pelo critério mais favorável",
    "SUMULA_85": "Horas extras conforme Súmula 85 do TST",
    "PRIMEIRAS_EM_SEPARADO": "Apurar primeiras horas extras em separado",
    "EXCEDENTE_SEMANAL": "Horas extras excedentes da jornada semanal",
    "EXCEDENTE_MENSAL": "Horas extras excedentes da jornada mensal",
}
HORARIOS_NOTURNOS = {"AGRICOLA": "Atividade agrícola 21:00 às 05:00", "PECUARIA": "Atividade pecuária 20:00 às 04:00",
                     "URBANA": "Atividade urbana 22:00 às 05:00"}
DIAS = {"seg": "valorJornadaSegunda", "ter": "valorJornadaTerca", "qua": "valorJornadaQuarta", "qui": "valorJornadaQuinta",
        "sex": "valorJornadaSexta", "sab": "valorJornadaDiariaSabado", "dom": "valorJornadaDiariaDom"}
INTERJORNADAS = ("10:00", "11:00", "12:00", "14:00", "17:00")


def _entre_semanas(interjornadas):
    """Opções de "entre semanas" que a tela oferece para o "entre jornadas" escolhido (padrão 11:00)."""
    base = interjornadas if isinstance(interjornadas, str) else "11:00"
    horas, minutos = base.split(":")
    return (f"{int(horas) + 24:02d}:{minutos}", base)

# caixas simples: campo do .json → id na tela (na ordem em que a tela as mostra)
CAIXAS_FORMAS = {"considerarFeriados": "considerarFeriado", "extrasFeriadosSeparado": "extraFeriadoSeparado",
                 "extrasDomingosSeparado": "extraDescansoSeparado", "extrasSabadosDomingosSeparado": "extraSabadoDomingoSeparado"}
CAIXAS_JORNADA = {"jornadaDiariaFeriadosTrabalhados": "jornadaDiariaFeriadoTrabalhado",
                  "jornadaDiariaFeriadosNaoTrabalhados": "jornadaDiariaFeriadoNaoTrabalhado"}
CAIXAS_DESCANSO = {"apurarFeriadosTrabalhados": "apurarFeriadosTrabalhados", "apurarDomingosTrabalhados": "apurarDomingosTrabalhados",
                   "apurarSabadosDomingosTrabalhados": "apurarSabadosDomingosTrabalhados",
                   "intervaloArt384": "apurarSupressaoIntervalo384", "intervaloArt72": "apurarSupressaoIntervalo72",
                   "intervaloInsalubridade": "apurarSupressaoIntervaloArt253"}
CAIXAS_INTRA = {"fracionamentoIntrajornadaValido": "considerarFracionamentoIntra",
                "supressaoIntrajornadaIntegral": "apurarSupressaoIntervaloIntraIntegral",
                "supressaoIntrajornadaArt71par4": "apurarSupressaoIntervaloIntraReforma",
                "excessoIntrajornadaSumula118": "apurarExcessoIntervaloIntra",
                "apenasExcessoAlemDaJornada": "apurarApenasExcessoAcimaJornada"}
CAIXAS_NOTURNO = {"apurarHorasNoturnas": "apurarHorasNoturnas", "apurarExtrasNoturnas": "apurarHorasExtrasNoturnas",
                  "reducaoFictaNoturna": "considerarReducaoFictaDaHoraNoturna", "prorrogacaoSumula60": "horarioProrrogadoSumula60",
                  "forcarProrrogacao": "forcarProrrogacao"}
# marcar uma desmarca as outras na tela
EXCLUSIVAS = [("intervaloArt384", "intervaloArt72", "intervaloInsalubridade"),
              ("apurarFeriadosTrabalhados", "apurarDomingosTrabalhados", "apurarSabadosDomingosTrabalhados"),
              ("extrasDomingosSeparado", "extrasSabadosDomingosSeparado")]
OUTROS = {"formaApuracao", "qtHorasSumula85", "qtPrimeirasHorasSeparado", "tolerancia", "toleranciaPorTurno", "toleranciaPorDia",
          "jornadaDiaria", "jornadaSemanal", "jornadaMensal", "art253", "interjornadas", "entreSemanas", "intrajornada4a6",
          "intrajornadaAcima6", "toleranciaIntrajornadaAcima6", "intervaloIntrajornadaMaximo", "horarioNoturno"}
CONHECIDOS = OUTROS | set(CAIXAS_FORMAS) | set(CAIXAS_JORNADA) | set(CAIXAS_DESCANSO) | set(CAIXAS_INTRA) | set(CAIXAS_NOTURNO)


def interpretar_criterios(r, criterios, base="cartaoDePonto.criterios"):
    """Valida o bloco e devolve a lista de operações (ou None se houver erro)."""
    erros_antes = len(r.erros)
    if not isinstance(criterios, dict):
        r.erro(base, criterios, "deve ser um objeto { campo: valor }")
        return None
    for campo in criterios:
        if campo not in CONHECIDOS:
            r.erro(f"{base}.{campo}", criterios[campo], "campo não reconhecido nos Critérios de Apuração", sorted(CONHECIDOS))
    c = {k: v for k, v in criterios.items() if k in CONHECIDOS and v is not None}

    def booleano(campo):
        valor = c.get(campo)
        if valor is not None and not isinstance(valor, bool):
            r.erro(f"{base}.{campo}", valor, "use true ou false")
            return None
        return valor

    def hora(campo, valor=None):
        valor = c.get(campo) if valor is None else valor
        if not isinstance(valor, str) or not HORA.match(valor.strip()):
            r.erro(f"{base}.{campo}", valor, "use HH:MM (ex.: 02:00)")
            return None
        return valor.strip()

    def decimal(campo):
        valor = c.get(campo)
        if isinstance(valor, bool) or not isinstance(valor, (int, float)) or valor <= 0:
            r.erro(f"{base}.{campo}", valor, "use número decimal positivo (ex.: 44 ou 188.57)")
            return None
        return f"{valor:.2f}".replace(".", ",")

    def exige(campo, condicao, mensagem):
        if campo in c and not condicao:
            r.erro(f"{base}.{campo}", c[campo], mensagem)

    ops = []
    # Formas de apuração
    forma = c.get("formaApuracao")
    if forma is not None:
        if forma not in FORMAS:
            r.erro(f"{base}.formaApuracao", forma, "valor não reconhecido", sorted(FORMAS))
        else:
            ops.append(["radio", "tipoApuracaoHorasExtras", FORMAS[forma]])
    exige("qtHorasSumula85", forma == "SUMULA_85", "só com formaApuracao SUMULA_85")
    exige("qtPrimeirasHorasSeparado", forma == "PRIMEIRAS_EM_SEPARADO", "só com formaApuracao PRIMEIRAS_EM_SEPARADO")
    if forma == "SUMULA_85" and "qtHorasSumula85" in c and hora("qtHorasSumula85"):
        ops.append(["texto", "qtsumulatst", c["qtHorasSumula85"].strip()])
    if forma == "PRIMEIRAS_EM_SEPARADO" and "qtPrimeirasHorasSeparado" in c and hora("qtPrimeirasHorasSeparado"):
        ops.append(["texto", "qthoraseparado", c["qtPrimeirasHorasSeparado"].strip()])
    for grupo in EXCLUSIVAS:
        ligados = [campo for campo in grupo if c.get(campo) is True]
        if len(ligados) > 1:
            r.erro(f"{base}.{ligados[1]}", True, f"a tela aceita só um de {', '.join(grupo)} (veio também {ligados[0]})")
    # a tela desabilita: "em separado" com NAO_APURAR; feriados (separado, jornada, trabalhados) sem considerarFeriados
    sem_feriados = c.get("considerarFeriados") is False
    for campo in ("extrasFeriadosSeparado", "extrasDomingosSeparado", "extrasSabadosDomingosSeparado"):
        exige(campo, c.get(campo) is not True or forma != "NAO_APURAR", "não existe com formaApuracao NAO_APURAR")
    for campo in ("extrasFeriadosSeparado", "jornadaDiariaFeriadosTrabalhados", "jornadaDiariaFeriadosNaoTrabalhados",
                  "apurarFeriadosTrabalhados"):
        exige(campo, c.get(campo) is not True or not sem_feriados, "só com considerarFeriados (a tela desabilita sem ele)")
    for campo, alvo in CAIXAS_FORMAS.items():
        if booleano(campo) is not None:
            ops.append(["caixa", alvo, c[campo]])
    # tolerância: os valores ligam a caixa
    tolerancia = booleano("tolerancia")
    valores_tolerancia = [k for k in ("toleranciaPorTurno", "toleranciaPorDia") if k in c]
    if valores_tolerancia and tolerancia is False:
        r.erro(f"{base}.tolerancia", False, "com toleranciaPorTurno/toleranciaPorDia a caixa Tolerância fica ligada")
    elif valores_tolerancia or tolerancia is not None:
        ops.append(["caixa", "tolerancia", bool(valores_tolerancia) or tolerancia])
        for campo in valores_tolerancia:
            if hora(campo):
                ops.append(["texto", campo, c[campo].strip()])
    # Jornada padrão
    jornada = c.get("jornadaDiaria")
    if jornada is not None:
        if not isinstance(jornada, dict) or not jornada:
            r.erro(f"{base}.jornadaDiaria", jornada, "deve ser { seg, ter, qua, qui, sex, sab, dom } em HH:MM", list(DIAS))
        else:
            for dia, valor in jornada.items():
                if dia not in DIAS:
                    r.erro(f"{base}.jornadaDiaria.{dia}", valor, "dia não reconhecido", list(DIAS))
                elif hora(f"jornadaDiaria.{dia}", valor):
                    ops.append(["texto", DIAS[dia], valor.strip()])
    for campo, alvo in (("jornadaSemanal", "qtJornadaSemanal"), ("jornadaMensal", "qtJornadaMensal")):
        if campo in c:
            valor = decimal(campo)
            if valor:
                ops.append(["texto", alvo, valor])
    for campo, alvo in CAIXAS_JORNADA.items():
        if booleano(campo) is not None:
            ops.append(["caixa", alvo, c[campo]])
    # Períodos de descanso
    for campo, alvo in CAIXAS_DESCANSO.items():
        if booleano(campo) is not None:
            ops.append(["caixa", alvo, c[campo]])
    art253 = c.get("art253")
    if art253 is not None:
        if c.get("intervaloInsalubridade") is not True:
            r.erro(f"{base}.art253", art253, "só com intervaloInsalubridade true")
        elif not isinstance(art253, dict) or not set(art253) <= {"trabalho", "descanso"} or not art253:
            r.erro(f"{base}.art253", art253, "deve ser { trabalho, descanso } em HH:MM")
        else:
            for chave, alvo in (("trabalho", "valorTrabalhoArt253"), ("descanso", "valorDescansoArt253")):
                if chave in art253 and hora(f"art253.{chave}", art253[chave]):
                    ops.append(["texto", alvo, art253[chave].strip()])
    inter = c.get("interjornadas")
    if inter is not None:
        if inter is False:
            ops.append(["caixa", "descansoEntreJornadas", False])
        elif inter is True or inter in INTERJORNADAS:
            ops.append(["caixa", "descansoEntreJornadas", True])
            if inter is not True:
                ops.append(["lista", "valorDescansoEntreJornadas", inter])
        else:
            r.erro(f"{base}.interjornadas", inter, "use uma opção da tela (ou true para o padrão 11:00)", list(INTERJORNADAS))
    if "entreSemanas" in c:
        if inter in (None, False):
            r.erro(f"{base}.entreSemanas", c["entreSemanas"], "só com interjornadas")
        elif c["entreSemanas"] not in _entre_semanas(inter):
            # a lista da tela depende do "entre jornadas": ele mesmo ou ele + 24h (11:00 → 35:00 ou 11:00)
            r.erro(f"{base}.entreSemanas", c["entreSemanas"], "use o próprio interjornadas ou interjornadas + 24h",
                   list(_entre_semanas(inter)))
        else:
            ops.append(["lista", "valorDescansoEntreSemanas", c["entreSemanas"]])
    intra = {}
    for campo, caixa, valor_id in (("intrajornada4a6", "intervaloIntraJornadaSupQuatroSeis", "valorIntervaloIntraJornadaSupQuatroSeis"),
                                   ("intrajornadaAcima6", "intervalorIntraJornadaSupSeis", "valorIntervalorIntraJornadaSupSeis")):
        valor = c.get(campo)
        if valor is None:
            continue
        if valor is False:
            ops.append(["caixa", caixa, False])
            continue
        ops.append(["caixa", caixa, True])
        intra[campo] = True
        if valor is not True and hora(campo):
            ops.append(["texto", valor_id, valor.strip()])
    exige("toleranciaIntrajornadaAcima6", "intrajornadaAcima6" in intra, "só com intrajornadaAcima6")
    if "toleranciaIntrajornadaAcima6" in c and "intrajornadaAcima6" in intra and hora("toleranciaIntrajornadaAcima6"):
        ops.append(["texto", "toleranciaIntervaloIntraJornadaSupSeis", c["toleranciaIntrajornadaAcima6"].strip()])
    for campo, alvo in CAIXAS_INTRA.items():
        if campo not in c:
            continue
        if c[campo] is True and campo in ("excessoIntrajornadaSumula118",) and "intrajornadaAcima6" not in intra:
            r.erro(f"{base}.{campo}", True, "só com intrajornadaAcima6 (a tela desabilita sem ele)")
        elif c[campo] is True and campo == "apenasExcessoAlemDaJornada" and c.get("excessoIntrajornadaSumula118") is not True:
            r.erro(f"{base}.{campo}", True, "só com excessoIntrajornadaSumula118 true (a tela desabilita sem ele)")
        elif c[campo] is True and not intra:
            r.erro(f"{base}.{campo}", True, "só com intrajornada4a6 ou intrajornadaAcima6 (a tela desabilita sem eles)")
        elif booleano(campo) is not None:
            ops.append(["caixa", alvo, c[campo]])
    exige("intervaloIntrajornadaMaximo", c.get("excessoIntrajornadaSumula118") is True and "intrajornadaAcima6" in intra,
          "só com intrajornadaAcima6 e excessoIntrajornadaSumula118 true")
    if c.get("excessoIntrajornadaSumula118") is True and "intrajornadaAcima6" in intra and "intervaloIntrajornadaMaximo" in c             and hora("intervaloIntrajornadaMaximo"):
        ops.append(["texto", "valorIntervaloIntrajornadaMaximo", c["intervaloIntrajornadaMaximo"].strip()])
    # Horário noturno
    noturno = c.get("horarioNoturno")
    if noturno is not None:
        if noturno not in HORARIOS_NOTURNOS:
            r.erro(f"{base}.horarioNoturno", noturno, "valor não reconhecido", sorted(HORARIOS_NOTURNOS))
        else:
            ops.append(["radio", "horarioNoturnoApuracaroCartao", HORARIOS_NOTURNOS[noturno]])
    exige("apurarExtrasNoturnas", c.get("apurarExtrasNoturnas") is not True or c.get("apurarHorasNoturnas") is True,
          "só com apurarHorasNoturnas true")
    exige("apurarExtrasNoturnas", c.get("apurarExtrasNoturnas") is not True or forma == "EXCEDENTE_DIARIA",
          "só com formaApuracao EXCEDENTE_DIARIA (a tela desabilita nas outras formas)")
    exige("reducaoFictaNoturna", noturno in (None, "URBANA"), "só com horarioNoturno URBANA (a tela desabilita nos outros)")
    exige("forcarProrrogacao", c.get("forcarProrrogacao") is not True or c.get("prorrogacaoSumula60") is True,
          "só com prorrogacaoSumula60 true")
    for campo, alvo in CAIXAS_NOTURNO.items():
        if booleano(campo) is not None:
            ops.append(["caixa", alvo, c[campo]])
    return None if len(r.erros) > erros_antes else ops


def _cartao_de_ponto(r):
    """Bloco `cartaoDePonto` da raiz: hoje só `criterios`. Sem arquivos.cartao-de-ponto não há tela a preencher."""
    bloco = r.dados.get("cartaoDePonto")
    if bloco is None:
        return
    if not isinstance(bloco, dict):
        r.erro("cartaoDePonto", bloco, "deve ser um objeto { criterios }")
        return
    for campo in bloco:
        if campo != "criterios":
            r.erro(f"cartaoDePonto.{campo}", bloco[campo], "campo não reconhecido", ["criterios"])
    if "criterios" not in bloco:
        return
    ops = interpretar_criterios(r, bloco["criterios"])
    if ops is None:
        return
    if "cartao_ponto_arquivo" not in r.valores:
        r.ignorar("cartaoDePonto.criterios", "sem arquivos.cartao-de-ponto: não há cartão a apurar")
        return
    r.usar("cartaoDePonto.criterios", "cartao_ponto_criterios", json.dumps(ops, ensure_ascii=False))
