from selenium.common.exceptions import WebDriverException
# from browser_pjecalc import WebDriver
# from Tools.script_get_source_file import GetDadosGUI, GUIAutomationJRS
from Calculo.pjecalc_pagina_inicial import PjecalcPaginaInicial
from Calculo.pjecalc_dados_calculo import DadosCalculo
from Calculo.pjecalc_faltas import Faltas
from Calculo.pjecalc_ferias import Ferias
from Calculo.pjecalc_historico_salarial import HistoricoSalarial
from Calculo.pjecalc_verbas import VerbasModel
# from Calculo.verbas import Verbas
from Calculo.pjecalc_fgts import FGTS
from Calculo.pjecalc_contribuicao_social import ContribuicaoSocial
from Calculo.pjecalc_imposto_renda import ImpostoRenda
from Calculo.pjecalc_multas_e_indenizacoes import MultasIndenizacoes
from Calculo.pjecalc_honorarios import Honorarios
from Calculo.pjecalc_custas_judiciais import Custas
from Calculo.pjecalc_correcao_juros_multa import Correcao
from Operacoes.pjecalc_liquidar import Liquidar
from Operacoes.pjecalc_imprimir import Imprimir
from Operacoes.pjecalc_exportar import Exportar
from Tools.pjecalc_control import Control
import pyautogui as pa
from time import sleep
import os
import gc


def limparFiles():
    # Zerar arquivos (log.txt e source_plan.txt)
    l = open(os.getcwd() + "\log.txt", "w")
    l.close()
    s = open(os.getcwd() + "\source_plan.txt", "w")
    s.close()


def function_main(driver, value):

    arquivo_permissao = 'C:\Windows\System32\FilePathJRS.txt'
    objTools = Control()

    if os.path.exists(arquivo_permissao):

        # Limpar Log
        limparFiles()

        try:
            if value[0] == 0:

                locale_plabase = value[1]

                # objeto_geckdriver = WebDriver()
                # driver = objeto_geckdriver.driver_web()

                objeto_home = PjecalcPaginaInicial()

                try:
                    driver.get('http://localhost:9257/pjecalc/pages/principal.jsf?conversationId=11')
                    sleep(5)
                except WebDriverException:
                    pa.alert(title='Rôberto', text='O PJeCalc não encontra-se em execução. Execute-o e inicialize a automação novamente.')
                    driver.close()
                    exit()

                # ---------- PJeCalc - Página Inicial ---------- #
                objeto_home.criar_novo_calculo(driver)
                # ---------- PJeCalc - Dados do Cálculo ---------- #
                objeto_dados = DadosCalculo(locale_plabase)
                objeto_dados.registrar_horario_inicial()
                dados = objeto_dados.main_dados_calculo(driver)
                nome_reclamente = dados[0]
                id_processo = dados[1]
                admissao = dados[2]
                rescisao = dados[3]
                inicio_calculo = dados[4]
                termino_calculo = dados[5]
                numero_processo = dados[6]
                objTools.limparFilesTemp()

                # ---------- PJeCalc - Faltas ---------- #
                objeto_faltas = Faltas(locale_plabase)
                objeto_faltas.main_faltas(driver)
                objTools.limparFilesTemp()

                # # ---------- PJeCalc - Férias ---------- #
                objeto_ferias = Ferias(locale_plabase)
                objeto_ferias.main_ferias(driver)
                objTools.limparFilesTemp()

                # ---------- PJeCalc - Histórico Salarial ---------- #
                objeto_historico = HistoricoSalarial(locale_plabase)
                objeto_historico.main_historico_salarial(driver, admissao, rescisao, inicio_calculo, termino_calculo)
                objTools.limparFilesTemp()

                # ---------- PJeCalc - Verbas ---------- #
                # objeto_verbas = Verbas(locale_plabase)
                # resul = objeto_verbas.functionMain(driver)
                # if resul == 1:
                objeto_verbas_model = VerbasModel()
                objeto_verbas_model.main_verbas(driver)
                objTools.limparFilesTemp()

                # ---------- PJeCalc - FGTS ---------- #
                objeto_fgts = FGTS(locale_plabase)
                objeto_fgts.main_fgts(driver)
                objTools.limparFilesTemp()

                # # ---------- PJeCalc - Contribuição Social ---------- #
                objeto_social = ContribuicaoSocial(locale_plabase)
                objeto_social.main_contribuicao_social(driver, admissao, rescisao, inicio_calculo, termino_calculo)
                objTools.limparFilesTemp()

                # ---------- PJeCalc - Imposto de Renda (só com ir_* do .json) ---------- #
                objeto_ir = ImpostoRenda(locale_plabase)
                objeto_ir.main_imposto_renda(driver)
                objTools.limparFilesTemp()

                try:
                    # ---------- PJeCalc - Multas e Indenizações ---------- #
                    objeto_multas = MultasIndenizacoes(locale_plabase)
                    objeto_multas.main_multas_indenizacoes(driver)
                    objTools.limparFilesTemp()
                except Exception as e:
                    print(f'- (except)[Multas e Indenizações]: {e}')
                    driver.refresh()
                    sleep(5)
                    objTools.limparFilesTemp()
                    objeto_multas = MultasIndenizacoes(locale_plabase)
                    objeto_multas.main_multas_indenizacoes(driver)
                    objTools.limparFilesTemp()

                # ---------- PJeCalc - Honorários ---------- #
                objeto_honorarios = Honorarios(locale_plabase)
                objeto_honorarios.main_honorarios(driver)
                objTools.limparFilesTemp()

                # ---------- PJeCalc - Custas ---------- #
                objeto_custas = Custas(locale_plabase)
                objeto_custas.main_custas(driver)
                objTools.limparFilesTemp()

                # ---------- PJeCalc - Correção ---------- #
                objeto_correcao = Correcao(locale_plabase)
                objeto_correcao.main_correcao(driver)
                objTools.limparFilesTemp()

                # ---------- PJeCalc - Liquidar ---------- #
                objeto_liquidar = Liquidar()
                objeto_liquidar.main_liquidar(driver)
                objTools.limparFilesTemp()

                # ---------- PJeCalc - Imprimir ---------- #
                objeto_imprimir = Imprimir(locale_plabase)
                objeto_imprimir.main_imprimir(driver, nome_reclamente)
                objTools.limparFilesTemp()

                # ---------- PJeCalc - Exportar ---------- #
                objeto_exportar = Exportar(locale_plabase)
                objeto_exportar.main_exportar(driver)

                # ---------- PJeCalc - Outras Funções ---------- #
                objeto_dados.registrar_horario_final()
                objeto_dados.encaminhar_log(id_processo)
                # Fechar arquivo
                # objeto_dados.f.close()
                # Tempo de controle
                # sleep(2)
                # pa.alert(title='Rôberto', text='Automação Finalizada!')
                # Fechar o PJeCalc
                # driver.close()
                # Limpar arquivos temporários
                objTools.limparFilesTemp()

                # Encerrar
                # exit()
        except IndexError as e:
            print(f"# - Erro [Base]: {e}")
            pa.alert(title='Aviso', text=f'{e}')
    else:
        pa.alert(title='Rôberto', text='Operação não permitida! Entre em contato com o setor de TI.')

if __name__ == '__main__':
    function_main()