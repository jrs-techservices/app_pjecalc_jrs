# -*- coding: utf-8 -*-
"""Roda uma execução chamando os fluxos atuais da automação (modos 0, 1 e 2) sem alterá-los."""
import json
import os
import re
from collections import deque
import sqlite3
import sys
import threading
import traceback
from datetime import datetime
from pathlib import Path

import pyautogui

from servico import banco, config
from Tools.pendencias import ler_linha

MODOS = {0: "base", 1: "verbas", 2: "completo"}
EXTENSOES_GERADAS = {".pjc", ".pdf"}


class AlertaDaAutomacao(BaseException):
    """Herda de BaseException para atravessar os `except Exception` dos fluxos e parar a rodada."""


# linhas que não dizem em que passo o robô estava (stacktrace do Selenium, a própria exceção, pontinhos de espera)
_RUIDO = re.compile(r"chrome://|^Stacktrace|^RemoteError|^WebDriverError|^NoSuchElementError|^Message:|\[except\] Erro \[Full\]|"
                    r"\[servico\]|^[.\s]*$")


def explicar_alerta(texto, passos):
    """'Aviso: Message: ' (exceção do Selenium sem texto) não diz nada: completa com o tipo e os últimos passos do log."""
    if not re.search(r"Message:\s*(Stacktrace:|$)", str(texto).strip()):
        return texto
    if "NoSuchElement" in str(texto) or "TimeoutException" in str(texto):
        tipo = "elemento da tela não encontrado (tempo esgotado)"
    elif "StaleElement" in str(texto):
        tipo = "a tela mudou enquanto o robô a usava"
    elif "ElementNotInteractable" in str(texto) or "not reachable" in str(texto):
        tipo = "elemento da tela desabilitado ou escondido"
    else:
        tipo = "erro do navegador sem mensagem"
    contexto = " → ".join(passos) if passos else "sem passos registrados"
    return f"Aviso: {tipo}. Últimos passos: {contexto}"


class _CapturaDeSaida:
    """Copia para o log da execução as linhas impressas pela thread do worker."""

    def __init__(self, original, execucao_id, thread):
        self.original = original
        self._execucao_id = execucao_id
        self._thread = thread
        self._buffer = ""
        self._seq = 0
        self.pendencias = []
        self.ultimos_passos = deque(maxlen=4)  # contexto para alerta com mensagem vazia

    def write(self, texto):
        self.original.write(texto)
        if threading.current_thread() is self._thread:
            self._buffer += texto
            while "\n" in self._buffer:
                linha, self._buffer = self._buffer.split("\n", 1)
                self._registrar(linha)
        return len(texto)

    def flush(self):
        self.original.flush()

    def descarregar(self):
        if self._buffer:
            self._registrar(self._buffer)
            self._buffer = ""

    def _registrar(self, linha):
        linha = linha.strip()
        pendencia = ler_linha(linha) if linha else None
        if pendencia and pendencia not in self.pendencias:
            self.pendencias.append(pendencia)
        if linha and not _RUIDO.search(linha):
            self.ultimos_passos.append(linha.lstrip("-. ").strip()[:160])
        if not linha or self._seq >= config.LIMITE_LOG_POR_EXECUCAO:
            return
        self._seq += 1
        try:
            banco.adicionar_log(self._execucao_id, self._seq, linha)
        except sqlite3.Error as erro:
            self.original.write(f"- [servico] falha ao gravar log: {erro}\n")

    def __getattr__(self, nome):
        return getattr(self.original, nome)


def _classificar(planilha_base, planilha_verbas):
    from Tools.script_get_source_file import GUIAutomationJRS

    planilhas = [p for p in (planilha_base, planilha_verbas) if p]
    return GUIAutomationJRS().verificar_arquivo(planilhas) or None


