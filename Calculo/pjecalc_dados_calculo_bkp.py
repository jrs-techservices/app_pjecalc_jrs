from selenium.webdriver.support.wait import WebDriverWait, TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoAlertPresentException
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
import pyautogui as pa
from datetime import datetime
import tkinter.filedialog
from tkinter import *
import pandas as pd
import unidecode
import shutil
import xlrd
import time
import os
import gc
from Tools.pjecalc_control import Control


class DadosCalculo:


    def __init__(self, source):
        self.source = source
        # Leitura da Planilha
        self.planilha_base = pd.read_excel(source, sheet_name='PJE-BD', header=1)
        # Tamanho da PlanilhaBase
        self.tamanho_planilha_base = len(self.planilha_base)
        self.objTools = Control()
        self.delay = 10
        self.delayG = 1.5

    # Instanciando um objeto da classe Controle

    def limparFiles(self):
        # Zerar arquivos (log.txt e source_plan.txt)
        l = open(os.getcwd() + "\log.txt", "w")
        l.close()
        s = open(os.getcwd() + "\source_plan.txt", "w")
        s.close()

    # Atributos
    local = ""
    mensagem_erro = ""
    datetime_admissao = ""
    datetime_demissao = ""
    datetime_inicio_calc = ""
    datetime_final_calc = ""
    source = ""

    def registrar_horario_inicial(self):
        horario_inicial_full = datetime.today()
        inicio = horario_inicial_full.strftime('%H:%M:%S')
        # print(inicio)
        file_txt_log = open(os.getcwd() + '\log.txt', "a")
        file_txt_log.write('- Horário Inicial: ' + inicio + '\n\n')
        return file_txt_log.close()

    def registrar_horario_final(self):
        horario_final_full = datetime.now()
        final = horario_final_full.strftime('%H:%M:%S')
        # print(final)
        file_txt_log = open(os.getcwd() + '\log.txt', "a")
        file_txt_log.write('\n- Horário Final: ' + final + '\n')
        return file_txt_log.close()

    def mensagem_alert_frontend(self, driver, conteudo):
        driver.execute_script(f"alert('{conteudo}')")
        WebDriverWait(driver, 5).until(EC.alert_is_present())
        alerta = Alert(driver)
        time.sleep(5)
        try:
            alerta.accept()
        except NoAlertPresentException:
            pass

    def verificacao_new(self, driver):

        def gerar_relatorio(campo, msg, status):
            file_txt_log = open(os.getcwd() + '\log.txt', "a")
            file_txt_log.write(f'- {campo}: {msg} | {status}\n')
            return file_txt_log.close()

        try:
            barraMensagem = WebDriverWait(driver, 3).until(EC.visibility_of_element_located((By.CLASS_NAME, "sucesso")))
        except TimeoutException:
            barraMensagem = WebDriverWait(driver, 3).until(EC.visibility_of_element_located((By.CLASS_NAME, "erro")))

        alertaMensagem = barraMensagem.get_attribute("textContent")

        if 'sucesso' in alertaMensagem:
            print("- Alerta de verificação: ", alertaMensagem)
            gerar_relatorio("Dados do Cálculo", "--", "Ok")
        else:
            print("- Alerta de verificação: ", alertaMensagem)
            elementos_error = WebDriverWait(driver, 3).until(
                EC.visibility_of_all_elements_located((By.CLASS_NAME, 'linkErro')))
            for erro in elementos_error:
                erroUtil = erro.get_attribute("textContent")
                erroUtil = erroUtil.split("//<![")
                print(erroUtil[0])
                # Pop-up na tela 01
                # self.mensagem_alert_frontend(driver, erroUtil[0])
                # Pop-up na tela 02
                pa.alert(title="Rôberto", text="Erro! " + erroUtil[0])
                # Registrar Log de erro
                gerar_relatorio("Dados do Cálculo", erroUtil[0], "---------- Erro! ----------")
            driver.close()
            exit()

    def verificacao(self, driver):

        delay = 10
        # local = 'Dados do Cálculo'
        try:
            # Elemento de erro
            # Retorna apenas um elemento
            elemento_class_error = WebDriverWait(driver, 5).until(
                EC.visibility_of_all_elements_located((By.CLASS_NAME, 'linkErro')))
            for elemento in elemento_class_error:
                erro = elemento.get_attribute("textContent")
                self.mensagem_erro = erro.split("//<!")
                print("Erro! ", self.mensagem_erro[0])
                pa.alert(title="Rôberto", text="Erro! " + self.mensagem_erro[0])
                primeira_aba = WebDriverWait(driver, self.delay).until(
                    EC.presence_of_element_located((By.ID, 'formulario:tabDadosProcesso')))
                conteudo_primeira_aba = primeira_aba.get_attribute("textContent")
                segunda_aba = WebDriverWait(driver, self.delay).until(
                    EC.presence_of_element_located((By.ID, 'formulario:tabParametrosCalculo')))
                conteudo_segunda_aba = segunda_aba.get_attribute("textContent")

                if erro in conteudo_primeira_aba:
                    print(" - Há erros na Aba - Dados do Processo!!")
                    self.local = 'Parâmetros do Cálculo'
                elif erro in conteudo_segunda_aba:
                    print(" - Há erros na Aba - Parâmetros do Cálculo!!")
                    self.local = 'Dados do Processo'
            if self.mensagem_erro:
                pa.alert(title="Rôberto", text="Favor, preencher os campos obrigatórios!\n O PJeCalc será fechado.")
                driver.close()
                exit()
        except TimeoutException:
            pass

        def gerar_relatorio(campo, status):
            file_txt_log = open(os.getcwd() + '\log.txt', "a")
            file_txt_log.write(f'- {campo}:{self.local} | {status}\n')
            return file_txt_log.close()

        try:
            mensagem = WebDriverWait(driver, delay).until(
                EC.presence_of_element_located((By.ID, 'formulario:painelMensagens:j_id77')))
            msg = mensagem.text
            if 'Operação realizada com sucesso.' in msg:
                # print('* Operação realizada com sucesso.')
                gerar_relatorio('Dados do Cálculo', 'Ok')
                # status_operacao = 'Ok'
            else:
                # print('* ERRO!', msg)
                gerar_relatorio('Dados do Cálculo', '---------- Erro! ----------')
        except TimeoutException:
            print('- [Except][Dados Cálculo] - Elemento não encontrado/A Página demorou para responder. Encerrando...')

        # Tempo de controle
        time.sleep(2)

    def source_base_worksheet(self):

        def upload_file():
            source_txt = os.getcwd() + '\source_plan.txt'
            file = open(source_txt, "w")
            conteudo = tkinter.filedialog.askopenfilename(title='Selecione a Planilha Base')
            file.write(conteudo)
            return file.close(), app.destroy()

        def mudar_cor_button(button, cor_ativa, cor_apagada):
            button.bind("<Enter>", func=lambda e: button.config(foreground=cor_ativa))
            button.bind("<Leave>", func=lambda e: button.config(foreground=cor_apagada))

        # folder = os.getcwd()
        # dir_raiz = os.path.dirname(folder)
        img = os.getcwd() + '\Tools\sistema.png'
        app = Tk()
        C = Canvas(app, height=200, width=300)
        app.title('Rô-berto')
        filename = PhotoImage(file=img)
        background_label = Label(app, image=filename)
        background_label.place(x=0, y=0, relwidth=1, relheight=1)
        btn = Button(app, text='Clique Aqui', font=('Helvetica', '8'), foreground='#28506E', command=upload_file,
                     borderwidth=0, background='#FFFFFF', activeforeground='green', activebackground='#FFFFFF')
        btn.place(height=20, width=120, x=90, y=110)

        mudar_cor_button(btn, "red", "#28506E")

        C.pack()
        app.mainloop()

    def encaminhar_log(self, id_processo):

        contador = 0
        source_log = os.getcwd() + '\log.txt'
        diretorio_destino = os.path.dirname(self.source)
        target_log = fr"{diretorio_destino}\ID_{id_processo} - Log Automação.txt"
        if os.path.exists(target_log):
            for item in os.listdir(diretorio_destino):
                if 'Log' in item:
                    contador += 1
            target_log = fr"{diretorio_destino}\ID_{id_processo} - Log Automação ({contador}).txt"
            contador += 1
            shutil.copy(source_log, target_log)
        else:
            shutil.copy(source_log, target_log)

        # Limpar
        f = open(source_log, 'w')
        f.close()

    # Selecionar a Planilha Base:
    # source_base_worksheet(self=None)

    # diretorio_classe = os.getcwd()
    # diretorio_raiz = os.path.dirname(diretorio_classe)
    source_txt = os.getcwd() + '\source_plan.txt'
    f = open(source_txt, "r")
    arquivo = f.read()
    # ATRIBUTOS DA CLASSE
    # Tempo de espera padrão

    # Variáveis para controle
    var_controle_int = 1
    var_controle_float = 1.1
    var_controle_string = "Em branco"
    var_controle_date = datetime.now()

    # Variáveis globais da classe
    numero_processo = ""
    processo = ""
    valor_da_causa = ""
    nome_parte1 = ""
    nome_parte2 = ""
    doc_parte2 = ""
    prazo_de_aviso_previo = ""
    quantidade_dias_aviso_previo = ""
    aplicar_prescricao_verbas = ""
    aplicar_prescricao_FGTS = ""
    projetar_aviso_previo_indenizado = ""
    limitar_avos_ao_periodo_do_calculo = ""
    zerar_valor_negativo_padrao = ""
    considerar_feriados_estaduais = ""
    considerar_feriados_municipais = ""
    sabado_como_dia_util = ""
    id_processo = ""

    # # Leitura da Planilha
    # planilha_base = pd.read_excel(arquivo, sheet_name='PJE-BD', header=1)
    # # Tamanho da PlanilhaBase
    # tamanho_planilha_base = len(planilha_base)

    # MÉTODOS
    def identificacao_processo(self, driver):

        for i in range(self.tamanho_planilha_base):

            col_identificador = self.planilha_base.loc[i, 'IDENTIFICADOR']
            dados_col_informacao = self.planilha_base.loc[i, 'INFORMACAO']

            # Condição para pular as linhas em branco da coluna Identificador na planilha base
            if type(col_identificador) == type(self.var_controle_float):
                # print('* Pulando linhas em branco ...')
                continue
            elif col_identificador == 'id_processo':
                self.id_processo = dados_col_informacao
                self.id_processo = str(self.id_processo)
                print('- ID: ', self.id_processo)
            elif col_identificador == 'numero_processo':
                self.numero_processo = dados_col_informacao
                print('- Numero do Processo: ', self.numero_processo)
                if "nao_preenchido" in self.numero_processo:
                    break
                else:
                    # Tratamento
                    self.processo = self.numero_processo
                    self.numero_processo = self.numero_processo.replace("-", " ")
                    self.numero_processo = self.numero_processo.replace(".", " ")
                    self.numero_processo = self.numero_processo.split()
                    print('- Numero do Processo: ', self.numero_processo)
                    # PJeCalc
                    # Número
                    campo_numero = WebDriverWait(driver, self.delay).until(
                        EC.presence_of_element_located((By.NAME, 'formulario:numero')))
                    campo_numero.send_keys(self.numero_processo[0])
                    # Dígito
                    campo_digito = WebDriverWait(driver, self.delay).until(
                        EC.presence_of_element_located((By.NAME, 'formulario:digito')))
                    campo_digito.send_keys(self.numero_processo[1])
                    # Ano
                    campo_ano = WebDriverWait(driver, self.delay).until(
                        EC.presence_of_element_located((By.NAME, 'formulario:ano')))
                    campo_ano.send_keys(self.numero_processo[2])
                    # Tribunal
                    campo_tribunal = WebDriverWait(driver, self.delay).until(
                        EC.presence_of_element_located((By.NAME, 'formulario:regiao')))
                    campo_tribunal.send_keys(self.numero_processo[4])
                    # Vara
                    campo_vara = WebDriverWait(driver, self.delay).until(
                        EC.presence_of_element_located((By.NAME, 'formulario:vara')))
                    campo_vara.send_keys(self.numero_processo[5])

                    # Tratamento do número do processo para o adicionar ao PDF e PJC
                    self.processo = self.processo.replace("-", "")
                    self.processo = self.processo.replace(".", "")
                    print("- Número do Processo para os arquivos PJC e PDF", self.processo)

        return self.id_processo, self.processo

    def preencher_valor_causa(self, driver):

        for i in range(self.tamanho_planilha_base):

            coluna_identificador = self.planilha_base.loc[i, 'IDENTIFICADOR']
            coluna_informacao = self.planilha_base.loc[i, 'INFORMACAO']

            # Condição para pular as linhas em branco da coluna Identificador na planilha base
            if type(coluna_identificador) == type(self.var_controle_float):
                # print('* Pulando linhas em branco ...')
                continue
            elif coluna_identificador == 'valor_da_causa':
                self.valor_da_causa = coluna_informacao
                print('- Valor da Causa: ', self.valor_da_causa)
                # PJeCalc
                # Valor da Causa
                if "nao_preenchido" in str(self.valor_da_causa):
                    break
                else:
                    self.valor_da_causa = f'{self.valor_da_causa:.2f}'
                    campo_valor_causa = WebDriverWait(driver, self.delay).until(
                        EC.presence_of_element_located((By.NAME, 'formulario:valorDaCausa')))
                    campo_valor_causa.send_keys(self.valor_da_causa)

    def preencher_nome_reclamante(self, driver):

        for i in range(len(self.planilha_base)):

            coluna_identificador = self.planilha_base.loc[i, 'IDENTIFICADOR']
            coluna_informacao = self.planilha_base.loc[i, 'INFORMACAO']

            # Condição para pular as linhas em branco da coluna Identificador na planilha base
            if type(coluna_identificador) == type(self.var_controle_float):
                # print('* Pulando linhas em branco ...')
                continue
            # Nome da parte 1
            elif coluna_identificador == "nome_parte1":
                self.nome_parte1 = coluna_informacao
                # nome_parte1 = coluna_informacao
                print('- Nome da parte 1: ', self.nome_parte1)
                if "nao_preenchido" in self.nome_parte1:
                    break
                else:
                    # Nome
                    campo_nome = WebDriverWait(driver, self.delay).until(
                        EC.presence_of_element_located((By.NAME, 'formulario:reclamanteNome')))
                    campo_nome.send_keys(self.nome_parte1)
                    break

        return self.nome_parte1

    def preencher_documento_reclamente(self, driver):

        for i in range(len(self.planilha_base)):

            coluna_identificador = self.planilha_base.loc[i, 'IDENTIFICADOR']
            coluna_informacao = self.planilha_base.loc[i, 'INFORMACAO']

            # Condição para pular as linhas em branco da coluna Identificador na planilha base
            if type(coluna_identificador) == type(self.var_controle_float):
                # print('* Pulando linhas em branco ...')
                continue
            # Documento da parte 1
            elif coluna_identificador == "doc_parte1":
                cpf = coluna_informacao
                cpf_str = str(cpf)
                if len(cpf_str) < 11:
                    cpf_str = f"{cpf_str:0>11}"
                print('- CPF Reclamante: ', cpf_str)
                if "nao_preenchido" in cpf_str:
                    break
                else:
                    # Selecionar a Opção CPF
                    selecionar_cpf = WebDriverWait(driver, self.delay).until(
                        EC.element_to_be_clickable((By.ID, 'formulario:documentoFiscalReclamante:0')))
                    selecionar_cpf.click()
                    # Tempo de Controle
                    time.sleep(1)
                    # cpf1 = cpf.replace(".", "")
                    # cpf_util = cpf1.replace("-", "")
                    # Preencher PJeCalc
                    campo_cpf = WebDriverWait(driver, self.delay).until(
                        EC.presence_of_element_located((By.NAME, 'formulario:reclamanteNumeroDocumentoFiscal')))
                    campo_cpf.send_keys(cpf_str)
                    break

    def preencher_advogado(self, driver):

        for i in range(len(self.planilha_base)):

            coluna_identificador = self.planilha_base.loc[i, 'IDENTIFICADOR']
            coluna_informacao = self.planilha_base.loc[i, 'INFORMACAO']

            # Condição para pular as linhas em branco da coluna Identificador na planilha base
            if type(coluna_identificador) == type(self.var_controle_float):
                # print('* Pulando linhas em branco ...')
                continue
            # Nome da parte 1
            elif coluna_identificador == "advogado_parte1":
                advogado_parte1 = coluna_informacao
                print('- Advogado da parte 1: ', advogado_parte1)
                if "nao_preenchido" in advogado_parte1:
                    break
                else:
                    # Nome
                    campo_nome = WebDriverWait(driver, self.delay).until(
                        EC.presence_of_element_located((By.NAME, 'formulario:nomeAdvogadoReclamante')))
                    campo_nome.send_keys(advogado_parte1)
                    # Tempo de controle
                    time.sleep(1)
                    # Adicionar
                    btn_add = WebDriverWait(driver, self.delay).until(
                        EC.element_to_be_clickable((By.ID, 'formulario:incluirAdvogadoReclamante')))
                    btn_add.click()
                    # Aguardar carregamento
                    self.objTools.aguardar_carregamento(driver)
                    break

    def preencher_reclamado(self, driver):

        for i in range(len(self.planilha_base)):

            coluna_identificador = self.planilha_base.loc[i, 'IDENTIFICADOR']
            coluna_informacao = self.planilha_base.loc[i, 'INFORMACAO']

            # Condição para pular as linhas em branco da coluna Identificador na planilha base
            if type(coluna_identificador) == type(self.var_controle_float):
                # print('* Pulando linhas em branco ...')
                continue
            elif coluna_identificador == 'nome_parte2':
                self.nome_parte2 = coluna_informacao
                self.nome_parte2 = str(self.nome_parte2)
                print('- Nome da parte 2: ', self.nome_parte2)
                if "nao_preenchido" in self.nome_parte2:
                    break
                else:
                    # PJeCalc — Preencher Nome do Reclamado
                    campo_nome = WebDriverWait(driver, self.delay).until(
                        EC.presence_of_element_located((By.NAME, 'formulario:reclamadoNome')))
                    campo_nome.send_keys(self.nome_parte2)

            elif coluna_identificador == 'doc_parte2':
                self.doc_parte2 = coluna_informacao
                self.doc_parte2 = str(self.doc_parte2)

                # Verificar a quantidade de caracteres do CNPJ. Se for inferior a 14, adiciona um zero a esquerda.
                if len(self.doc_parte2) < 14:
                    # Adicionar um zero à esquerda no CNPJ
                    self.doc_parte2 = f"{self.doc_parte2:0>14}"

                print('- CNPJ Reclamado: ', self.doc_parte2)
                if "nao_preenchido" in self.doc_parte2:
                    break
                else:
                    # PJeCalc - Preencher CNPJ do Reclamado
                    opcao_cnpj = WebDriverWait(driver, self.delay).until(
                        EC.element_to_be_clickable((By.ID, 'formulario:tipoDocumentoFiscalReclamado:1')))
                    opcao_cnpj.click()
                    # Tempo de Controle
                    time.sleep(1)
                    campo_numero_cnpj = WebDriverWait(driver, self.delay).until(
                        EC.presence_of_element_located((By.NAME, 'formulario:reclamadoNumeroDocumentoFiscal')))
                    campo_numero_cnpj.send_keys(self.doc_parte2)

    def preencher_advogado_parte2(self, driver):

        for i in range(len(self.planilha_base)):

            coluna_identificador = self.planilha_base.loc[i, 'IDENTIFICADOR']
            coluna_informacao = self.planilha_base.loc[i, 'INFORMACAO']

            # Condição para pular as linhas em branco da coluna Identificador na planilha base
            if type(coluna_identificador) == type(self.var_controle_float):
                # print('* Pulando linhas em branco ...')
                continue
            # Nome da parte 1
            elif coluna_identificador == "advogado_parte2":
                advogado_parte2 = coluna_informacao
                print('- Advogado da parte 2: ', advogado_parte2)

                if "nao_preenchido" in advogado_parte2:
                    break
                else:
                    campo_nome_advogado = WebDriverWait(driver, self.delay).until(
                        EC.presence_of_element_located((By.NAME, 'formulario:nomeAdvogadoReclamado')))
                    campo_nome_advogado.send_keys(advogado_parte2)
                    # Tempo de controle
                    time.sleep(1)
                    btn_add = WebDriverWait(driver, self.delay).until(
                        EC.element_to_be_clickable((By.ID, 'formulario:incluirAdvogadoReclamado')))
                    btn_add.click()
                    self.objTools.aguardar_carregamento(driver)
                    break

    def salvar(self, driver):
        btn_salvar = WebDriverWait(driver, self.delay).until(
            EC.presence_of_element_located((By.ID, 'formulario:salvar')))
        btn_salvar.click()

    def aba_parametros_calculo(self, driver):
        selecionar_aba = WebDriverWait(driver, self.delay).until(
            EC.presence_of_element_located((By.ID, 'formulario:tabParametrosCalculo_lbl')))
        selecionar_aba.click()

    def preencher_estado_municipio(self, driver):

        for i in range(len(self.planilha_base)):

            coluna_identificador = self.planilha_base.loc[i, 'IDENTIFICADOR']
            coluna_informacao = self.planilha_base.loc[i, 'INFORMACAO']

            # Condição para pular as linhas em branco da coluna Identificador na planilha base
            if type(coluna_identificador) == type(self.var_controle_float):
                continue
            elif coluna_identificador == "uf":
                uf = coluna_informacao
                print('- Estado: ', uf)
                if "nao_preenchido" in uf:
                    break
                else:
                    # Selecionar o Estado
                    selecionar_estado = WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.NAME, 'formulario:estado')))
                    selecao = Select(selecionar_estado)
                    selecao.select_by_visible_text(uf)
                    # Tempo de controle
                    time.sleep(1)
            elif coluna_identificador == "municipio":
                cidade = coluna_informacao
                cidade = unidecode.unidecode(cidade)
                # print('- Município: ', cidade)
                cidade = cidade.strip()
                print('- Município: ', cidade)
                selecionar_municipio = WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.ID, 'formulario:municipio')))
                selecao2 = Select(selecionar_municipio)
                selecao2.select_by_visible_text(cidade)

    def preencher_datas_calculo(self, driver):

        for i in range(len(self.planilha_base)):

            coluna_identificador = self.planilha_base.loc[i, 'IDENTIFICADOR']
            coluna_informacao = self.planilha_base.loc[i, 'INFORMACAO']

            # Condição para pular as linhas em branco da coluna Identificador na planilha base
            if type(coluna_identificador) == type(self.var_controle_float):
                # print('* Pulando linhas em branco ...')
                continue
            elif coluna_identificador == "data_admissao":
                data_admissao = coluna_informacao
                if type(data_admissao) == type(self.var_controle_int):
                    data_admissao = xlrd.xldate_as_datetime(data_admissao, 0)
                    self.datetime_admissao = data_admissao
                    data_admissao = data_admissao.strftime('%d/%m/%Y')
                    # Preencher Data de Admissão
                    campo_admissao = WebDriverWait(driver, self.delay).until(
                        EC.presence_of_element_located((By.NAME, 'formulario:dataAdmissaoInputDate')))
                    campo_admissao.send_keys(data_admissao)
                else:
                    data_admissao = ''
                print('- Data de Admissão: ', data_admissao)

            elif coluna_identificador == "data_rescisao":
                data_rescisao = coluna_informacao
                if type(data_rescisao) == type(self.var_controle_int):
                    data_rescisao = xlrd.xldate_as_datetime(data_rescisao, 0)
                    # Coletar data no formato datetime para criar condição no Histórico Salarial
                    self.datetime_demissao = data_rescisao
                    data_rescisao = data_rescisao.strftime('%d/%m/%Y')
                    # Preencher Data de Demissão
                    campo_demissao = WebDriverWait(driver, self.delay).until(
                        EC.presence_of_element_located((By.NAME, 'formulario:dataDemissaoInputDate')))
                    campo_demissao.send_keys(data_rescisao)
                else:
                    data_rescisao = ''
                    pass
                print('- Data de Rescisão: ', data_rescisao)

            elif coluna_identificador == "data_ajuizamento":
                data_ajuizamento = coluna_informacao
                if type(data_ajuizamento) == type(self.var_controle_int):
                    data_ajuizamento = xlrd.xldate_as_datetime(data_ajuizamento, 0)
                    # data_ajuizamento = datetime.fromordinal(datetime(1900, 1, 1).toordinal() + data_ajuizamento - 2)
                    # if type(data_ajuizamento) == type(self.var_controle_date):
                    data_ajuizamento = data_ajuizamento.strftime('%d/%m/%Y')
                    # Preencher Data de Ajuizamento
                    campo_ajuizamento = WebDriverWait(driver, self.delay).until(
                        EC.presence_of_element_located((By.NAME, 'formulario:dataAjuizamentoInputDate')))
                    campo_ajuizamento.send_keys(data_ajuizamento)
                else:
                    data_ajuizamento = ''
                print('- Data de Ajuizamento: ', data_ajuizamento)
        return self.datetime_admissao, self.datetime_demissao

    def limitar_calculo(self, driver):

        for i in range(len(self.planilha_base)):

            coluna_identificador = self.planilha_base.loc[i, 'IDENTIFICADOR']
            coluna_informacao = self.planilha_base.loc[i, 'INFORMACAO']

            # Condição para pular as linhas em branco da coluna Identificador na planilha base
            if type(coluna_identificador) == type(self.var_controle_float):
                # print('* Pulando linhas em branco ...')
                continue
            elif coluna_identificador == "inicio_calculo":
                inicio_calculo = coluna_informacao
                if type(inicio_calculo) == type(self.var_controle_int):
                    inicio_calculo = xlrd.xldate_as_datetime(inicio_calculo, 0)
                    self.datetime_inicio_calc = inicio_calculo
                    inicio_calculo = inicio_calculo.strftime('%d/%m/%Y')
                    # Preecher Data Inicial
                    campo_data_inicial = WebDriverWait(driver, self.delay).until(
                        EC.presence_of_element_located((By.NAME, 'formulario:dataInicioCalculoInputDate')))
                    campo_data_inicial.send_keys(inicio_calculo)
                else:
                    inicio_calculo = ''
                print('- Início Cálculo: ', inicio_calculo)

            elif coluna_identificador == "termino_calculo":
                termino_calculo = coluna_informacao

                if type(termino_calculo) == type(self.var_controle_int):
                    termino_calculo = xlrd.xldate_as_datetime(termino_calculo, 0)
                    # Coletar data no formato datetime para criar condição no Histórico Salarial
                    self.datetime_final_calc = termino_calculo
                    termino_calculo = termino_calculo.strftime('%d/%m/%Y')
                    # Preencher Data Final
                    campo_data_final = WebDriverWait(driver, self.delay).until(
                        EC.presence_of_element_located((By.NAME, 'formulario:dataTerminoCalculoInputDate')))
                    campo_data_final.send_keys(termino_calculo)
                else:
                    termino_calculo = ''
                print('- Término Cálculo: ', termino_calculo)
            # break
        return self.datetime_inicio_calc, self.datetime_final_calc

    def aplicar_prescricao_verbas_fgts(self, driver):

        for i in range(len(self.planilha_base)):

            coluna_identificador = self.planilha_base.loc[i, 'IDENTIFICADOR']
            coluna_informacao = self.planilha_base.loc[i, 'INFORMACAO']

            # Condição para pular as linhas em branco da coluna Identificador na planilha base
            if type(coluna_identificador) == type(self.var_controle_float):
                # print('* Pulando linhas em branco ...')
                continue
            elif coluna_identificador == "aplicar_prescricao_verbas":
                self.aplicar_prescricao_verbas = coluna_informacao
                print('- Aplicar Prescrição - Verbas - ', self.aplicar_prescricao_verbas)
            elif coluna_identificador == "aplicar_prescricao_FGTS":
                self.aplicar_prescricao_FGTS = coluna_informacao
                print('- Aplicar Prescrição - FGTS: ', self.aplicar_prescricao_FGTS)

        if self.aplicar_prescricao_verbas == 'True':
            campo_verbas = WebDriverWait(driver, self.delay).until(
                EC.element_to_be_clickable((By.ID, 'formulario:prescricaoQuinquenal')))
            checkbox_verbas = campo_verbas.is_selected()
            if checkbox_verbas:
                print('- Checkbox - Verbas (Quinquenal) - Já Habilitado.')
            else:
                print('- Checkbox - Verbas (Quinquenal) - Foi Habilitado.')
                campo_verbas.click()

        elif self.aplicar_prescricao_verbas == 'False':
            campo_verbas = WebDriverWait(driver, self.delay).until(
                EC.element_to_be_clickable((By.ID, 'formulario:prescricaoQuinquenal')))
            checkbox_verbas = campo_verbas.is_selected()
            if checkbox_verbas:
                print('- Checkbox - Verbas (Quinquenal) - Foi Desabilitado.')
                campo_verbas.click()

        if self.aplicar_prescricao_FGTS == 'True':
            campo_fgts = WebDriverWait(driver, self.delay).until(
                EC.element_to_be_clickable((By.ID, 'formulario:prescricaoFgts')))
            checkbox_fgts = campo_fgts.is_selected()
            if checkbox_fgts:
                print('- Checkbox - FGTS - Já Habilitado.')
            else:
                print('- Checkbox - FGTS - Foi Habilitado.')
                checkbox_fgts.click()
        elif self.aplicar_prescricao_FGTS == 'False':
            campo_fgts = WebDriverWait(driver, self.delay).until(
                EC.element_to_be_clickable((By.ID, 'formulario:prescricaoFgts')))
            checkbox_fgts = campo_fgts.is_selected()
            if checkbox_fgts:
                print('- Checkbox - FGTS - Foi Desabilitado.')
                checkbox_fgts.click()

    def selecionar_regime_trabalho(self, driver):

        for i in range(len(self.planilha_base)):

            coluna_identificador = self.planilha_base.loc[i, 'IDENTIFICADOR']
            coluna_informacao = self.planilha_base.loc[i, 'INFORMACAO']

            # Condição para pular as linhas em branco da coluna Identificador na planilha base
            if type(coluna_identificador) == type(self.var_controle_float):
                # print('* Pulando linhas em branco ...')
                continue
            elif coluna_identificador == "regime_trabalho":
                regime_trabalho = coluna_informacao
                print('- Regime de Trabalho: ', regime_trabalho)
                # Preencher PJeCalc
                opcao = WebDriverWait(driver, self.delay).until(
                    EC.presence_of_element_located((By.NAME, 'formulario:tipoDaBaseTabelada')))
                selecionar_opcao = Select(opcao)
                selecionar_opcao.select_by_visible_text(regime_trabalho)

    def selecionar_prazo_aviso_previo(self, driver):

        for i in range(len(self.planilha_base)):

            coluna_identificador = self.planilha_base.loc[i, 'IDENTIFICADOR']
            coluna_informacao = self.planilha_base.loc[i, 'INFORMACAO']

            # Condição para pular as linhas em branco da coluna Identificador na planilha base
            if type(coluna_identificador) == type(self.var_controle_float):
                # print('* Pulando linhas em branco ...')
                continue
            elif coluna_identificador == "prazo_de_aviso_previo":
                self.prazo_de_aviso_previo = coluna_informacao
                print('- Prazo de Aviso Prévio: ', self.prazo_de_aviso_previo)
                # Preencher PJeCalc
                campo_prazo_aviso_previo = WebDriverWait(driver, self.delay).until(
                    EC.presence_of_element_located((By.NAME, 'formulario:apuracaoPrazoDoAvisoPrevio')))
                selecionar = Select(campo_prazo_aviso_previo)
                selecionar.select_by_visible_text(self.prazo_de_aviso_previo)

            elif coluna_identificador == "quantidade_dias_aviso_previo":
                self.quantidade_dias_aviso_previo = coluna_informacao
                print('- Quantidade de dias de aviso prévio: ', self.quantidade_dias_aviso_previo)

        # time.sleep(2)
        if self.prazo_de_aviso_previo == 'Informado':
            # Aguardar o campo condicional aparecer
            # aguardar_campo_quantidade()

            WebDriverWait(driver, self.delay).until(
                EC.visibility_of_element_located((By.NAME, 'formulario:prazoAvisoInformado')))

            # time.sleep(2)
            quantidade = WebDriverWait(driver, self.delay).until(
                EC.presence_of_element_located((By.NAME, 'formulario:prazoAvisoInformado')))
            quantidade.click()
            quantidade.send_keys(self.quantidade_dias_aviso_previo)

    def checkboxs(self, driver):

        for i in range(len(self.planilha_base)):

            coluna_identificador = self.planilha_base.loc[i, 'IDENTIFICADOR']
            coluna_informacao = self.planilha_base.loc[i, 'INFORMACAO']

            # Condição para pular as linhas em branco da coluna Identificador na planilha base
            if type(coluna_identificador) == type(self.var_controle_float):
                # print('* Pulando linhas em branco ...')
                continue
            elif coluna_identificador == "projetar_aviso_previo_indenizado":
                self.projetar_aviso_previo_indenizado = coluna_informacao
                print('- Projetar Aviso Prévio Indenizado: ', self.projetar_aviso_previo_indenizado)
            elif coluna_identificador == "limitar_avos_ao_periodo_do_calculo":
                self.limitar_avos_ao_periodo_do_calculo = coluna_informacao
                print('- Limitar Avos ao Período do Cálculo: ', self.limitar_avos_ao_periodo_do_calculo)
            elif coluna_identificador == "zerar_valor_negativo_padrao":
                self.zerar_valor_negativo_padrao = coluna_informacao
                print('- Zerar Valor Negativo (Padrão): ', self.zerar_valor_negativo_padrao)
            elif coluna_identificador == "considerar_feriados_estaduais":
                self.considerar_feriados_estaduais = coluna_informacao
                print('- Considerar Feriados Estaduais: ', self.considerar_feriados_estaduais)
            elif coluna_identificador == "considerar_feriados_municipais":
                self.considerar_feriados_municipais = coluna_informacao
                print('- Considerar Feriados Municipais: ', self.considerar_feriados_municipais)

        if self.projetar_aviso_previo_indenizado == 'True':
            campo_projetar = WebDriverWait(driver, self.delay).until(
                EC.element_to_be_clickable((By.ID, 'formulario:projetaAvisoIndenizado')))
            checkbox_projetar = campo_projetar.is_selected()
            # Condição para verificar se o checkbox está habilitador
            if checkbox_projetar:
                print('- Checkbox - Projetar Aviso Prévio Indenizado - Já Habilitado.')
            else:
                print('- Checkbox - Projetar Aviso Prévio Indenizado - Foi Habilitado.')
                campo_projetar.click()
        elif self.projetar_aviso_previo_indenizado == 'False':
            campo_projetar = WebDriverWait(driver, self.delay).until(
                EC.element_to_be_clickable((By.ID, 'formulario:projetaAvisoIndenizado')))
            checkbox_projetar = campo_projetar.is_selected()
            if checkbox_projetar:
                print('- Checkbox - Projetar Aviso Prévio Indenizado - Foi Desabilitado.')
                campo_projetar.click()

        if self.limitar_avos_ao_periodo_do_calculo == 'True':
            campo_limitar = WebDriverWait(driver, self.delay).until(
                EC.element_to_be_clickable((By.ID, 'formulario:limitarAvos')))
            checkbox_limitar = campo_limitar.is_selected()
            if checkbox_limitar:
                print('- Checkbox - Limitar Avos ao Período do Cálculo - Já Habilitado.')
            else:
                print('- Checkbox - Limitar Avos ao Período do Cálculo - Foi Habilitado.')
                campo_limitar.click()
        elif self.limitar_avos_ao_periodo_do_calculo == 'False':
            try:
                campo_limitar = WebDriverWait(driver, self.delay).until(
                    EC.element_to_be_clickable((By.ID, 'formulario:limitarAvos')))
                checkbox_limitar = campo_limitar.is_selected()
                if checkbox_limitar:
                    print('- Checkbox - Limitar Avos ao Período do Cálculo - Foi Desabilitado.')
                    checkbox_limitar.click()
            except TimeoutException:
                print("- Checkbox - 'Limitar Avos ao Período do Cálculo' - Desativado")

        if self.zerar_valor_negativo_padrao == 'True':
            zerar_val_negativo = WebDriverWait(driver, self.delay).until(
                EC.element_to_be_clickable((By.ID, 'formulario:zeraValorNegativo')))
            checkbox_zerar = zerar_val_negativo.is_selected()
            if checkbox_zerar:
                print('- Checkbox - Zerar Valor Negativo (Padrão) - Já Habilitado.')
            else:
                print('- Checkbox - Zerar Valor Negativo (Padrão) - Foi Habilitado.')
                zerar_val_negativo.click()
        elif self.zerar_valor_negativo_padrao == 'False':
            zerar_val_negativo = WebDriverWait(driver, self.delay).until(
                EC.element_to_be_clickable((By.ID, 'formulario:zeraValorNegativo')))
            checkbox_zerar = zerar_val_negativo.is_selected()
            if checkbox_zerar:
                print('- Checkbox - Zerar Valor Negativo (Padrão) - Foi Desabilitado.')
                zerar_val_negativo.click()

        if self.considerar_feriados_estaduais == 'True':
            considerar_estaduais = WebDriverWait(driver, self.delay).until(
                EC.element_to_be_clickable((By.ID, 'formulario:consideraFeriadoEstadual')))
            checkbox_estaduais = considerar_estaduais.is_selected()
            if checkbox_estaduais:
                print('- Checkbox - Considerar Feriados Estaduais - Já Habilitado.')
            else:
                print('- Checkbox - Considerar Feriados Estaduais - Foi Habilitado.')
                considerar_estaduais.click()
        elif self.considerar_feriados_estaduais == 'False':
            considerar_estaduais = WebDriverWait(driver, self.delay).until(
                EC.element_to_be_clickable((By.ID, 'formulario:consideraFeriadoEstadual')))
            checkbox_estaduais = considerar_estaduais.is_selected()
            if checkbox_estaduais:
                print('- Checkbox - Considerar Feriados Estaduais - Foi Desabilitado.')
                considerar_estaduais.click()

        if self.considerar_feriados_municipais == 'True':
            considerar_municipais = WebDriverWait(driver, self.delay).until(
                EC.element_to_be_clickable((By.ID, 'formulario:consideraFeriadoMunicipal')))
            checkbox_municipais = considerar_municipais.is_selected()
            if checkbox_municipais:
                print('- Checkbox - Considerar Feriados Municipais - Já Habilitado.')
            else:
                print('- Checkbox - Considerar Feriados Municipais - Foi Habilitado.')
                considerar_municipais.click()
        elif self.considerar_feriados_municipais == 'False':
            considerar_municipais = WebDriverWait(driver, self.delay).until(
                EC.element_to_be_clickable((By.ID, 'formulario:consideraFeriadoMunicipal')))
            checkbox_municipais = considerar_municipais.is_selected()
            if checkbox_municipais:
                print('- Checkbox - Considerar Feriados Municipais - Foi Desabilitado.')
                considerar_municipais.click()

    def preencher_maior_ultima_remuneracao(self, driver):

        for i in range(len(self.planilha_base)):

            coluna_identificador = self.planilha_base.loc[i, 'IDENTIFICADOR']
            coluna_informacao = self.planilha_base.loc[i, 'INFORMACAO']

            # Condição para pular as linhas em branco da coluna Identificador na planilha base
            if type(coluna_identificador) == type(self.var_controle_float):
                # print('* Pulando linhas em branco ...')
                continue
            elif coluna_identificador == "maior_remuneracao":
                maior_remuneracao = coluna_informacao
                print("- Maior Remuneração: ", maior_remuneracao)
                # Preencher Maior Remuneração
                if maior_remuneracao != '<nao_preenchido>':
                    maior = WebDriverWait(driver, self.delay).until(
                        EC.presence_of_element_located((By.NAME, 'formulario:valorMaiorRemuneracao')))
                    maior_remuneracao_new = f"{maior_remuneracao:.2f}"
                    maior.send_keys(maior_remuneracao_new)

            elif coluna_identificador == "ultima_remuneracao":
                ultima_remuneracao = coluna_informacao
                print("- Última Remuneração: ", ultima_remuneracao)
                if ultima_remuneracao != '<nao_preenchido>':
                    ultima = WebDriverWait(driver, self.delay).until(
                        EC.presence_of_element_located((By.NAME, 'formulario:valorUltimaRemuneracao')))
                    ultima_remuneracao_new = f"{ultima_remuneracao:.2f}"
                    ultima.send_keys(ultima_remuneracao_new)

    def preencher_cargaHoraria(self, driver):

        for i in range(len(self.planilha_base)):

            coluna_identificador = self.planilha_base.loc[i, 'IDENTIFICADOR']
            coluna_informacao = self.planilha_base.loc[i, 'INFORMACAO']

            # Condição para pular as linhas em branco da coluna Identificador na planilha base
            if type(coluna_identificador) == type(self.var_controle_float):
                # print('* Pulando linhas em branco ...')
                continue
            elif coluna_identificador == "carga_horaria":
                carga_horaria = coluna_informacao
                print('- Carga Horária: ', carga_horaria)
                # Converter formato do valor
                if carga_horaria != '-':
                    valor_carga_horaria = '{:.2f}'.format(carga_horaria)
                    campo_carga_horaria = WebDriverWait(driver, self.delay).until(
                        EC.presence_of_element_located((By.NAME, 'formulario:valorCargaHorariaPadrao')))
                    campo_carga_horaria.send_keys(valor_carga_horaria)
                break

    def sabadoUtil(self, driver):

        for i in range(len(self.planilha_base)):

            coluna_identificador = self.planilha_base.loc[i, 'IDENTIFICADOR']
            coluna_informacao = self.planilha_base.loc[i, 'INFORMACAO']

            # Condição para pular as linhas em branco da coluna Identificador na planilha base
            if type(coluna_identificador) == type(self.var_controle_float):
                # print('* Pulando linhas em branco ...')
                continue
            elif coluna_identificador == "sabado_como_dia_util":
                self.sabado_como_dia_util = coluna_informacao
                print('- Sábado como Dia Útil: ', self.sabado_como_dia_util)
                break

        if self.sabado_como_dia_util == 'True':
            campo_sabado_util = WebDriverWait(driver, self.delay).until(
                EC.element_to_be_clickable((By.ID, 'formulario:sabadoDiaUtil')))
            checkbox_sabado = campo_sabado_util.is_selected()
            if checkbox_sabado:
                print('- Checkbox - Sábado como Dia Útil - Já Habilitado.')
            else:
                print('- Checkbox - Sábado como Dia Útil - Foi Habilitado.')
                campo_sabado_util.click()
        elif self.sabado_como_dia_util == 'False':
            campo_sabado_util = WebDriverWait(driver, self.delay).until(
                EC.element_to_be_clickable((By.ID, 'formulario:sabadoDiaUtil')))
            checkbox_sabado = campo_sabado_util.is_selected()
            if checkbox_sabado:
                print('- Checkbox - Sábado como Dia Útil - Foi Desabilitado.')
                campo_sabado_util.click()

    def remover_ponto_facultativo_carnaval(self, driver):

        # try:
        #     elements = WebDriverWait(driver, self.delay).until(EC.presence_of_all_elements_located((By.XPATH, '//tbody[@id="formulario:listagemPontosFacultativos:tb"]//td[2][@class="rich-table-cell "]')))
        #     for indice, value in enumerate(reversed(elements)):
        #
        #         if 'CARNAVAL' in value.get_attribute('textContent'):
        #             print(f"- [{indice}] {value.get_attribute('textContent')}")
        #             WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.XPATH, f'//a[@id="formulario:listagemPontosFacultativos:{indice}:excluirPontoFacultativo"]'))).click()
        #             self.objTools.aguardar_carregamento(driver)
        #             break
        # except Exception as e:
        #     print(f"- [except][remover_ponto_facultativo_carnaval]: {e}")


        # PAREI_AQUI
        try:
            # Aguarda até que os elementos da tabela estejam visíveis
            elementos = WebDriverWait(driver, self.delay).until(EC.presence_of_all_elements_located((By.XPATH, '//tr[contains(@class, "rich-table-row")]')))

            # Itera sobre os elementos encontrados para verificar se contêm o texto "CORPUS CHRISTI"
            for indice, elemento in enumerate(elementos):
                # Procura pela célula que contém o texto
                celula_texto = elemento.find_element(By.XPATH, './td[contains(@class, "rich-table-cell")][2]')  # Índice [2] refere-se à segunda célula <td>
                print(f"{indice}) - {celula_texto.text}")
                if celula_texto.text == "CARNAVAL":
                    print(f"- [LOCALIZADO]: {indice}) - {celula_texto.text}")
                    # Encontra o link para clicar baseado no id do primeiro elemento <td>
                    link_para_clicar = elemento.find_element(By.XPATH, f'./td[@id="formulario:listagemPontosFacultativos:{indice}:j_id578"]/a[contains(@class, "linkExcluir")]')
                    link_para_clicar.click()
                    break
        except Exception as e:
            print(f"- [except][remover_ponto_facultativo_carnaval]: {e}")

    def remover_ponto_facultativo_corpus_christi(self, driver):

        # try:
        #     elements = WebDriverWait(driver, self.delay).until(EC.presence_of_all_elements_located((By.XPATH, '//tbody[@id="formulario:listagemPontosFacultativos:tb"]//td[2][@class="rich-table-cell "]')))
        #     for indice, value in enumerate(reversed(elements)):
        #         if 'CORPUS CHRISTI' in value.get_attribute('textContent'):
        #             print(f"- [{indice}] {value.get_attribute('textContent')}")
        #             WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.XPATH, f'//a[@id="formulario:listagemPontosFacultativos:{indice}:excluirPontoFacultativo"]'))).click()
        #             self.objTools.aguardar_carregamento(driver)
        #             break
        # except Exception as e:
        #     print(f"- [except][remover_ponto_facultativo_corpus_christi]: {e}")


        # PAREI_AQUI
        try:
            # Aguarda até que os elementos da tabela estejam visíveis
            elementos = WebDriverWait(driver, self.delay).until(EC.presence_of_all_elements_located((By.XPATH, '//tr[contains(@class, "rich-table-row")]')))

            # Itera sobre os elementos encontrados para verificar se contêm o texto "CORPUS CHRISTI"
            for indice, elemento in enumerate(elementos):
                # Procura pela célula que contém o texto
                celula_texto = elemento.find_element(By.XPATH, './td[contains(@class, "rich-table-cell")][2]')  # Índice [2] refere-se à segunda célula <td>
                print(f"{indice}) - {celula_texto.text}")
                if celula_texto.text == "CORPUS CHRISTI":
                    print(f"- [LOCALIZADO]: {indice}) - {celula_texto.text}")
                    # Encontra o link para clicar baseado no id do primeiro elemento <td>
                    link_para_clicar = elemento.find_element(By.XPATH, f'./td[@id="formulario:listagemPontosFacultativos:{indice}:j_id578"]/a[contains(@class, "linkExcluir")]')
                    link_para_clicar.click()
                    break
        except Exception as e:
            print(f"- [except][remover_ponto_facultativo_corpus_christi]: {e}")

    def remover_ponto_facultativo_sexta_santa(self, driver):

        # try:
        #     elements = WebDriverWait(driver, self.delay).until(EC.presence_of_all_elements_located((By.XPATH, '//tbody[@id="formulario:listagemPontosFacultativos:tb"]//td[2][@class="rich-table-cell "]')))
        #     for indice, value in enumerate(reversed(elements)):
        #         if 'SEXTA-FEIRA SANTA' in value.get_attribute('textContent'):
        #             print(f"- [{indice}] {value.get_attribute('textContent')}")
        #             WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.XPATH, f'//a[@id="formulario:listagemPontosFacultativos:{indice}:excluirPontoFacultativo"]'))).click()
        #             self.objTools.aguardar_carregamento(driver)
        #             break
        # except Exception as e:
        #     print(f"- [except][remover_ponto_facultativo_sexta_santa]: {e}")

        # PAREI_AQUI
        try:
            # Aguarda até que os elementos da tabela estejam visíveis
            elementos = WebDriverWait(driver, self.delay).until(EC.presence_of_all_elements_located((By.XPATH, '//tr[contains(@class, "rich-table-row")]')))

            # Itera sobre os elementos encontrados para verificar se contêm o texto "CORPUS CHRISTI"
            for indice, elemento in enumerate(elementos):
                # Procura pela célula que contém o texto
                celula_texto = elemento.find_element(By.XPATH, './td[contains(@class, "rich-table-cell")][2]')  # Índice [2] refere-se à segunda célula <td>
                print(f"{indice}) - {celula_texto.text}")
                if celula_texto.text == "SEXTA-FEIRA SANTA":
                    print(f"- [LOCALIZADO]: {indice}) - {celula_texto.text}")
                    # Encontra o link para clicar baseado no id do primeiro elemento <td>
                    link_para_clicar = elemento.find_element(By.XPATH, f'./td[@id="formulario:listagemPontosFacultativos:{indice}:j_id578"]/a[contains(@class, "linkExcluir")]')
                    link_para_clicar.click()
                    break
        except Exception as e:
            print(f"- [except][remover_ponto_facultativo_sexta_santa]: {e}")

    def definir_ponto_facultativo(self, driver):

        planilha = pd.read_excel(self.source, sheet_name="PJE-DIV", header=1)
        # Ponto Facultativo
        cidade = planilha.iloc[0, 0]  # A3
        sexta_feira_santa = planilha.iloc[0, 1]  # B3
        corpus_christi = planilha.iloc[0, 2]  # C3
        carnaval = planilha.iloc[0, 3]  # D3

        print("- Ponto Facultativo: ", cidade, " - ", sexta_feira_santa, carnaval, corpus_christi)
        if sexta_feira_santa == "FALSE":
            self.remover_ponto_facultativo_sexta_santa(driver)

        if corpus_christi == "FALSE":
            self.remover_ponto_facultativo_corpus_christi(driver)

        if carnaval == "FALSE":
            self.remover_ponto_facultativo_carnaval(driver)

    def preencher_comentarios(self, driver):

        for i in range(len(self.planilha_base)):

            coluna_identificador = self.planilha_base.loc[i, 'IDENTIFICADOR']
            coluna_informacao = self.planilha_base.loc[i, 'INFORMACAO']

            # Condição para pular as linhas em branco da coluna Identificador na planilha base
            if type(coluna_identificador) == type(self.var_controle_float):
                # print('* Pulando linhas em branco ...')
                continue
            elif coluna_identificador == "comentarios_parametros":
                comentarios_parametros = coluna_informacao
                print('- Comentários: ', comentarios_parametros)
                if comentarios_parametros == "<nao_preenchido>":
                    break
                else:
                    # Preencher PJeCalc
                    comentarios = WebDriverWait(driver, self.delay).until(
                        EC.presence_of_element_located((By.NAME, 'formulario:comentarios')))
                    comentarios.send_keys(comentarios_parametros)
                    break

    def main_dados_calculo(self, driver):

        # objeto_dados = DadosCalculo()
        dados_processo = self.identificacao_processo(driver)
        id_processo = dados_processo[0]
        numero_processo = dados_processo[1]
        # Tempo de Controle
        time.sleep(self.delayG)
        self.preencher_valor_causa(driver)
        # Tempo de Controle
        time.sleep(self.delayG)
        nome_reclamente = self.preencher_nome_reclamante(driver)
        # Tempo de controle
        time.sleep(self.delayG)
        self.preencher_documento_reclamente(driver)
        # Tempo de controle
        time.sleep(self.delayG)
        self.preencher_advogado(driver)
        # Tempo de controle
        time.sleep(self.delayG)
        self.preencher_reclamado(driver)
        # Tempo de Controle
        time.sleep(self.delayG)
        self.preencher_advogado_parte2(driver)
        # Tempo de Controle
        time.sleep(self.delayG)
        # Parâmetros do Cálculo
        self.aba_parametros_calculo(driver)
        # Tempo de controle
        time.sleep(self.delayG)
        self.preencher_estado_municipio(driver)
        # Tempo de controle
        time.sleep(self.delayG)
        datas = self.preencher_datas_calculo(driver)
        admissao = datas[0]
        rescisao = datas[1]
        # Tempo de controle
        time.sleep(self.delayG)
        escopo_calc = self.limitar_calculo(driver)
        inicio_calculo = escopo_calc[0]
        termino_calculo = escopo_calc[1]
        # Tempo de controle
        time.sleep(self.delayG)
        self.aplicar_prescricao_verbas_fgts(driver)
        # Tempo de controle
        time.sleep(self.delayG)
        self.selecionar_regime_trabalho(driver)
        # Tempo de controle
        time.sleep(self.delayG)
        self.selecionar_prazo_aviso_previo(driver)
        # Tempo de controle
        time.sleep(self.delayG)
        self.checkboxs(driver)
        # Tempo de controle
        time.sleep(self.delayG)
        self.preencher_maior_ultima_remuneracao(driver)
        # Tempo de controle
        time.sleep(self.delayG)
        self.preencher_cargaHoraria(driver)
        # Tempo de controle
        time.sleep(self.delayG)
        self.sabadoUtil(driver)
        # Tempo de controle
        time.sleep(self.delayG)
        # Somente para versão v.34 da planilha base
        self.definir_ponto_facultativo(driver)
        # Tempo de controle
        time.sleep(self.delayG)
        self.preencher_comentarios(driver)
        # Tempo de controle
        time.sleep(self.delayG)
        self.salvar(driver)
        self.objTools.aguardar_carregamento(driver)
        time.sleep(self.delayG)
        self.salvar(driver)
        # Aguardar Processamento
        self.objTools.aguardar_carregamento(driver)
        time.sleep(self.delayG)
        self.verificacao_new(driver)
        print('# ========== [DADOS_CALCULO] ========== #')

        # [Limpar_arquivos_temporarios]
        self.objTools.limparFilesTemp()

        return nome_reclamente, id_processo, admissao, rescisao, inicio_calculo, termino_calculo, numero_processo
