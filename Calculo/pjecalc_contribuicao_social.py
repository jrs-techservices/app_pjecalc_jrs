from Tools.pendencias import de_relatorio
from selenium.webdriver.support.wait import WebDriverWait, TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoAlertPresentException
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import pandas as pd
import xlrd
import time
import os
import gc
#
# from Calculo.pjecalc_dados_calculo import DadosCalculo
from Tools.pjecalc_control import Control
from Calculo.leitura_planilha import (ler_pje_hist_val, booleano_da_planilha, valor_vazio, escolher_atividade_economica,
                                      ler_pje_bd, SemHistoricoSalarial)
import pyautogui as pa


class ContribuicaoSocial:


    def __init__(self, source):
        self.source = source
        try:
            self.planilha_base_inss = ler_pje_hist_val(self.source, header=3)
        except SemHistoricoSalarial:
            self.planilha_base_inss = None
        self.planilha_base = ler_pje_bd(self.source)
        self.delay = 10
        self.delayG = 1.5
        self.objTools = Control()
        self.cont_social_apurar_segurado = ""
        self.cont_social_cobrar_reclamante = ""
        self.cont_social_com_correcao_trabalhista = ""
        self.cont_social_salario_pagos = ""
        self.cont_social_aliquota_segurado = ""
        self.cont_social_aliquota_empregador = ""
        self.cont_social_apurar_empresa = ""
        self.cont_social_apurar_sat = ""
        self.cont_social_apurar_terceiros = ""
        self.processo_de_agroindustria = ""
        self.empresa_enquadrada_simples = ""
        self.empresa_com_desoneracao = ""
        self.empresa_agro = ""
        self.empresa_desonerada = ""
        self.entidade_filantropica = ""



    def gerar_relatorio(self, campo, subatividade, status):
        file_txt_log = open(os.getcwd() + '\log.txt', "a")
        file_txt_log.write(f'- {campo} : {subatividade} | {status}\n')
        return file_txt_log.close()

    def mensagem_alert_frontend(self, driver, conteudo):
        driver.execute_script(f"alert('{conteudo}')")
        WebDriverWait(driver, 5).until(EC.alert_is_present())
        alerta = Alert(driver)
        time.sleep(3)
        try:
            alerta.accept()
        except NoAlertPresentException:
            pass

    def verificacao_cnae(self, driver):

        delay = 5
        mensagem_sucesso = ""
        mensagem_erro = ""
        conteudo = ""


        elemento_titulo = WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.ID, 'barraTitulo')))
        titulo_pagina = elemento_titulo.text
        titulo_pagina = titulo_pagina.replace(">", ":")

        def gerar_relatorio(campo, status):
            file_txt_log = open(os.getcwd() + '\log.txt', "a")
            file_txt_log.write(f'- {campo} : {titulo_pagina} | {status}\n')
            return file_txt_log.close()

        def gerar_relatorio_erro(campo, status):
            file_txt_log = open(os.getcwd() + '\log.txt', "a")
            file_txt_log.write(f'- {campo} | {status}\n')
            return file_txt_log.close()

        try:
            mensagem_sucesso = WebDriverWait(driver, 3).until(EC.visibility_of_element_located((By.CLASS_NAME, "sucesso")))
        except TimeoutException:
            pass

        try:
            mensagem_erro = WebDriverWait(driver, 3).until(EC.visibility_of_element_located((By.CLASS_NAME, "erro")))
        except TimeoutException:
            pass

        if mensagem_sucesso:
            msg = mensagem_sucesso.text
            msg = msg.replace("\n", "")
            print("- ", msg)
            gerar_relatorio('Contribuição Social', 'Ok')
        elif mensagem_erro:
            # msg = mensagem_erro.text
            # Script
            elementos_erro = WebDriverWait(driver, delay).until(EC.visibility_of_all_elements_located((By.CLASS_NAME, "linkErro")))
            if elementos_erro:
                # print("- Tamanho da Lista: ", len(elementos_erro))
                for elemento in elementos_erro:
                    # Início Tratamento
                    erro = elemento.get_attribute("textContent")
                    erros = erro.split("//<!")
                    conteudo = str(erros[0])
                    driver.execute_script(f"alert('{conteudo}')")
                    WebDriverWait(driver, delay).until(EC.alert_is_present())
                    alerta = Alert(driver)
                    time.sleep(3)
                    try:
                        alerta.accept()
                    except NoAlertPresentException:
                        continue
            gerar_relatorio_erro(f'Contribuição Social: {conteudo}', '---------- Erro! ----------')
            de_relatorio(f'Contribuição Social: {conteudo}')
            #
            try:
                elemento_cancelar_status = WebDriverWait(driver, delay).until(EC.presence_of_element_located((By.NAME, "formulario:cancelarGeracao")))
                elemento_cancelar_status.click()
            except TimeoutException:
                pass

            try:
                elemento_cancelar_status_2 = WebDriverWait(driver, delay).until(EC.presence_of_element_located((By.NAME, "formulario:cancelar")))
                elemento_cancelar_status_2.click()
            except TimeoutException:
                pass

        time.sleep(2)


    def verificacao(self, driver):

        delay = 10

        elemento_titulo = WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.ID, 'barraTitulo')))
        titulo_pagina = elemento_titulo.text

        titulo_pagina = titulo_pagina.replace(">", ":")

        def gerar_relatorio(campo, status):
            file_txt_log = open(os.getcwd() + '\log.txt', "a")
            file_txt_log.write(f'- {campo} : {titulo_pagina} | {status}\n')
            return file_txt_log.close()

        try:
            mensagem = WebDriverWait(driver, delay).until(
                EC.presence_of_element_located((By.ID, 'formulario:painelMensagens:j_id69')))
            msg = mensagem.text
            if 'Operação realizada com sucesso.' in msg:
                # print('* Operação realizada com sucesso.')
                gerar_relatorio('Contribuição Social', 'Ok')
            else:
                print('* ERRO!', msg)
                gerar_relatorio('Contribuição Social', '---------- Erro! ----------')
                de_relatorio('Contribuição Social')
                try:
                    self.cancelar_operacao(driver)
                except TimeoutException:
                    pass
        except TimeoutException:
            print('- [Except][INSS] - Elemento não encontrado/A Página demorou para responder. Encerrando...')

        # Tempo de controle
        time.sleep(2)

    def acessar_contribuicao_social(self, driver):
        WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.CLASS_NAME, "menuImageInss"))).click()

    def selecionar_salarios_devidos(self, driver):

        for i in range(len(self.planilha_base)):

            coluna_identificador = self.planilha_base.loc[i, 'IDENTIFICADOR']
            coluna_informacao = self.planilha_base.loc[i, 'INFORMACAO']

            # Condição para pular as linhas em branco da coluna Identificador na planilha base
            if type(coluna_identificador) == float:
                continue
            elif coluna_identificador == 'cont_social_apurar_segurado':
                self.cont_social_apurar_segurado = coluna_informacao
            elif coluna_identificador == 'cont_social_cobrar_reclamante':
                self.cont_social_cobrar_reclamante = coluna_informacao
            elif coluna_identificador == 'cont_social_com_correcao_trabalhista':
                self.cont_social_com_correcao_trabalhista = coluna_informacao


        self.ajustar_checkbox(driver, 'formulario:apurarInssSeguradoDevido', self.cont_social_apurar_segurado, 'APURAR_INSS_SEGURADO')
        self.ajustar_checkbox(driver, 'formulario:cobrarDoReclamanteDevido', self.cont_social_cobrar_reclamante, 'COBRAR_DO_RECLAMANTE')
        self.ajustar_checkbox(driver, 'formulario:corrigirDescontoReclamante', self.cont_social_com_correcao_trabalhista, 'CORRIGIR_DESCONTO_RECLAMANTE')

    def ajustar_checkbox(self, driver, id_campo, valor, rotulo):
        """Sem valor na planilha mantém o padrão do PJe-Calc; campo desabilitado (ex.: 'Cobrar' com 'Apurar' desmarcado) não é alterado."""
        marcar = booleano_da_planilha(valor)
        if marcar is None:
            print(f"- [{rotulo}]: sem valor na planilha ({valor!r}); mantido o padrão do PJe-Calc")
            return
        try:
            campo = WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, id_campo)))
        except TimeoutException:
            print(f"- [{rotulo}]: campo desabilitado ou ausente no PJe-Calc; não alterado")
            return
        if campo.is_selected() != marcar:
            campo.click()

    def selecionar_salarios_pagos(self, driver):

        for i in range(len(self.planilha_base)):

            coluna_identificador = self.planilha_base.loc[i, 'IDENTIFICADOR']
            coluna_informacao = self.planilha_base.loc[i, 'INFORMACAO']

            # Condição para pular as linhas em branco da coluna Identificador na planilha base
            if type(coluna_identificador) == float:
                continue
            elif coluna_identificador == 'cont_social_salario_pagos':
                self.cont_social_salario_pagos = coluna_informacao
                break

        self.ajustar_checkbox(driver, 'formulario:apurarSalariosPagos', self.cont_social_salario_pagos, 'APURAR_SALARIOS_PAGOS')


    def salvar(self, driver):
        WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.CSS_SELECTOR, '.botao#formulario\:salvar'))).click()

    def acessar_ocorrencias(self, driver):
        WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, 'formulario:ocorrencias'))).click()

    def regerar(self, driver):
        WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, 'formulario:regerar'))).click()

    def selecionar_aliquota_segurado(self, driver):

        for i in range(len(self.planilha_base)):

            coluna_identificador = self.planilha_base.loc[i, 'IDENTIFICADOR']
            coluna_informacao = self.planilha_base.loc[i, 'INFORMACAO']

            # Condição para pular as linhas em branco da coluna Identificador na planilha base
            if type(coluna_identificador) == float:
                continue
            elif coluna_identificador == 'cont_social_aliquota_segurado':
                self.cont_social_aliquota_segurado = coluna_informacao
                print('- Alíquota Segurado: ', self.cont_social_aliquota_segurado)
                # Após encontrar e atribuir o valor, encerrar o loop
                break

        if self.cont_social_aliquota_segurado == 'Segurado Empregado':
            elemento_segurado = WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, 'formulario:aliquotaEmpregado:0')))
            checkbox_segurado = elemento_segurado.is_selected()
            if checkbox_segurado:
                print('- Checkbox - "Segurado Empregado" - Já Habilitado.')
            else:
                print('- Checkbox - "Segurado Empregado" - Foi Habilitado.')
                elemento_segurado.click()

        elif self.cont_social_aliquota_segurado == 'Empregado Doméstico':
            elemento_empregado = WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, 'formulario:aliquotaEmpregado:1')))
            checkbox_empregado = elemento_empregado.is_selected()
            if checkbox_empregado:
                print('- Checkbox - "Empregado Doméstico" - Já Habilitado.')
            else:
                print('- Checkbox - "Empregado Doméstico" - Foi Habilitado.')
                elemento_empregado.click()
        elif self.cont_social_aliquota_segurado == 'Fixa':
            elemento_fixa = WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, 'formulario:aliquotaEmpregado:2')))
            checkbox_fixa = elemento_fixa.is_selected()
            if checkbox_fixa:
                print('- Checkbox - "Fixa" - Já Habilitado.')
            else:
                print('- Checkbox - "Fixa" - Foi Habilitado.')
                elemento_fixa.click()
        elif valor_vazio(self.cont_social_aliquota_segurado):
            print('- Alíquota Segurado: sem valor na planilha; mantido o padrão do PJe-Calc')
        else:
            print('!! Parâmetros das Ocorrências -> Alíquota Segurado: Erro!!')

    # Nova Função para o caso do cnae não ser encontrado.
    def definar_aliquota_empregador_fixa(self, driver):

        val_fixo_empresa = "20,0000"
        val_fixo_sat = "3,0000"
        # Option Button
        WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, "formulario:aliquotaEmpregador:2"))).click()
        time.sleep(0.5)
        # Empresa (%)
        WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.NAME, "formulario:aliquotaEmpresaFixa"))).send_keys(val_fixo_empresa)
        time.sleep(0.5)
        # SAT (%)
        WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.NAME, "formulario:aliquotaRatFixa"))).send_keys(val_fixo_sat)
        time.sleep(0.5)

    # CNAE — Atualização - 04/01/2023
    def preencher_atividade_economica(self, driver):

        for i in range(len(self.planilha_base)):

            coluna_identificador = self.planilha_base.loc[i, 'IDENTIFICADOR']
            coluna_informacao = self.planilha_base.loc[i, 'INFORMACAO']

            # Condição para pular as linhas em branco da coluna Identificador na planilha base
            if type(coluna_identificador) == float:
                continue
            elif coluna_identificador == 'cont_social_aliquota_empregador':
                self.cont_social_aliquota_empregador = coluna_informacao
                # Remover espaços em branco
                if isinstance(self.cont_social_aliquota_empregador, str):
                    self.cont_social_aliquota_empregador = self.cont_social_aliquota_empregador.strip()
                print('- Atividade Econômica *: ', self.cont_social_aliquota_empregador)
                # Após identificar e atribuir o valor, encerrar o loop
                break

        if valor_vazio(self.cont_social_aliquota_empregador):
            print('- Atividade Econômica: sem valor na planilha; mantido o padrão do PJe-Calc')
            return

        # Selecionar Alíquota Empregador → Até o momento será sempre a opção 'Por Atividade Econômica'
        elemento_por_ativ_economica = WebDriverWait(driver, self.delay).until(
            EC.element_to_be_clickable((By.ID, 'formulario:aliquotaEmpregador:0')))
        status_checkbox = elemento_por_ativ_economica.is_selected()
        if status_checkbox:
            print('- Checkbox - "Por Atividade Econômica" - Já Habilitado.')
        else:
            print('- Checkbox - "Por Atividade Econômica" - Foi Habilitado.')
            elemento_por_ativ_economica.click()

        # Tempo de controle
        time.sleep(1)
        campo_atividade_economica = WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.NAME, 'formulario:atividadesEconomicas')))
        campo_atividade_economica.send_keys(self.cont_social_aliquota_empregador)
        # Tempo de controle
        time.sleep(2)
        # Lê todas as sugestões antes de escolher: o "contém" com várias entradas pegaria a primeira da lista.
        xpath_sugestao = "/html/body/form/div/div[3]/table/tbody/tr/td[3]/span/div/table[1]/tbody/tr[1]/td/span[3]/fieldset/fieldset/div[1]/div/fieldset/div[1]/span/table/tbody/tr[1]/td/span/div[1]/div[1]/div/table/tbody/tr/td/div/table/tbody/tr[{}]/td"
        sugestoes = []
        while True:
            try:
                celula = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.XPATH, xpath_sugestao.format(len(sugestoes) + 1))))
            except TimeoutException:
                break
            sugestoes.append(celula.text)
        print(f"- [CNAE] sugestões do PJe-Calc: {sugestoes}")

        try:
            # Pelo serviço, o SAP manda a descrição completa e a ambiguidade para a execução; a janela antiga segue como antes.
            escolhida = escolher_atividade_economica(self.cont_social_aliquota_empregador, sugestoes,
                                                     ambiguo_escolhe_primeiro=os.environ.get("PJECALC_SERVICO") != "1")
        except ValueError as erro:
            print(f"- [CNAE]: {erro}")
            pa.alert(title='Rôberto', text=f'Contribuição Social: {erro}')
            raise

        if escolhida is not None:
            posicao, texto = escolhida
            print(f"- [CNAE] escolhida: {texto}")
            with open(os.getcwd() + '\log.txt', "a") as file_txt_log:
                file_txt_log.write(f"- Contribuição Social : CNAE : {texto}\n")
            WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.XPATH, xpath_sugestao.format(posicao + 1)))).click()
            time.sleep(1)
            self.selecionar_atividade_economica_checkbox(driver)
        elif not sugestoes:
            # Trecho de código para o caso do cnae não ser encontrado
            elemento = WebDriverWait(driver, self.delay).until(EC.visibility_of_element_located((By.ID, "formulario:suggestionautoCompleteAtividadesNothingLabel")))
            retorno_registro = elemento.get_attribute("textContent")
            print("- Retorno: ", retorno_registro)
            if "Registro não encontrado" in retorno_registro:
                self.mensagem_alert_frontend(driver, "Registro não encontrado. Será adicionado a Alíquota do Empregador Fixa.")
                self.definar_aliquota_empregador_fixa(driver)
                file_txt_log = open(os.getcwd() + '\log.txt', "a")
                conteudo_log = f"- Contribuição Social : CNAE : {retorno_registro} - Será adicionado a Alíquota do Empregador Fixa "
                file_txt_log.write(conteudo_log)
                file_txt_log.close()
            else:
                self.definar_aliquota_empregador_fixa(driver)
        else:
            print(f"- [CNAE]: nenhuma sugestão corresponde a '{self.cont_social_aliquota_empregador}'; alíquota do empregador fixa")
            self.definar_aliquota_empregador_fixa(driver)

    def selecionar_atividade_economica_checkbox(self, driver):

        for i in range(len(self.planilha_base)):

            coluna_identificador = self.planilha_base.loc[i, 'IDENTIFICADOR']
            coluna_informacao = self.planilha_base.loc[i, 'INFORMACAO']

            # Condição para pular as linhas em branco da coluna Identificador na planilha base
            if type(coluna_identificador) == float:
                continue
            elif coluna_identificador == 'cont_social_apurar_empresa':
                self.cont_social_apurar_empresa = coluna_informacao
                print('- Apurar Empresa: ', self.cont_social_apurar_empresa)

                self.ajustar_checkbox(driver, 'formulario:apurarEmpresaPorAtividade', self.cont_social_apurar_empresa, 'APURAR_EMPRESA')

            elif coluna_identificador == 'cont_social_apurar_sat':
                self.cont_social_apurar_sat = coluna_informacao
                print('- Apurar SAT: ', self.cont_social_apurar_sat)

                self.ajustar_checkbox(driver, 'formulario:apurarRATPorAtividade', self.cont_social_apurar_sat, 'APURAR_SAT')

            elif coluna_identificador == 'cont_social_apurar_terceiros':
                self.cont_social_apurar_terceiros = coluna_informacao
                print('- Apurar Terceiros: ', self.cont_social_apurar_terceiros)

                self.ajustar_checkbox(driver, 'formulario:apurarTerceirosPorAtividade', self.cont_social_apurar_terceiros, 'APURAR_TERCEIROS')

    # Novas funções para a versão 3.34 da planilha base
    def definir_aliquota_empregador_agro(self, driver):

        for i in range(len(self.planilha_base)):

            coluna_identificador = self.planilha_base.loc[i, 'IDENTIFICADOR']
            coluna_informacao = self.planilha_base.loc[i, 'INFORMACAO']

            # Condição para pular as linhas em branco da coluna Identificador na planilha base
            if type(coluna_identificador) == float:
                continue
            elif coluna_identificador == "processo_de_agroindustria":
                self.processo_de_agroindustria = coluna_informacao
                print("- Processo de Agroindústria: ", self.processo_de_agroindustria)
                break

        if booleano_da_planilha(self.processo_de_agroindustria) is True:
            # Selecionar a opção Fixa
            WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, "formulario:aliquotaEmpregador:2"))).click()
            time.sleep(1)
            # Empresa(%)
            campo_empresa = WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.NAME, "formulario:aliquotaEmpresaFixa")))
            campo_empresa.click()
            campo_empresa.send_keys("0")
            # SAT (%)
            campo_sat = WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.NAME, "formulario:aliquotaRatFixa")))
            campo_sat.click()
            campo_sat.send_keys("0")
            # Terceiros (%)

    def definir_aliquota_empregador_entidade_filantropica(self, driver):

        for i in range(len(self.planilha_base)):

            coluna_identificador = self.planilha_base.loc[i, 'IDENTIFICADOR']
            coluna_informacao = self.planilha_base.loc[i, 'INFORMACAO']

            # Condição para pular as linhas em branco da coluna Identificador na planilha base
            if type(coluna_identificador) == float:
                continue
            elif coluna_identificador == "entidade_filantropica":
                self.entidade_filantropica = coluna_informacao
                print("-Entidade Filantrópica: ", self.entidade_filantropica)
                break

        if booleano_da_planilha(self.entidade_filantropica) is True:
            # Selecionar a opção Fixa
            WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, "formulario:aliquotaEmpregador:2"))).click()
            time.sleep(1)
            # Empresa(%)
            campo_empresa = WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.NAME, "formulario:aliquotaEmpresaFixa")))
            campo_empresa.click()
            campo_empresa.send_keys("0")
            # SAT (%)
            campo_sat = WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.NAME, "formulario:aliquotaRatFixa")))
            campo_sat.click()
            campo_sat.send_keys("0")
            # Terceiros (%)

    def definir_periodos_simples_nacional(self, driver):

        for i in range(len(self.planilha_base)):

            coluna_identificador = self.planilha_base.loc[i, 'IDENTIFICADOR']
            coluna_informacao = self.planilha_base.loc[i, 'INFORMACAO']

            # Condição para pular as linhas em branco da coluna Identificador na planilha base
            if type(coluna_identificador) == float:
                continue
            elif coluna_identificador == "empresa_enquadrada_simples":
                self.empresa_enquadrada_simples = coluna_informacao
                print("- Empresa enquadra no Simples Nacional: ", self.empresa_enquadrada_simples)
                break

        if booleano_da_planilha(self.empresa_enquadrada_simples) is True:

            planilha = pd.read_excel(self.source, sheet_name='PJE-DIV', header=20)

            for i in range(len(planilha)):
                inicio = planilha.loc[i, "SN_INICIO"]
                fim = planilha.loc[i, "SN_TERMINO"]

                if inicio > 0 and fim > 0:
                    comp_inicial = int(inicio)
                    comp_final = int(fim)
                    # Conversão para Datetime
                    comp_inicial = xlrd.xldate_as_datetime(comp_inicial, 0)
                    comp_final = xlrd.xldate_as_datetime(comp_final, 0)
                    # Conversão para Data str
                    comp_inicial_dt = comp_inicial.strftime("%m/%Y")
                    comp_fim_dt = comp_final.strftime("%m/%Y")
                    print(comp_inicial_dt, " - ", comp_fim_dt)
                    # Início
                    comp_inicial = WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.NAME, "formulario:dataInicioSimplesInputDate")))
                    comp_inicial.send_keys(comp_inicial_dt)
                    # Fim
                    comp_fim = WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.NAME, "formulario:dataTerminoSimplesInputDate")))
                    comp_fim.send_keys(comp_fim_dt)
                    # Adicionar
                    WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, "formulario:cmdIncluirPeriodoSimples"))).click()
                    self.objTools.aguardar_carregamento(driver)
                    time.sleep(1)

    def definir_empresa_desonerada(self, driver):

        for i in range(len(self.planilha_base)):

            coluna_identificador = self.planilha_base.loc[i, 'IDENTIFICADOR']
            coluna_informacao = self.planilha_base.loc[i, 'INFORMACAO']

            # Condição para pular as linhas em branco da coluna Identificador na planilha base
            if type(coluna_identificador) == float:
                continue
            elif coluna_identificador == "empresa_com_desoneracao":
                self.empresa_com_desoneracao = coluna_informacao
                print("- Empresa com Desoneração: ", self.empresa_com_desoneracao)
                break

        if booleano_da_planilha(self.empresa_com_desoneracao) is True:

            # Selecionar a opção Por Período
            WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, "formulario:aliquotaEmpregador:1"))).click()

            planilha = pd.read_excel(self.source, sheet_name='PJE-DIV', header=7)
            var_str = ""
            for i in range(len(planilha)):
                inicio = planilha.loc[i, "DES_INICIO"]
                fim = planilha.loc[i, "DES_TERMINO"]
                des = planilha.loc[i, "DES"]
                emp = planilha.loc[i, "EMP"]
                sat = planilha.loc[i, "SAT (%)"]

                if type(inicio) != type(var_str):

                    if inicio > 0 and fim > 0:
                        if des == "SIM":
                            emp = f"{emp:.4%}"
                            sat = f"{sat:.4%}"
                            print("- Empresa (%): ", emp, " -- SAT (%): ", sat)
                        else:
                            emp = f"{emp:.4%}"
                            sat = f"{sat:.4%}"
                            print("- Empresa (%): ", emp, " -- SAT (%): ", sat)
                        # Continua
                        comp_inicial = int(inicio)
                        comp_final = int(fim)
                        # Conversão para Datetime
                        comp_inicial = xlrd.xldate_as_datetime(comp_inicial, 0)
                        comp_final = xlrd.xldate_as_datetime(comp_final, 0)
                        # Conversão para Data str
                        comp_inicial_dt = comp_inicial.strftime("%m/%Y")
                        comp_fim_dt = comp_final.strftime("%m/%Y")
                        print(comp_inicial_dt, " - ", comp_fim_dt)

                        # INÍCIO
                        campo_inicio = WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.NAME, "formulario:dataInicioPeriodoInputDate")))
                        campo_inicio.send_keys(comp_inicial_dt)
                        # FIM
                        campo_fim = WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.NAME, "formulario:dataTerminoPeriodoInputDate")))
                        campo_fim.send_keys(comp_fim_dt)
                        # EMPRESA
                        campo_empresa = WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.NAME, "formulario:aliquotaEmpresaPorPeriodo")))
                        campo_empresa.send_keys(emp)
                        # SAT
                        campo_sat = WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.NAME, "formulario:aliquotaRatPorPeriodo")))
                        campo_sat.send_keys(sat)
                        # Adicionar
                        WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, "formulario:cmdIncluirPorPeriodo"))).click()
                        self.objTools.aguardar_carregamento(driver)
                        time.sleep(1)

    def definir_aliquota_empregador_v3_34(self, driver):

        for i in range(len(self.planilha_base)):

            coluna_identificador = self.planilha_base.loc[i, 'IDENTIFICADOR']
            coluna_informacao = self.planilha_base.loc[i, 'INFORMACAO']

            # Condição para pular as linhas em branco da coluna Identificador na planilha base
            if type(coluna_identificador) == float:
                continue
            elif coluna_identificador == "processo_de_agroindustria":
                self.empresa_agro = coluna_informacao
                print("- Processo de Agroidústria: ", self.empresa_agro)
            elif coluna_identificador == "empresa_com_desoneracao":
                self.empresa_desonerada = coluna_informacao
                print("- Empresa com Desoneração: ", self.empresa_desonerada)
            elif coluna_identificador == "entidade_filantropica":
                self.entidade_filantropica = coluna_informacao
                print("- Empresa com Desoneração: ", self.entidade_filantropica)

                # Se a empresa é agro
                if booleano_da_planilha(self.empresa_agro) is True:
                    self.definir_aliquota_empregador_agro(driver)
                    time.sleep(1)
                # Se a empresa é desonerada
                elif booleano_da_planilha(self.empresa_desonerada) is True:
                    self.definir_empresa_desonerada(driver)
                    time.sleep(1)
                elif booleano_da_planilha(self.entidade_filantropica) is True:
                    self.definir_aliquota_empregador_entidade_filantropica(driver)
                    time.sleep(1)
                else:
                    # Senão, CNAE
                    self.preencher_atividade_economica(driver)
                    time.sleep(1)
                    # self.selecionar_atividade_economica_checkbox(driver)
                    # time.sleep(1)

                # Simples Nacional
                self.definir_periodos_simples_nacional(driver)
                time.sleep(1)

    def confirmar_operacao(self, driver):
        WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, 'formulario:confirmarGeracao'))).click()

    def cancelar_operacao(self, driver):
        WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, 'formulario:cancelarGeracao'))).click()


    def preencher_salarios_pagos_historico(self, driver, admissao, rescisao, inicio_calculo, termino_calculo):

        # Condição para checar intervalo do cálculo. Não pode passar de 30 anos.
        print(f"- Data de Admissão: {admissao}\n- Data de Demissão: {rescisao}\n- Data Inicial do Cálculo: {inicio_calculo}\n- Data Final do Cálculo: {termino_calculo}\n")
        script = "alert('O escopo do cálculo é superior ao limite da planilha base (30 anos). Irei ignorar esta operação.')"
        resultado = 0

        if inicio_calculo != "" and termino_calculo != "":
            resultado = termino_calculo.year - inicio_calculo.year
            print("- Início e Término do cálculo preenchidos!")
            print(f"- Escopo do Cálculo: {resultado} anos.")

        elif inicio_calculo == "" and termino_calculo == "":
            resultado = rescisao.year - admissao.year
            print("- Início e Término do cálculo vazio!")
            print(f"- Escopo do Cálculo: {resultado} anos.")

        elif inicio_calculo == "":
            resultado = termino_calculo.year - admissao.year
            print("- Data de Cálculo Inicial vazio!")
            print(f"- Escopo do Cálculo: {resultado} anos.")

        elif termino_calculo == "":
            resultado = rescisao.year - inicio_calculo.year
            print("- Data de Término do Cálculo vazio!")
            print(f"- Escopo do Cálculo: {resultado} anos.")

        print("\n - Valor Final do Escopo do Cálculo: ", resultado)

        if resultado > 30:
            driver.execute_script(script)
            WebDriverWait(driver, self.delay).until(EC.alert_is_present())
            alerta = Alert(driver)
            self.gerar_relatorio("Contribuição Social", "O intervalo do Cálculo é superior ao limite da planilha (30 anos)", "---------- Erro! ----------")
            de_relatorio("Contribuição Social", "O intervalo do Cálculo é superior ao limite da planilha (30 anos)")
            time.sleep(5)
            alerta.accept()
        else:

            indice = 0
            # Coletar a quantidade de competência na coluna do Excel AA5
            quantidade_compentencias = self.planilha_base_inss.iloc[0, 26]
            print("- Quantidade de Competências: ", quantidade_compentencias)
            # Loop para percorrer a coluna AB do Excel
            for k in range(1, quantidade_compentencias + 1):
                col_base_inss = self.planilha_base_inss.iloc[k, 27]
                # Preencher PJeCalc
                try:
                    col_base_inss = f"{col_base_inss:.2f}"
                    campo_salarios_pagos = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.NAME, f'formulario:listagemOcorrenciasDevidos:{indice}:baseHistoricoDevido')))
                    campo_salarios_pagos.click()
                    campo_salarios_pagos.send_keys(Keys.CONTROL, "a")
                    campo_salarios_pagos.send_keys(col_base_inss)
                    indice += 1
                except TimeoutException:
                    time.sleep(1.5)
                    break

            # Tempo de controle
            time.sleep(1)
            self.salvar(driver)
            self.objTools.aguardar_carregamento(driver)
            # Tempo de controle
            time.sleep(1)
            self.verificacao(driver)
            # Tempo de controle
            time.sleep(1.5)

    def preencher_salarios_pagos_historico_v34(self, driver, admissao, rescisao, inicio_calculo, termino_calculo):

        if self.planilha_base_inss is None:
            print('- [AVISO][Contribuição Social]: pedido sem histórico salarial; base do INSS dos salários pagos não lançada.')
            return

        print(
            f"- Data de Admissão: {admissao}\n- Data de Demissão: {rescisao}\n- Data Inicial do Cálculo: {inicio_calculo}\n- Data Final do Cálculo: {termino_calculo}\n")
        script = "alert('O escopo do cálculo é superior ao limite da planilha base (30 anos). Irei ignorar esta operação.')"
        resultado = 0

        if inicio_calculo != "" and termino_calculo != "":
            resultado = termino_calculo.year - inicio_calculo.year
            print("- Início e Término do cálculo preenchidos!")
            print(f"- Escopo do Cálculo: {resultado} anos.")

        elif inicio_calculo == "" and termino_calculo == "":
            resultado = rescisao.year - admissao.year
            print("- Início e Término do cálculo vazio!")
            print(f"- Escopo do Cálculo: {resultado} anos.")

        elif inicio_calculo == "":
            resultado = termino_calculo.year - admissao.year
            print("- Data de Cálculo Inicial vazio!")
            print(f"- Escopo do Cálculo: {resultado} anos.")

        elif termino_calculo == "":
            resultado = rescisao.year - inicio_calculo.year
            print("- Data de Término do Cálculo vazio!")
            print(f"- Escopo do Cálculo: {resultado} anos.")

        # print("\n - Valor Final do Escopo do Cálculo: ", resultado)

        if resultado > 30:
            driver.execute_script(script)
            WebDriverWait(driver, self.delay).until(EC.alert_is_present())
            alerta = Alert(driver)
            self.gerar_relatorio("Histórico Salarial",
                                 "O intervalo do Cálculo é superior ao limite da planilha (30 anos)",
                                 "---------- Erro! ----------")
            time.sleep(5)
            alerta.accept()
        else:
            indice = 0
            # Coletar a quantidade de competência na coluna do Excel AA5
            quantidade_compentencias = self.planilha_base_inss.iloc[0, 26]
            print("- Quantidade de Competências 1: ", quantidade_compentencias)
            quantidade_compentencias = int(quantidade_compentencias)
            print("- Quantidade de Competências 2: ", quantidade_compentencias)
            # Loop para percorrer a coluna AB do Excel
            for k in range(2, quantidade_compentencias + 2):
                col_base_inss = self.planilha_base_inss.iloc[k, 27]
                # Preencher PJeCalc
                try:
                    col_base_inss = f"{col_base_inss:.2f}"
                    name_field = fr'//input[@name="formulario:listagemOcorrenciasDevidos:{indice}:baseHistoricoDevido"]'
                    field = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.XPATH, f'{name_field}')))
                    field.click()
                    field.send_keys(Keys.CONTROL, "a")  # Seleciona o texto atual
                    field.send_keys(Keys.DELETE)
                    field.send_keys(col_base_inss)
                    field.send_keys(Keys.TAB)

                    indice += 1
                except Exception as e:
                    print(f"- [except][INSS][preencher_salarios_pagos]: {e}")
                    time.sleep(1.5)
                    break

            self.salvar(driver)
            time.sleep(1.5)


    def main_contribuicao_social(self, driver, admissao, rescisao, inicio_calculo, termino_calculo):

        self.acessar_contribuicao_social(driver)
        # Aguardar Processamento
        self.objTools.aguardar_carregamento(driver)
        # Tempo de controle
        time.sleep(self.delayG)
        self.selecionar_salarios_devidos(driver)
        # Tempo de controle
        time.sleep(self.delayG)
        self.selecionar_salarios_pagos(driver)
        # Tempo de controle
        time.sleep(self.delayG)
        self.salvar(driver)
        # Aguardar Processamento
        self.objTools.aguardar_carregamento(driver)
        # Tempo de controle
        time.sleep(self.delayG)
        # Nova Função de Verificação
        self.verificacao_cnae(driver)
        # Tempo de controle
        time.sleep(self.delayG)
        self.acessar_ocorrencias(driver)
        self.objTools.aguardar_carregamento(driver)
        # Tempo de controle
        time.sleep(self.delayG)
        self.regerar(driver)
        # Tempo de controle
        time.sleep(self.delayG)
        self.objTools.aguardar_carregamento(driver)
        # Tempo de controle
        time.sleep(self.delayG)
        self.selecionar_aliquota_segurado(driver)
        # Tempo de controle
        time.sleep(self.delayG)
        # Para planilha base v3.34 - Início
        self.definir_aliquota_empregador_v3_34(driver)
        # Tempo de controle
        time.sleep(self.delayG)
        self.confirmar_operacao(driver)
        self.objTools.aguardar_carregamento(driver)
        # Tempo de controle
        time.sleep(self.delayG)
        self.verificacao_cnae(driver)
        # Tempo de controle
        time.sleep(self.delayG)
        # Para planilha base v3.34 - Início
        self.preencher_salarios_pagos_historico_v34(driver, admissao, rescisao, inicio_calculo, termino_calculo)
        # Para planilha base v3.34 - Fim
        self.objTools.aguardar_carregamento(driver)
        # Tempo de controle
        time.sleep(self.delayG)

        # - Limpar Temp
        self.objTools.limparFilesTemp()
        gc.collect(generation=0)
        gc.collect(generation=1)
        gc.collect(generation=2)

        print('-- Fim - (Contribuição Social) --')