def _preparar_lancamentos(registro, execucao_id):
    """Relê o .json (pode ter mudado desde o pedido) e devolve a planilha base a usar e a planilha temporária criada, se houver."""
    from Calculo.leitura_planilha import definir_complemento_pje_bd
    from servico import lancamentos

    from servico import verbas_pedido

    interpretacao = lancamentos.interpretar(registro["lancamentos"])
    if interpretacao.verbas_pedido:
        if registro["planilha_verbas"]:
            interpretacao.verbas_pedido = None
            interpretacao.ignorados["verbas"] = "a planilha de verbas do pedido prevalece"
        elif registro["planilha_base"]:
            from Calculo.leitura_planilha import historicos_da_planilha_sap
            verbas_pedido.conferir_historicos(interpretacao, historicos_da_planilha_sap(registro["planilha_base"]))
        else:
            verbas_pedido.conferir_historicos(interpretacao, [nome for nome, _ in interpretacao.historicos])
    if interpretacao.erros:
        campos = "; ".join(f"{e['campo']}={e['valor']!r} ({e['mensagem']})" for e in interpretacao.erros)
        raise ValueError(f"O .json de lançamentos mudou desde o pedido e agora tem valores não aceitos: {campos}")
    resumo = interpretacao.resumo()
    banco.atualizar(execucao_id, lancamentos_resumo=json.dumps(resumo, ensure_ascii=False))
    print(f"- [lançamentos] {registro['lancamentos']}: {len(resumo['usados'])} campo(s) usado(s), {len(resumo['ignorados'])} ignorado(s)")
    for tela, campos in resumo.get("ignorados_por_tela", {}).items():
        print(f"- [lançamentos] ignorados em {tela} ({len(campos)}):")
        for campo, motivo in campos.items():
            print(f"- [lançamentos]     {campo} ({motivo})")
    for aviso in resumo["avisos"]:
        print(f"- [AVISO][lançamentos]: {aviso}")

    if registro["planilha_base"]:
        from Calculo.leitura_planilha import ler_pje_bd

        planilha = ler_pje_bd(registro["planilha_base"])
        existentes = {str(c).strip(): v for c, v in zip(planilha["IDENTIFICADOR"], planilha["INFORMACAO"]) if isinstance(c, str)}
        complemento, forcados, avisos = lancamentos.combinar_com_planilha(interpretacao, existentes)
        for aviso in avisos:
            print(f"- [AVISO][lançamentos]: {aviso}")
        definir_complemento_pje_bd(registro["planilha_base"], complemento, forcados)
        verbas = _planilha_de_verbas(interpretacao, registro, execucao_id)
        for tipo, linhas in (("faltas", interpretacao.faltas), ("férias", interpretacao.ferias),
                             ("histórico salarial", interpretacao.historicos), ("base de INSS", interpretacao.base_inss)):
            if linhas:
                print(f"- [AVISO][lançamentos]: pedido com planilha base: a {tipo} da planilha prevalece; o(s) .csv de {tipo} do .json foi(ram) ignorado(s)")
        return registro["planilha_base"], None, verbas
    temporaria = lancamentos.criar_planilha_do_pedido(registro["lancamentos"], interpretacao.pares(), execucao_id,
                                                      interpretacao.faltas, interpretacao.ferias, interpretacao.historicos,
                                                      interpretacao.base_inss)
    print(f"- [lançamentos] pedido sem planilha base: planilha temporária {temporaria}")
    return temporaria, temporaria, _planilha_de_verbas(interpretacao, registro, execucao_id)


def _planilha_de_verbas(interpretacao, registro, execucao_id):
    """Bloco `verbas` do .json → planilha de verbas temporária (o fluxo completo a lê como a planilha da casa)."""
    if not interpretacao.verbas_pedido:
        return None
    from servico import verbas_pedido

    caminho = verbas_pedido.criar_planilha_de_verbas(registro["lancamentos"], interpretacao.verbas_pedido, execucao_id)
    principais = interpretacao.verbas_pedido["verbas"]
    print(f"- [lançamentos] {len(principais)} verba(s) e {len(interpretacao.verbas_pedido['reflexos'])} reflexo(s) manual(is) "
          f"do .json: planilha de verbas temporária {caminho}")
    for v in principais:
        print(f"- [lançamentos] verba {v['linha']['IIDVERBAJRS']}: {v['descricao']} (Expresso: {v['item']['expresso']})")
    return caminho


def _fluxo(modo):
    if modo == 0:
        import pjecalc_main_base
        return pjecalc_main_base.function_main
    if modo == 1:
        import pjecalc_main_verbas
        return pjecalc_main_verbas.function_main_vb
    import pjecalc_main_full_switch
    return pjecalc_main_full_switch.function_main


