from Tools.pendencias import de_relatorio, interromper
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.wait import WebDriverWait, TimeoutException
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time
import xlrd
import os
import gc
from Tools.pjecalc_control import Control
from Calculo.leitura_planilha import ler_pje_bd


class MultasIndenizacoes:


    def __init__(self, source):
        self.source = source
        self.planilha_base = ler_pje_bd(source)
        self.delay = 10
        self.delayG = 1.5
        self.objTools = Control()
        self.qtd_multas_indenizacoes = 0

    # ATRIBUTOS

    var_controle_float = 0.0
    var_controle_int = 0
    var_controle_string = ""

    # MULTA E INDENIZAÇÕES 1
    multas_indenizacoes_qtd = ''
    multas_indenizacoes_descricao_1 = ''
    multas_indenizacoes_credor_1 = ''
    multas_indenizacoes_terceiro_1 = ''
    multas_indenizacoes_form_pagto_1 = ""
    multas_indenizacoes_tipo_1 = ''
    multas_indenizacoes_vcto_1 = ''
    multas_indenizacoes_valor_1 = ''
    multas_indenizacoes_base_pje_calc_1 = ''
    multas_indenizacoes_aliquota_1 = ''
    multas_indenizacoes_aplicar_juros_1 = ''
    multas_indenizacoes_a_partir_de_1 = ""


    def verificacao(self, driver):

        delay = 6

        def gerar_relatorio(campo, status):
            file_txt_log = open(os.getcwd() + '\log.txt', "a")
            # file_txt_log.write('- ' + campo + ' | ' + status + '\n')
            file_txt_log.write(f'- {campo} : {self.multas_indenizacoes_descricao_1.title()} | {status}\n')
            return file_txt_log.close()

        def cancelar_operacao():
            btn_cancelar = WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, 'formulario:cancelar')))
            btn_cancelar.click()
            self.objTools.aguardar_carregamento(driver)

        try:
            mensagem = WebDriverWait(driver, delay).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "table[id^='formulario:painelMensagens:']")))
            msg = mensagem.text
            if 'Operação realizada com sucesso.' in msg:
                # print('* Operação realizada com sucesso.')
                gerar_relatorio('Multas e Indenizações', 'Ok')
            else:
                # print('* ERRO!', msg)
                gerar_relatorio('Multas e Indenizações', '---------- Erro! ----------')
                de_relatorio('Multas e Indenizações')
                cancelar_operacao()

        except TimeoutException:
            print('- [Except][Multas/Indenizações] - Elemento não encontrado/A Página demorou para responder. Encerrando...')

        # Tempo de controle
        time.sleep(2)

    def acessar_multas_indenizacoes(self, driver):
        WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.CLASS_NAME, "menuImageMulta"))).click()

    def selecionar_novo(self, driver):
        WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, 'formulario:incluir'))).click()

    def verificar_qtdMultasIndenizacoes(self):

        for i in range(len(self.planilha_base)):

            coluna_identificador = self.planilha_base.loc[i, 'IDENTIFICADOR']
            coluna_informacao = self.planilha_base.loc[i, 'INFORMACAO']

            # - Pular linhas em branco
            if type(coluna_identificador) == float:
                continue
            elif coluna_identificador == "multas_indenizacoes_qtd":
                self.qtd_multas_indenizacoes = coluna_informacao
                print(f"- QTD MULTAS E INDENIZAÇÕES: {self.qtd_multas_indenizacoes} - TIPO: {type(self.qtd_multas_indenizacoes)}")
                return self.qtd_multas_indenizacoes
            else:
                continue

    def preencher_dados_multas_indenizacoes(self, driver):

        indice = 1

        for i in range(len(self.planilha_base)):

            coluna_identificador = self.planilha_base.loc[i, 'IDENTIFICADOR']
            coluna_informacao = self.planilha_base.loc[i, 'INFORMACAO']

            # Condição para pular as linhas em branco da coluna Identificador na planilha base
            if type(coluna_identificador) == type(self.var_controle_float):
                continue
            elif coluna_identificador == "multas_indenizacoes_qtd":
                multas_indenizacoes_qtd = coluna_informacao
                print("\n- Qtd - Multas e Indenizações: ", multas_indenizacoes_qtd)
                if multas_indenizacoes_qtd == 0:
                    print("- Multas e Indenizações: * Sem ocorrências")
                    break
            # Descrição
            elif f'multas_indenizacoes_descricao_{indice}' in coluna_identificador:
                self.multas_indenizacoes_descricao_1 = coluna_informacao
                print('- Descrição: ', self.multas_indenizacoes_descricao_1)

            # Credor/Devedor
            elif f'multas_indenizacoes_credor_{indice}' in coluna_identificador:
                self.multas_indenizacoes_credor_1 = coluna_informacao
                print('- Credor: ', self.multas_indenizacoes_credor_1)

            # Forma de Pagamento
            elif f"multas_indenizacoes_form_pagto_{indice}" in coluna_identificador:
                self.multas_indenizacoes_form_pagto_1 = coluna_informacao
                print("- Forma de Pagamento: ", self.multas_indenizacoes_form_pagto_1)

            elif f'multas_indenizacoes_terceiro_{indice}' in coluna_identificador:
                self.multas_indenizacoes_terceiro_1 = coluna_informacao
                print('- Terceiro: ', self.multas_indenizacoes_terceiro_1)

            # Tipo (Informado/Calculado)
            elif f'multas_indenizacoes_tipo_{indice}' in coluna_identificador:
                self.multas_indenizacoes_tipo_1 = coluna_informacao
                self.multas_indenizacoes_tipo_1 = self.multas_indenizacoes_tipo_1.title()
                print('- Tipo: ', self.multas_indenizacoes_tipo_1)

            # Data de Vencimento _ Se Tipo -> Informado
            elif f'multas_indenizacoes_vcto_{indice}' in coluna_identificador:
                self.multas_indenizacoes_vcto_1 = coluna_informacao

                if type(self.multas_indenizacoes_vcto_1) == type(self.var_controle_int):
                    self.multas_indenizacoes_vcto_1 = xlrd.xldate_as_datetime(self.multas_indenizacoes_vcto_1, 0)
                    self.multas_indenizacoes_vcto_1 = self.multas_indenizacoes_vcto_1.strftime('%d/%m/%Y')
                    print("- Vencimento: ", self.multas_indenizacoes_vcto_1)

            # Valor _ Se Tipo -> Informado
            elif f'multas_indenizacoes_valor_{indice}' in coluna_identificador:
                self.multas_indenizacoes_valor_1 = coluna_informacao

                if type(self.multas_indenizacoes_valor_1) != type(self.var_controle_string):
                    self.multas_indenizacoes_valor_1 = float(self.multas_indenizacoes_valor_1)
                    self.multas_indenizacoes_valor_1 = '{:.2f}'.format(self.multas_indenizacoes_valor_1)
                    print('- Valor: ', self.multas_indenizacoes_valor_1)

            # Base
            elif f'multas_indenizacoes_base_pje-calc_{indice}' in coluna_identificador:
                self.multas_indenizacoes_base_pje_calc_1 = coluna_informacao
                # self.multas_indenizacoes_base_pje_calc_1 = self.multas_indenizacoes_base_pje_calc_1.title()
                print('- Base: ', self.multas_indenizacoes_base_pje_calc_1)

            # Alíquota (%)
            elif f'multas_indenizacoes_aliquota_{indice}' in coluna_identificador:
                self.multas_indenizacoes_aliquota_1 = coluna_informacao

                if type(self.multas_indenizacoes_aliquota_1) == type(self.var_controle_float):
                    self.multas_indenizacoes_aliquota_1 = '{:.2%}'.format(self.multas_indenizacoes_aliquota_1)

                print('- Alíquota: ', self.multas_indenizacoes_aliquota_1)

            # Aplicar Juros _ Se Tipo -> Informado
            elif f'multas_indenizacoes_aplicar_juros_{indice}' in coluna_identificador:
                self.multas_indenizacoes_aplicar_juros_1 = coluna_informacao
                print('- Aplicar Juros: ', self.multas_indenizacoes_aplicar_juros_1)

            # Aplicar Juros - A partir de
            elif f'multas_indenizacoes_a_partir_de_{indice}' in coluna_identificador:
                self.multas_indenizacoes_a_partir_de_1 = coluna_informacao
                print('- Aplicar Juros a partir de: ', self.multas_indenizacoes_a_partir_de_1)

                for k in range(len(self.planilha_base)):

                    if '-' in self.multas_indenizacoes_credor_1:
                        break
                    else:
                        # Novo
                        self.selecionar_novo(driver)
                        self.objTools.aguardar_carregamento(driver)
                        # Tempo de controle
                        time.sleep(2)
                        if 'Calculado' in self.multas_indenizacoes_tipo_1:

                            # Descrição
                            campo_descricao = WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.NAME, 'formulario:descricao')))
                            campo_descricao.send_keys(self.multas_indenizacoes_descricao_1)

                            # Tempo de Controle
                            time.sleep(1)

                            # Credor/Devedor
                            selecionar_credor = WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.NAME, 'formulario:credorDevedor')))
                            selecionar = Select(selecionar_credor)
                            selecionar.select_by_visible_text(self.multas_indenizacoes_credor_1)

                            # Tempo de controle
                            time.sleep(1)

                            # Condição para adicionar o Terceiro
                            if self.multas_indenizacoes_credor_1 == "Terceiro e Reclamante":

                                # Forma de Pagamento
                                if self.multas_indenizacoes_form_pagto_1 == "DESCONTAR":
                                    WebDriverWait(driver, self.delay).until(EC.visibility_of_element_located((By.ID, "formulario:tipoCobrancaReclamante:0"))).click()

                                elif self.multas_indenizacoes_form_pagto_1 == "COBRAR":
                                    WebDriverWait(driver, self.delay).until(EC.visibility_of_element_located((By.ID, "formulario:tipoCobrancaReclamante:1"))).click()
                                # Tempo de controle
                                time.sleep(1)

                                # Forma antiga
                                # campo_terceiro = WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.NAME, 'formulario:terceiro')))
                                # campo_terceiro.send_keys(self.multas_indenizacoes_terceiro_1)
                                # Nova Forma
                                WebDriverWait(driver, self.delay).until(EC.visibility_of_element_located((By.NAME, "formulario:terceiro"))).send_keys(self.multas_indenizacoes_terceiro_1)

                            elif self.multas_indenizacoes_credor_1 == "Terceiro e Reclamado":
                                WebDriverWait(driver, self.delay).until(EC.visibility_of_element_located((By.NAME, "formulario:terceiro"))).send_keys(self.multas_indenizacoes_terceiro_1)


                            # Tempo de Controle
                            time.sleep(1)

                            # Tipo - (Calculado)
                            selecionar_calculado = WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, 'formulario:valor:1')))
                            selecionar_calculado.click()

                            # Tempo de controle
                            time.sleep(1)

                            # Base
                            selecionar_base = WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.NAME, 'formulario:tipoBaseMulta')))
                            base = Select(selecionar_base)
                            base.select_by_visible_text(self.multas_indenizacoes_base_pje_calc_1)

                            # Tempo de controle
                            time.sleep(1)

                            # Preencher Alíquota (%)
                            preencher_aliquota = WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.NAME, 'formulario:aliquota')))
                            preencher_aliquota.send_keys(self.multas_indenizacoes_aliquota_1)

                            # Tempo de controle
                            time.sleep(1)

                            self.salvar(driver)
                            self.objTools.aguardar_carregamento(driver)

                            # Tempo de controle
                            time.sleep(2)

                            self.verificacao(driver)

                            break

                        elif 'Informado' in self.multas_indenizacoes_tipo_1:

                            # Descrição
                            campo_descricao = WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.NAME, 'formulario:descricao')))
                            campo_descricao.send_keys(self.multas_indenizacoes_descricao_1)

                            # Tempo de Controle
                            time.sleep(1)

                            # Credor/Devedor
                            selecionar_credor = WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.NAME, 'formulario:credorDevedor')))
                            selecionar = Select(selecionar_credor)
                            selecionar.select_by_visible_text(self.multas_indenizacoes_credor_1)

                            # Tempo de controle
                            time.sleep(1)

                            # Condição para adicionar o Terceiro
                            if self.multas_indenizacoes_credor_1 == "Terceiro e Reclamante":

                                # Forma de Pagamento
                                if self.multas_indenizacoes_form_pagto_1 == "DESCONTAR":
                                    WebDriverWait(driver, self.delay).until(EC.visibility_of_element_located((By.ID, "formulario:tipoCobrancaReclamante:0"))).click()

                                elif self.multas_indenizacoes_form_pagto_1 == "COBRAR":
                                    WebDriverWait(driver, self.delay).until(EC.visibility_of_element_located((By.ID, "formulario:tipoCobrancaReclamante:1"))).click()
                                # Tempo de controle
                                time.sleep(1)

                                # Forma antiga
                                # campo_terceiro = WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.NAME, 'formulario:terceiro')))
                                # campo_terceiro.send_keys(self.multas_indenizacoes_terceiro_1)
                                # Nova Forma
                                WebDriverWait(driver, self.delay).until(EC.visibility_of_element_located((By.NAME, "formulario:terceiro"))).send_keys(self.multas_indenizacoes_terceiro_1)

                            elif self.multas_indenizacoes_credor_1 == "Terceiro e Reclamado":
                                WebDriverWait(driver, self.delay).until(EC.visibility_of_element_located((By.NAME, "formulario:terceiro"))).send_keys(self.multas_indenizacoes_terceiro_1)

                            # Tempo de Controle
                            time.sleep(1)

                            # Tipo - (Informado)
                            selecionar_informado = WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, 'formulario:valor:0')))
                            selecionar_informado.click()

                            # Tempo de controle
                            time.sleep(1)

                            # Vencimento
                            campo_vencimento = WebDriverWait(driver, self.delay).until(EC.visibility_of_element_located((By.NAME, 'formulario:dataVencimentoInputDate')))
                            campo_vencimento.send_keys(self.multas_indenizacoes_vcto_1)

                            # Tempo de controle
                            time.sleep(0.5)

                            # Valor
                            campo_valor = WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.NAME, 'formulario:valor2')))
                            campo_valor.send_keys(self.multas_indenizacoes_valor_1)

                            # Tempo de Controle
                            time.sleep(1)
                            if 'SIM' in self.multas_indenizacoes_aplicar_juros_1:
                                aplicar_juros = WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, 'formulario:aplicarJuros')))
                                if aplicar_juros.is_selected():
                                    print("- Checkbox - 'Aplicar Juros' - Já Habilitado.")
                                else:
                                    aplicar_juros.click()
                                time.sleep(1)

                                # Conversão e Preenchimento da data de Juros — A partir de
                                self.multas_indenizacoes_a_partir_de_1 = xlrd.xldate_as_datetime(self.multas_indenizacoes_a_partir_de_1, 0)
                                self.multas_indenizacoes_a_partir_de_1 = self.multas_indenizacoes_a_partir_de_1.strftime("%d/%m/%Y")
                                print(" - Aplicar Juros a partir de: ", self.multas_indenizacoes_a_partir_de_1)
                                # PJeCalc
                                WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.NAME, "formulario:dataJurosAPartirDeInputDate"))).send_keys(self.multas_indenizacoes_a_partir_de_1)
                                time.sleep(0.5)

                            self.aplicar_indice_da_multa(driver, f"multas_indenizacoes_indice_outro_{indice}")
                            self.salvar(driver)
                            self.objTools.aguardar_carregamento(driver)

                            # Tempo de controle
                            time.sleep(2)

                            self.verificacao(driver)

                            break

                print('\n')
                indice += 1

    def aplicar_indice_da_multa(self, driver, chave):
        """Correção monetária própria da multa INFORMADA (do .json): "Utilizar outro índice" + o índice da lista."""
        valores = [v for k, v in zip(self.planilha_base['IDENTIFICADOR'], self.planilha_base['INFORMACAO'])
                   if isinstance(k, str) and k.strip() == chave]
        if not valores or not isinstance(valores[0], str) or not valores[0].strip():
            return
        WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, 'formulario:correcaoMonetaria:1'))).click()
        self.objTools.aguardar_carregamento(driver)
        time.sleep(1)
        Select(WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.ID, 'formulario:outroIndiceCorrecao')))).select_by_visible_text(valores[0].strip())
        time.sleep(0.5)
        print(f"- [Multa] correção por outro índice: {valores[0].strip()}")

    def salvar(self, driver):
        WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.ID, 'formulario:salvar'))).click()

    def excluir_lancadas(self, driver):
        """Exclui as multas já salvas no cálculo (antes de repetir a tela, para não duplicar). Devolve quantas excluiu."""
        excluidas = 0
        for _ in range(50):
            self.acessar_multas_indenizacoes(driver)
            self.objTools.aguardar_carregamento(driver)
            time.sleep(self.delayG)
            links = driver.find_elements(By.CSS_SELECTOR, "[id^='formulario:listagem'] a.linkExcluir")
            if not links:
                return excluidas
            driver.execute_script("arguments[0].click();", links[0])
            self.objTools.aguardar_carregamento(driver)
            time.sleep(self.delayG)
            WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, "formulario:excluir"))).click()
            try:
                WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.ID, "popup_ok"))).click()
            except TimeoutException:
                pass
            self.objTools.aguardar_carregamento(driver)
            time.sleep(self.delayG)
            excluidas += 1
        raise RuntimeError("a listagem de multas não esvaziou depois de 50 exclusões")

    def main_multas_indenizacoes(self, driver):
        from Calculo.leitura_planilha import tela_tem_lancamento
        if not tela_tem_lancamento(self.planilha_base, ("multas_indenizacoes_",), {"multas_indenizacoes_qtd"}):
            print("- [Multas e Indenizações]: o pedido não traz multas; tela não aberta")
            return
        # Falha no meio: exclui o que já foi salvo e repete uma vez (repetir sem excluir duplicava as multas);
        # na 2ª falha, interrompe: o cálculo sairia sem parte das multas.
        for tentativa in (1, 2):
            try:
                self.acessar_multas_indenizacoes(driver)
                self.objTools.aguardar_carregamento(driver)
                # Tempo de controle
                time.sleep(self.delayG)
                self.preencher_dados_multas_indenizacoes(driver)
                # Tempo de controle
                time.sleep(self.delayG)
                self.objTools.limparFilesTemp()
                print('-- Fim - (Multas e Indenizações) --')
                return
            except Exception as e:
                motivo = str(e).strip().splitlines()[0][:200] if str(e).strip() else type(e).__name__
                print(f"- [except_main_multas_indenizacoes] tentativa {tentativa}: {motivo}")
                if tentativa == 2:
                    interromper('Multas e Indenizações', f"a tela falhou duas vezes: {motivo}")
                    return
                try:
                    driver.refresh()
                    time.sleep(5)
                    print(f"- [Multas e Indenizações] excluídas {self.excluir_lancadas(driver)} multa(s) salvas antes de repetir")
                except Exception as erro:
                    interromper('Multas e Indenizações', f"falhou ({motivo}) e não foi possível excluir as multas já salvas "
                                                         f"para repetir: {str(erro).strip()[:150] or type(erro).__name__}")
                    return
