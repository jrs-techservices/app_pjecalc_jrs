from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait, TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime, date, timedelta
from calendar import monthrange
import time
import os
#
from Tools.pjecalc_control import Control
from Tools.pendencias import interromper
from Calculo.pjecalc_menu import PjecalcMenu


# código do .json (cj_indices_acumulados) → opção da tela Liquidar
OPCOES_INDICES_ACUMULADOS = {"MES_SUBSEQUENTE_AO_VENCIMENTO": 0, "MES_DO_VENCIMENTO": 1, "MES_SUBSEQUENTE_E_MES_DO_VENCIMENTO": 2}


class Liquidar:

    delay = 10

    def __init__(self, source=None):
        self.source = source

    def verificacao(self, driver):

        def gerar_relatorio(campo, status):
            file_txt_log = open(os.getcwd() + '\log.txt', "a")
            # file_txt_log.write('* ' + campo + ' | ' + status + '\n')
            file_txt_log.write(f'- {campo} | {status}\n')
            return file_txt_log.close()

        delay = 10
        try:
            mensagem = WebDriverWait(driver, delay).until(
                EC.presence_of_element_located((By.ID, 'formulario:painelMensagens:j_id69')))
            msg = mensagem.text
            if 'Operação realizada com sucesso.' in msg:
                print('* Operação realizada com sucesso.')
                gerar_relatorio('Liquidar', 'Ok')
            else:
                print('* ERRO!', msg)
                gerar_relatorio('Liquidar', '---------- Erro! ----------')
                # Sem liquidar não há relatório: no serviço a execução termina como `falhou`, com a mensagem do PJe-Calc.
                interromper('Liquidar', msg)
                # exit() -> Antes
                pass
        except TimeoutException:
            print(
                '* Exceção - Verificação -  A Página demorou para responder ou o elemento não foi encontrado. Encerrando...')
            exit()

        # Tempo de controle
        time.sleep(2)

    def acessar_guia_operacoes(self, driver):
        WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'li.header:nth-child(3)'))).click()

    def acessar_liquidar(self, driver):
        WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.CLASS_NAME, "menuImageLiquidar"))).click()

    def acumular_indice(self, driver):
        """Índices acumulados: o do .json (cj_indices_acumulados) ou, sem ele, a opção de sempre (mensais no mês
        subsequente, anuais e rescisórias no mês do vencimento)."""
        opcao = 2
        if self.source:
            from Calculo.leitura_planilha import ler_pje_bd
            planilha = ler_pje_bd(self.source)
            pedido = [v for k, v in zip(planilha['IDENTIFICADOR'], planilha['INFORMACAO'])
                      if isinstance(k, str) and k.strip() == 'cj_indices_acumulados']
            if pedido and str(pedido[0]).strip() in OPCOES_INDICES_ACUMULADOS:
                opcao = OPCOES_INDICES_ACUMULADOS[str(pedido[0]).strip()]
        print(f"- [Liquidar] índices acumulados: opção {opcao}")
        WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, f"formulario:indicesAcumulados:{opcao}"))).click()

    def preencher_data(self, driver):

        def gerar_data_liquidacao():
            # - DATA ATUAL
            data_hoje = date.today()

            # - DIA ATUAL
            dia_verificacao = data_hoje.day

            # - CALCULAR DOIS MESES ANTES AO MÊS ATUAL
            dt_dois_meses_antes = date(data_hoje.year, data_hoje.month, data_hoje.day) - timedelta(days=60)
            # print(" # ", dt_dois_meses_antes)

            if dia_verificacao >= 16:
                dt_dois_meses_antes = dt_dois_meses_antes + timedelta(days=30)
                # print(" ## ", dt_dois_meses_antes)
                # mes += 1

            # - MÊS ATUAL
            mes = dt_dois_meses_antes.month

            # - ANO ATUAL
            ano = dt_dois_meses_antes.year

            # Função retorna uma tubla com a semana e último dia do mês
            ultimo_dia_mes = monthrange(ano, mes)

            # - ÚLTIMO DIA
            dia = ultimo_dia_mes[1]

            # - DATA LIQUIDAÇÃO
            data_liquidacao = datetime(ano, mes, dia).strftime("%d/%m/%Y")
            print(F"- DATA ATUAL: {data_hoje.strftime('%d/%m/%Y')} | - DATA HÁ DOIS MESES: {data_liquidacao}")

            return data_liquidacao

        data = gerar_data_liquidacao()

        campo_data = WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.NAME, 'formulario:dataDeLiquidacaoInputDate')))
        campo_data.send_keys(data)

    def click_liquidar(self, driver):
        WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.ID, 'formulario:liquidar'))).click()

    def main_liquidar(self, driver):

        objeto_liquidar = self
        objTools = Control()
        objeto_menu = PjecalcMenu()

        # objeto_liquidar.acessar_guia_operacoes(driver)
        objeto_menu.acessar_operacoes(driver)

        # Tempo de controle
        time.sleep(2)

        objeto_liquidar.acessar_liquidar(driver)

        objTools.aguardar_carregamento(driver)

        # Tempo de controle
        time.sleep(1)

        objeto_liquidar.preencher_data(driver)

        # Tempo de controle
        time.sleep(1)

        objeto_liquidar.acumular_indice(driver)

        # Tempo de controle
        time.sleep(1)

        objeto_liquidar.click_liquidar(driver)

        # objTools.aguardar_carregamento(driver)
        objTools.aguardar_carregamento(driver)

        # Tempo de controle
        time.sleep(1)

        objeto_liquidar.verificacao(driver)

        # Tempo de controle
        time.sleep(1)

        print('-- Fim - (Liquidar) --')