def _rodar_fluxo(driver, valor, alertas):
    try:
        _fluxo(valor[0])(driver, valor)
    except AlertaDaAutomacao:
        return banco.STATUS_FALHOU, alertas[0], None
    except SystemExit:
        mensagem = alertas[0] if alertas else "A automação encerrou antes do fim."
        return banco.STATUS_FALHOU, mensagem, None
    except Exception:
        return banco.STATUS_FALHOU, "Erro inesperado na automação.", traceback.format_exc()
    return None, None, None


def _capturar_tela(driver, execucao_id):
    """A página do Firefox da automação, nos dois modos; a tela da máquina só se o navegador já não responde.

    No modo interativo a janela da automação pode estar atrás de outras, e a tela da máquina mostraria o que o usuário tinha aberto.
    """
    destino = config.CAPTURAS_DIR / f"{execucao_id}_{datetime.now():%Y%m%d_%H%M%S}.png"

    def pagina_do_navegador():
        return driver is not None and driver.get_full_page_screenshot_as_file(str(destino))

    def tela_da_maquina():
        pyautogui.screenshot(str(destino))
        return True

    for tentativa in (pagina_do_navegador, tela_da_maquina):
        try:
            if tentativa() and destino.is_file():
                return str(destino)
        except Exception as erro:
            print(f"- [servico] captura ({tentativa.__name__}) falhou: {erro}")
    return None


PREFIXO_FALHOU = "FALHOU"


def _marcar_calculo_falho(driver, execucao_id):
    """Execução que falhou deixa o cálculo pela metade no PJe-Calc: o nome do reclamante ganha "FALHOU <id> - " para
    ninguém usá-lo por engano (fica como evidência; não é excluído). Sem cálculo salvo ainda, não faz nada.
    Devolve o nome novo, ou None."""
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.wait import WebDriverWait
    from Tools.pjecalc_control import Control

    try:
        # cálculo já salvo: o cabeçalho das telas mostra "Cálculo: N"; em Dados do Cálculo, formulario:idCalculo (vazio antes de salvar)
        salvo = driver.execute_script(r"""return /Cálculo:\s*\d+/.test(document.body.innerText) ||
            /^\d+$/.test(((document.getElementById('formulario:idCalculo') || {}).value || '').trim());""")
        if not salvo:
            return None
        espera = WebDriverWait(driver, 10)
        espera.until(EC.element_to_be_clickable((By.CLASS_NAME, "menuImageCalculo"))).click()
        Control().aguardar_carregamento(driver)
        campo = espera.until(EC.presence_of_element_located((By.NAME, "formulario:reclamanteNome")))
        atual = (campo.get_attribute("value") or "").strip()
        if atual.upper().startswith(PREFIXO_FALHOU):
            return atual
        novo = f"{PREFIXO_FALHOU} {execucao_id} - {atual}"[:150]
        campo.clear()
        campo.send_keys(novo)
        espera.until(EC.element_to_be_clickable((By.ID, "formulario:salvar"))).click()
        Control().aguardar_carregamento(driver)
        if "sucesso" not in driver.find_element(By.TAG_NAME, "body").text.lower():
            print("- [servico] o PJe-Calc não confirmou a marca FALHOU no cálculo")
            return None
        return novo
    except Exception as erro:
        print(f"- [servico] não foi possível marcar o cálculo como FALHOU: {str(erro).strip()[:150] or type(erro).__name__}")
        return None


def _fechar(driver):
    if driver is None:
        return
    try:
        driver.quit()
    except Exception:
        pass


def _arquivos_gerados(valor, inicio):
    marco = inicio.timestamp()
    encontrados = []
    for pasta_planilha in {Path(p).parent for p in valor[1:]}:
        for pasta in (pasta_planilha / "03 Automação", pasta_planilha):
            if not pasta.is_dir():
                continue
            for arquivo in pasta.iterdir():
                if (arquivo.is_file() and arquivo.suffix.lower() in EXTENSOES_GERADAS
                        and arquivo.stat().st_mtime >= marco):
                    encontrados.append(str(arquivo))
    return sorted(set(encontrados))


