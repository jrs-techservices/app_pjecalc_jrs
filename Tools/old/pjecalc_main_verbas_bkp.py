import pyautogui as pa
from selenium.common import WebDriverException
from Tools.script_get_source_file import GetDadosGUI
from browser_pjecalc import WebDriver
from Tools.pjecalc_control import Control
from Calculo.pjecalc_pagina_inicial import PjecalcPaginaInicial
from Calculo.verbas import Verbas
from Operacoes.pjecalc_liquidar import Liquidar
from Operacoes.pjecalc_imprimir import Imprimir
from Operacoes.pjecalc_exportar import Exportar
from time import sleep
import os
import gc


def function_main_vb():

    timeControl = 2.5

    if os.path.exists("C:\Windows\System32\FilePathJRS.txt"):

        # - Interface Gráfica
        objGUI = GetDadosGUI()
        objGUI.source_file()
        # - Inicializar PJeCalc
        objWeb = WebDriver()
        driver = objWeb.driver_web()
        # - Tools
        objTools = Control()
        source = objGUI.source_file
        # - Verbas
        objVerba = Verbas(source)

        try:
            driver.get('http://localhost:9257/pjecalc/pages/principal.jsf?conversationId=11')
            sleep(6)
        except WebDriverException:
            # Criar um popup
            pa.alert(title='Rôberto', text='O PJeCalc não encontra-se em execução. Execute-o e inicialize a automação novamente.')
            driver.close()
            exit()

        dados = objVerba.coletar_dados_planilha_verbas(objGUI.source_file)
        print("-: ", dados)

        reclamante = dados[0]
        num_processo = dados[1]

        # - PJeCalc Inicial
        objInicial = PjecalcPaginaInicial()
        objInicial.buscar_calculo(driver)
        sleep(timeControl)
        objInicial.buscar_reclamante(driver, reclamante)
        sleep(timeControl)
        objInicial.buscar_btn(driver)
        objTools.aguardar_processamento()
        sleep(timeControl)
        objInicial.abrir_calculo(driver)
        objTools.aguardar_processamento()
        sleep(timeControl)

        objVerba.salvar_operacao(driver)
        objTools.aguardar_processamento()
        sleep(timeControl)
        objVerba.verificacao(driver)
        sleep(timeControl)

        # PJeCalc Verbas
        objVerba.functionMain(driver)
        sleep(timeControl)

        # - PJeCalc Liquidar
        objLiquidar = Liquidar()
        objLiquidar.acessar_guia_operacoes(driver)
        sleep(timeControl)
        objLiquidar.acessar_liquidar(driver)
        objTools.aguardar_processamento()
        sleep(timeControl)
        objLiquidar.click_liquidar(driver)
        objTools.aguardar_processamento()
        sleep(timeControl)

        # - PJeCalc Imprimir
        objImprimir = Imprimir(objGUI.source_file)
        objImprimir.acessar_guia_imprimir(driver)
        objTools.aguardar_processamento()
        sleep(timeControl)
        objImprimir.click_imprimir(driver)
        objTools.aguardar_processamento()
        sleep(timeControl)
        objImprimir.mover_relarorio_renomeando(reclamante, source, num_processo)
        sleep(timeControl)

        # - PJeCalc Exportar
        objExportar = Exportar(objGUI.source_file)
        objExportar.entrar_exportar(driver)
        objTools.aguardar_processamento()
        sleep(timeControl)
        objExportar.click_exportar(driver)
        objTools.aguardar_processamento()
        sleep(timeControl)
        objExportar.mover_pjc_renomeando(reclamante, source, num_processo)
        sleep(timeControl)

        pa.alert(title='Rô-berto', text='Automação Finalizada!')

        # Fechar o PJeCalc
        driver.close()

        # Limpar arquivos temporários
        objTools.limparFilesTemp()
        gc.collect()
        gc.collect(generation=1)
        gc.collect(generation=2)

    else:
        pa.alert(title='Rô-berto', text='Operação não permitida! Entre em contato com o setor de TI.')


if __name__ == '__main__':
    function_main_vb()