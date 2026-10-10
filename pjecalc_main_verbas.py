import pyautogui as pa
from selenium.common import WebDriverException
from Tools.script_get_source_file import GUIAutomationJRS
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


def limparFiles():
    # Zerar arquivos (log.txt e source_plan.txt)
    l = open(os.getcwd() + "\log.txt", "w")
    l.close()
    s = open(os.getcwd() + "\source_plan.txt", "w")
    s.close()


def function_main_vb(driver, value):

    timeControl = 2.5

    if os.path.exists("C:\Windows\System32\FilePathJRS.txt"):

        # Limpar Log
        limparFiles()

        try:
            if value[0] == 1:

                locale_plaverba = value[1]

                # - Verbas
                objVerba = Verbas(locale_plaverba)

                # Verificar a existência do arquivo PJC na pasta do processo/planilha base
                status_operacao = objVerba.checar_arquivo_pjc_diretorio(locale_plaverba)
                if not status_operacao:
                    pa.alert(title="Alerta", text="O arquivo .PJC não foi localizado no mesmo diretório da planilha.")
                    exit()

                # - Registrar Horário Inicial
                objVerba.registrar_horario_inicial()

                # - Inicializar PJeCalc
                # objWeb = WebDriver()
                # driver = objWeb.driver_web()
                objTools = Control()
                # - PJeCalc Inicial
                objInicial = PjecalcPaginaInicial()

                try:
                    driver.get('http://localhost:9257/pjecalc/pages/principal.jsf?conversationId=11')
                    sleep(5)
                    objInicial.clicar_paginaInicial_pjecalc(driver)
                    sleep(2)
                except WebDriverException:
                    # Criar um popup
                    pa.alert(title='Rôberto', text='O PJeCalc não encontra-se em execução. Execute-o e inicialize a automação novamente.')
                    driver.close()
                    exit()

                dados = objVerba.coletar_dados_planilha_verbas(locale_plaverba)
                print("-: ", dados)

                reclamante = dados[0]
                num_processo = dados[1]
                id_processo = dados[2]
                # Formatação
                id_processo = int(id_processo)


                # objInicial.buscar_calculo(driver)
                objInicial.importar_calculo(driver)
                sleep(timeControl)
                # objInicial.buscar_reclamante(driver, reclamante)
                objInicial.anexar_arquivo_pjc(driver, status_operacao[0])
                sleep(timeControl)
                # objInicial.buscar_btn(driver)
                objInicial.confirmar_operacao(driver)
                # objTools.aguardar_processamento()
                objTools.aguardar_carregamento(driver)
                sleep(timeControl)
                # objInicial.abrir_calculo(driver)
                # objTools.aguardar_processamento()
                # sleep(timeControl)

                objVerba.salvar_operacao(driver)
                # objTools.aguardar_processamento()
                objTools.aguardar_carregamento(driver)
                sleep(timeControl)
                objVerba.verificacao(driver)
                sleep(timeControl)

                # PJeCalc Verbas
                objVerba.functionMain(driver)
                sleep(timeControl)
                objTools.limparFilesTemp()

                # - PJeCalc Liquidar
                objLiquidar = Liquidar()
                objLiquidar.acessar_guia_operacoes(driver)
                sleep(timeControl)
                objLiquidar.acessar_liquidar(driver)
                objTools.aguardar_processamento()
                sleep(timeControl)
                objLiquidar.click_liquidar(driver)
                objTools.limparFilesTemp()

                # - PJeCalc Imprimir
                objImprimir = Imprimir(locale_plaverba)
                objImprimir.aguardar_carregamento(driver)
                # objTools.aguardar_processamento()
                sleep(timeControl)

                objImprimir.acessar_guia_imprimir(driver)
                # objTools.aguardar_processamento()
                objTools.aguardar_carregamento(driver)
                sleep(timeControl)
                objImprimir.click_imprimir(driver)
                objImprimir.aguardar_carregamento(driver)
                # objTools.aguardar_processamento()
                # sleep(timeControl)
                objImprimir.mover_relarorio_renomeando(driver, reclamante)
                sleep(timeControl)
                objTools.limparFilesTemp()

                # - PJeCalc Exportar
                objExportar = Exportar(locale_plaverba)
                objExportar.entrar_exportar(driver)
                # objTools.aguardar_processamento()
                objTools.aguardar_carregamento(driver)
                sleep(timeControl)
                objExportar.click_exportar(driver)
                # objTools.aguardar_processamento()
                objTools.aguardar_carregamento(driver)
                sleep(timeControl)
                objExportar.mover_pjc_renomeando(driver, locale_plaverba, num_processo)
                sleep(timeControl)

                # ---------- PJeCalc - Outras Funções ---------- #
                objVerba.registrar_horario_final()
                objVerba.encaminhar_log(id_processo, locale_plaverba)

                # pa.alert(title='Rô-berto', text='Automação Finalizada!')

                # Fechar o PJeCalc
                # driver.close()
                # Limpar arquivos temporários
                objTools.limparFilesTemp()

                # Encerrar
                # exit()
        except IndexError as e:
            print(f"# - Erro [Verbas]: {e}")
            pa.alert(title='Aviso', text=f'{e}')
    else:
        pa.alert(title='Rô-berto', text='Operação não permitida! Entre em contato com o setor de TI.')


if __name__ == '__main__':
    function_main_vb()