def executar(execucao_id):
    registro = banco.obter(execucao_id)
    inicio = datetime.now()
    banco.atualizar(execucao_id, status=banco.STATUS_EXECUTANDO, iniciado_em=inicio.isoformat(timespec="seconds"))

    alertas = []

    def interceptar_alerta(text="", title="", button="OK", **_):
        alertas.append(explicar_alerta(f"{title}: {text}" if title else str(text), list(saida.ultimos_passos)))
        print(f"- [servico] alerta da automação: {alertas[-1]}")
        raise AlertaDaAutomacao()

    from browser_pjecalc import WebDriver
    from Calculo.leitura_planilha import limpar_cache, limpar_complementos

    limpar_cache()
    limpar_complementos()
    temporaria = None
    verbas_temporaria = None
    navegador = registro["navegador"]
    saida = _CapturaDeSaida(sys.stdout, execucao_id, threading.current_thread())
    alerta_original = pyautogui.alert
    sys.stdout = saida
    pyautogui.alert = interceptar_alerta
    status, mensagem, erro, valor, driver, captura = banco.STATUS_FALHOU, None, None, None, None, None
    try:
        try:
            planilha_base = registro["planilha_base"]
            planilha_verbas = registro["planilha_verbas"]
            if registro.get("lancamentos"):
                planilha_base, temporaria, verbas_temporaria = _preparar_lancamentos(registro, execucao_id)
                planilha_verbas = planilha_verbas or verbas_temporaria
            valor = _classificar(planilha_base, planilha_verbas)
            if valor is None:
                mensagem = "Planilha inválida: a base precisa da aba CAD ou PJE-BD e a de verbas da aba TBCALCULO."
            else:
                banco.atualizar(execucao_id, modo=MODOS[valor[0]])
                driver = WebDriver().driver_web(oculto=navegador != banco.NAVEGADOR_INTERATIVO)
                if driver is None:
                    mensagem = "Não foi possível abrir o Firefox da automação."
                else:
                    status, mensagem, erro = _rodar_fluxo(driver, valor, alertas)
        except AlertaDaAutomacao:
            mensagem = alertas[0]
        except ValueError as problema:
            mensagem, erro = str(problema), traceback.format_exc()
        except Exception:
            mensagem, erro = "Erro ao preparar a execução.", traceback.format_exc()

        arquivos = _arquivos_gerados(valor, inicio) if valor else []
        tem_pjc = any(a.lower().endswith(".pjc") for a in arquivos)
        tem_pdf = any(a.lower().endswith(".pdf") for a in arquivos)
        if status is None and tem_pjc and not tem_pdf:
            # sem o relatório o cálculo não está pronto para uso: não é "concluído"
            status, mensagem = banco.STATUS_FALHOU, "O .PJC foi exportado, mas o relatório em PDF não foi gerado."
        if status is None:
            if tem_pjc:
                status, mensagem = banco.STATUS_CONCLUIDO, "Cálculo concluído."
                if temporaria:
                    from Calculo.leitura_planilha import csvs_de_historico

                    faltam = [nome for nome, falta in (("histórico salarial", not csvs_de_historico(temporaria)),
                                                       ("verbas", not verbas_temporaria)) if falta]
                    mensagem = ("Cálculo concluído só com o .json" +
                                (f": sem {' e '.join(faltam)} (não vieram no .json)" if faltam else "") +
                                ". Confira antes de usar.")
            else:
                status, mensagem = banco.STATUS_FALHOU, "O fluxo terminou sem exportar o .PJC."
        if status == banco.STATUS_FALHOU and driver is not None:
            captura = _capturar_tela(driver, execucao_id)
            print(f"- [servico] captura da falha: {captura or 'não foi possível capturar'}")
            marcado = _marcar_calculo_falho(driver, execucao_id)
            if marcado:
                print(f"- [servico] cálculo marcado no PJe-Calc: {marcado}")
                mensagem = f"{mensagem or 'A execução falhou.'} O cálculo incompleto ficou no PJe-Calc como '{marcado}'."
    finally:
        _fechar(driver)
        limpar_complementos()
        for arquivo in (temporaria, verbas_temporaria):
            if arquivo and os.path.exists(arquivo):
                os.remove(arquivo)
        pyautogui.alert = alerta_original
        saida.descarregar()
        sys.stdout = saida.original

    banco.atualizar(
        execucao_id, status=status, mensagem=mensagem, erro=erro,
        arquivos=arquivos, captura=captura, concluido_em=banco.agora(), pendencias=saida.pendencias,
    )
    print(f"- [servico] execução {execucao_id}: {status} - {mensagem}")
