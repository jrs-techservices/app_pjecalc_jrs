import os
from time import sleep
import pyautogui as pa
from browser_pjecalc import WebDriver
from Tools.pjecalc_control import Control
from Calculo.pjecalc_menu import PjecalcMenu
from selenium.common.exceptions import WebDriverException
from Calculo.pjecalc_pagina_inicial import PjecalcPaginaInicial
from Calculo.pjecalc_dados_calculo import DadosCalculo
from Calculo.pjecalc_faltas import Faltas
from Calculo.pjecalc_ferias import Ferias
from Calculo.pjecalc_historico_salarial import HistoricoSalarial
from Calculo.pjecalc_cartao_ponto import CartaoPonto
from Calculo.pjecalc_verbas import VerbasModel
from Calculo.verbas import Verbas
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



def limparFiles():
    # Zerar arquivos (log.txt e source_plan.txt)
    l = open(fr"{os.getcwd()}\log.txt", "w")
    s = open(fr"{os.getcwd()}\source_plan.txt", "w")
    l.close()
    s.close()


first_iteration = True


def function_main(driver, value):

    arquivo_permissao = r'C:\Windows\System32\FilePathJRS.txt'
    objTools = Control()

    global first_iteration

    if os.path.exists(arquivo_permissao):

        # Limpar Log
        limparFiles()
        try:
            if value[0] == 2:

                locale_plabase = value[1]
                locale_plaverba = value[2]

                objeto_home = PjecalcPaginaInicial()

                try:
                    driver.get('http://localhost:9257/pjecalc/pages/principal.jsf')  # sem conversationId fixo: o PJe-Calc abre uma conversa nova
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

                # ---------- PJeCalc - Cartão de Ponto (só com arquivos.cartao-de-ponto do .json) ---------- #
                # antes das Verbas: as de divisor/quantidade importada do cartão leem a apuração
                CartaoPonto(locale_plabase).main_cartao_ponto(driver)
                objTools.limparFilesTemp()


                # Padrão (desde 17/10/2026, A/B no 17480 com 11 de 11 itens do .PJC iguais): as verbas reais entram aqui e há
                # uma liquidação só; a verba-modelo (que só existe porque o PJe-Calc não liquida sem verba) é criada apenas se a
                # planilha de verbas vier sem registros. FLUXO_LIQUIDACAO_UNICA=0 volta ao fluxo antigo (modelo → 1ª liquidação
                # → verbas reais → exclui a modelo → 2ª liquidação).
                liquidacao_unica = os.environ.get("FLUXO_LIQUIDACAO_UNICA", "1") != "0"
                objMenu = PjecalcMenu()  # criado aqui: a limpeza do fim (del objMenu) roda nos dois fluxos
                objeto_verbas_model = VerbasModel()
                if liquidacao_unica:
                    print("- [fluxo] liquidação única: verbas reais logo depois do Histórico Salarial")
                    objeto_verbas = Verbas(locale_plaverba)
                    resul = objeto_verbas.functionMain(driver)
                    objTools.limparFilesTemp()
                    if resul == 1:
                        objeto_verbas_model.main_verbas(driver)
                        objTools.limparFilesTemp()
                else:
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

                # ---------- PJeCalc - Multas e Indenizações ---------- #
                # a própria tela exclui o que salvou e repete uma vez; repetir aqui duplicava as multas
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

                if not liquidacao_unica:
                    # ---------- PJeCalc - Liquidar (1ª, com a verba-modelo) ---------- #
                    objeto_liquidar = Liquidar(locale_plabase)
                    objeto_liquidar.main_liquidar(driver)
                    objTools.limparFilesTemp()

                    # ---------- PJeCalc - Menu ---------- #
                    objMenu.acessar_calculo(driver)

                    # ---------- PJeCalc - Verbas ---------- #
                    objeto_verbas = Verbas(locale_plaverba)
                    resul = objeto_verbas.functionMain(driver)
                    objTools.limparFilesTemp()

                    # Com verbas reais no cálculo, a verba-modelo (necessária só para a 1ª liquidação) sai antes da liquidação final.
                    if resul != 1:
                        objeto_verbas_model.excluir_verba_modelo(driver)
                        objTools.limparFilesTemp()

                # resul = objeto_verbas.functionMain(driver)
                # if resul == 1:
                #     objeto_verbas_model = VerbasModel()
                #     objeto_verbas_model.main_verbas(driver)

                # ---------- PJeCalc - Menu ---------- #
                # objMenu.acessar_operacoes(driver)

                # ---------- PJeCalc - Liquidar ---------- #
                objeto_liquidar = Liquidar(locale_plabase)
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
                # pa.alert(title='Rôberto', text='Automação Finalizada!')
                # Fechar o PJeCalc
                # driver.close()
                # Limpar arquivos temporários
                objTools.limparFilesTemp()

                # [CLEAR]
                del value
                del locale_plabase
                del locale_plaverba
                del objTools
                del objeto_home
                del objeto_dados
                del dados
                del nome_reclamente
                del id_processo
                del admissao
                del rescisao
                del inicio_calculo
                del termino_calculo
                del numero_processo
                del objeto_faltas
                del objeto_ferias
                del objeto_historico
                del objeto_verbas_model
                del objeto_fgts
                del objeto_social
                del objeto_multas
                del objeto_honorarios
                del objeto_correcao
                del objeto_liquidar
                del objMenu
                del objeto_verbas
                del objeto_imprimir
                del objeto_exportar

        except Exception as e:
            print(f"- [except] Erro [Full]: {e}")
            pa.alert(title='Aviso', text=f'{e}')

    else:
        pa.alert(title='Rôberto', text='Operação não permitida! Entre em contato com o setor de TI.')


if __name__ == '__main__':

    planilhas = [2, r'C:\Users\lucas.fonseca\Downloads\Automação PJeCalc - Testes\10480_0000447-66.2022.5.06.0020 PJe\10480 - Planilha Base v3.37.4.xlsb', r'C:\Users\lucas.fonseca\Downloads\Automação PJeCalc - Testes\10480_0000447-66.2022.5.06.0020 PJe\10480 - Verbas v1.10.1.xlsm']

    objDriver = WebDriver()
    driver = objDriver.driver_web()

    function_main(driver, planilhas)

    planilhas2 = [2, r'C:\Users\lucas.fonseca\Downloads\Automação PJeCalc - Testes\10470_0001218-29.2023.5.06.0143 PJe\10470 - Planilha Base v3.37.4.xlsb', r'C:\Users\lucas.fonseca\Downloads\Automação PJeCalc - Testes\10470_0001218-29.2023.5.06.0143 PJe\10470 - Verbas v1.10.1.xlsm']

    function_main(driver, planilhas2)


    planilhas3 = [2, r'C:\Users\lucas.fonseca\Downloads\Automação PJeCalc - Testes\10464_0001161-58.2023.5.13.0032 PJe\10464 - Planilha Base v3.37.4.xlsb', r'C:\Users\lucas.fonseca\Downloads\Automação PJeCalc - Testes\10464_0001161-58.2023.5.13.0032 PJe\10464 - Verbas v1.10.1.xlsm']

    function_main(driver, planilhas3)