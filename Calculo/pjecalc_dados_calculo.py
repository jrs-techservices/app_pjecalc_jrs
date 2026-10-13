from Tools.pendencias import de_relatorio, registrar
import os
import gc
import re
import xlrd
import shutil
import unidecode
import unicodedata
import pandas as pd
import pyautogui as pa
from time import sleep
from datetime import datetime
from Tools.pjecalc_control import Control
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.alert import Alert
from selenium.common.exceptions import NoAlertPresentException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait, TimeoutException
from selenium.webdriver.common.keys import Keys
from Calculo.leitura_planilha import (valor_vazio, data_da_planilha, booleano_da_planilha, numero_da_planilha,
                                      documento_da_planilha, opcao_de_municipio, ler_pje_bd)


class DadosCalculo:


    def __init__(self, source):
        self.source = source
        self.planilha_base = ler_pje_bd(source)
        self.tamanho_planilha_base = len(self.planilha_base)
        self.objTools = Control()
        self.delay = 5
        self.delayG = 1.5
        self.delayDefault = 0.5
        self.qtdTentativas = 3
        self.local = ""
        self.mensagem_erro = ""
        self.datetime_admissao = ""
        self.datetime_demissao = ""
        self.datetime_inicio_calc = ""
        self.datetime_final_calc = ""
        self.var_controle_int = 1
        self.var_controle_float = 1.1
        self.var_controle_string = "Em branco"
        self.var_controle_date = datetime.now()
        self.numero_processo = ""
        self.processo = ""
        self.valor_da_causa = ""
        self.nome_parte1 = ""
        self.nome_parte2 = ""
        self.doc_parte2 = ""
        self.prazo_de_aviso_previo = ""
        self.quantidade_dias_aviso_previo = ""
        self.aplicar_prescricao_verbas = ""
        self.aplicar_prescricao_FGTS = ""
        self.projetar_aviso_previo_indenizado = ""
        self.limitar_avos_ao_periodo_do_calculo = ""
        self.zerar_valor_negativo_padrao = ""
        self.considerar_feriados_estaduais = ""
        self.considerar_feriados_municipais = ""
        self.sabado_como_dia_util = ""
        self.id_processo = ""


    def limparFiles(self):
        # Zerar arquivos (log.txt e source_plan.txt)
        l = open(os.getcwd() + "\log.txt", "w")
        l.close()
        s = open(os.getcwd() + "\source_plan.txt", "w")
        s.close()

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
        sleep(5)
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
                de_relatorio("Dados do Cálculo", erroUtil[0])
            # driver.close()
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
                de_relatorio('Dados do Cálculo')
        except TimeoutException:
            print('- [Except][Dados Cálculo] - Elemento não encontrado/A Página demorou para responder. Encerrando...')

        # Tempo de controle
        sleep(2)


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

        if os.environ.get("PJECALC_SERVICO") == "1":
            # Pelo serviço o log fica no painel e na API; o .txt ao lado da planilha seria redundante.
            open(os.getcwd() + '\log.txt', 'w').close()
            return

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


    # source_txt = os.getcwd() + '\source_plan.txt'
    # f = open(source_txt, "r")
    # arquivo = f.read()

    def get_id_processo(self):

        for indice, identificador in enumerate(self.planilha_base['IDENTIFICADOR']):

            # [TRATAR_VALORES_EM_BRANCO]
            if not pd.isna(identificador):

                if 'id_processo' in identificador:
                    try:
                        informacao = self.planilha_base.loc[indice, 'INFORMACAO']
                        print(f"- [CHAVE]: {identificador} | VALOR: {informacao}")
                        if isinstance(informacao, int):
                            informacao = str(informacao)
                        if valor_vazio(informacao):
                            print("- [ID_PROCESSO_DEVE_SER_PREENCHIDO]")
                            return [False, f'[id_numero][{informacao}]']
                        else:
                            self.id_processo = informacao
                            print(f'- [ID_PROCESSO]: {self.id_processo}')
                            return [True, '']
                    except Exception as e:
                        msg = f"[except][get_id_processo]: {e}"
                        print(f"- {msg}")
                        return [False, msg]
            else:
                continue
        else:
            msg = "[não informado: mantido o padrão do PJe-Calc][get_id_processo]"
            print(f"- {msg}")
            return [False, msg]

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

    def digitar_numeroProcesso(self, driver, value):

        for _ in range(self.qtdTentativas):
            try:
                field = WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.XPATH, '//input[@id="formulario:numero"]')))
                field.send_keys(value)
                print("- [NUMERO_PROCESSO]: [OK]")
                return [True, '']
            except Exception as e:
                print(f"- [except][digitar_numeroProcesso]: {e}")
                sleep(1)
        else:
            msg = "[tentativas_esgotadas][digitar_numeroProcesso]"
            print(f"- {msg}")
            return [False, msg]

    def digitar_digitoProcesso(self, driver, value):

        for _ in range(self.qtdTentativas):
            try:
                field = WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.XPATH, '//input[@id="formulario:digito"]')))
                field.send_keys(value)
                print("- [DIGITO_PROCESSO]: [OK]")
                return [True, '']
            except Exception as e:
                print(f"- [except][digitar_digitoProcesso]: {e}")
                sleep(1)
        else:
            msg = "[tentativas_esgotadas][digitar_digitoProcesso]"
            print(f"- {msg}")
            return [False, msg]
            
    def digitar_anoProcesso(self, driver, value):

        for _ in range(self.qtdTentativas):
            try:
                field = WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.XPATH, '//input[@id="formulario:ano"]')))
                field.send_keys(value)
                print("- [ANO_PROCESSO]: [OK]")
                return [True, '']
            except Exception as e:
                print(f"- [except][digitar_anoProcesso]: {e}")
                sleep(1)
        else:
            msg = "[tentativas_esgotadas][digitar_anoProcesso]"
            print(f"- {msg}")
            return [False, msg]

    def digitar_trtProcesso(self, driver, value):

        for _ in range(self.qtdTentativas):
            try:
                field = WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.XPATH, '//input[@id="formulario:regiao"]')))
                field.send_keys(value)
                print("- [TRT_PROCESSO]: [OK]")
                return [True, '']
            except Exception as e:
                print(f"- [except][digitar_trtProcesso]: {e}")
                sleep(1)
        else:
            msg = "[tentativas_esgotadas][digitar_trtProcesso]"
            print(f"- {msg}")
            return [False, msg]

    def digitar_varaTrabProcesso(self, driver, value):

        for _ in range(self.qtdTentativas):
            try:
                field = WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.XPATH, '//input[@id="formulario:vara"]')))
                field.send_keys(value)
                print("- [VR_TRAB_PROCESSO]: [OK]")
                return [True, '']
            except Exception as e:
                print(f"- [except][digitar_varaTrabProcesso]: {e}")
                sleep(1)
        else:
            msg = "[tentativas_esgotadas][digitar_varaTrabProcesso]"
            print(f"- {msg}")
            return [False, msg]

    def get_numero_processo_and_digitar(self, driver):

        for indice, identificador in enumerate(self.planilha_base['IDENTIFICADOR']):

            # [TRATAR_VALORES_EM_BRANCO]
            if not pd.isna(identificador):

                if 'numero_processo' in identificador:
                    try:
                        informacao = self.planilha_base.loc[indice, 'INFORMACAO']
                        print(f"- [CHAVE]: {identificador} | VALOR: {informacao}")

                        if valor_vazio(informacao):
                            print("- [NUMERO_PROCESSO_DEVE_SER_PREENCHIDO]")
                            return [False, f'[numero_processo][{informacao}]']
                        else:
                            # [PEGAR_NUMERO_PROCESSO_FORMATADO]
                            nprocesso_formatado = informacao.replace("-", ".").replace(".", "")
                            print(F"- [NPROCESSO_FORMATADO]: {nprocesso_formatado}")
                            self.numero_processo = nprocesso_formatado
                            # [DIVIDIR_NUMERO_PROCESSO]
                            div_processo = informacao.replace("-", ".").split(".")
                            print(f"- [DIV_PROCESSO]: {div_processo}")
                            numero = div_processo[0]
                            digito = div_processo[1]
                            ano = div_processo[2]
                            tribunal = div_processo[-2]
                            varaTrab = div_processo[-1]

                            print(f'- [NUMERO]: {numero}')
                            print(f'- [DIGITO]: {digito}')
                            print(f'- [ANO]: {ano}')
                            print(f'- [TRT]: {tribunal}')
                            print(f'- [VARA_TRAB]: {varaTrab}')
                            print("")

                            # [PJECALC][DIGITAR_NUMERO]
                            self.digitar_numeroProcesso(driver, numero)

                            # [PJECALC][DIGITAR_DIGITO]
                            self.digitar_digitoProcesso(driver, digito)

                            # [PJECALC][DIGITAR_ANO]
                            self.digitar_anoProcesso(driver, ano)

                            # [PJECALC][DIGITAR_TRT]
                            self.digitar_trtProcesso(driver, tribunal)

                            # [PJECALC][DIGITAR_VARA_TRAB]
                            self.digitar_varaTrabProcesso(driver, varaTrab)
                            return [True, '']
                    except Exception as e:
                        msg = f"[except][get_numero_processo_and_digitar]: {e}"
                        print(f"- {msg}")
                        return [False, msg]

            else:
                continue
        else:
            msg = "[não informado: mantido o padrão do PJe-Calc][get_numero_processo_and_digitar]"
            print(f"- {msg}")
            return [False, msg]

    # [VALOR_CAUSA]
    def digitar_valorCausa(self, driver, value):

        for _ in range(self.qtdTentativas):
            try:
                field = WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.XPATH, '//input[@id="formulario:valorDaCausa"]')))
                field.send_keys(value)
                print("- [VALOR_CAUSA_PROCESSO]: [OK]")
                return [True, '']
            except Exception as e:
                print(f"- [except][digitar_valorCausa]: {e}")
                sleep(1)
        else:
            msg = "[tentativas_esgotadas][digitar_valorCausa]"
            print(f"- {msg}")
            return [False, msg]

    def get_valor_causa_and_digitar(self, driver):

        for indice, identificador in enumerate(self.planilha_base['IDENTIFICADOR']):
            # [TRATAR_VALORES_EM_BRANCO]
            if not pd.isna(identificador):
                if 'valor_da_causa' in identificador:
                    try:
                        informacao = self.planilha_base.loc[indice, 'INFORMACAO']
                        print(f"- [CHAVE]: {identificador} | VALOR: {informacao}")
                        # [VALOR_CAUSA]
                        valor_causa = numero_da_planilha(informacao)
                        if valor_causa is None:
                            return [False, f'[{identificador}][{informacao}]']
                        valor_causa = f"{valor_causa:.2f}"
                        print(f"- [VALOR_CAUSA]: {valor_causa}")
                        # [PJECALC][VALOR_CAUSA]
                        self.digitar_valorCausa(driver, valor_causa)
                        return [True, '']
                    except Exception as e:
                        msg = f"[except][get_valor_causa_and_digitar]: {e}"
                        print(f"- {msg}")
                        return [False, msg]
            else:
                continue
        else:
            msg = "[não informado: mantido o padrão do PJe-Calc][get_valor_causa_and_digitar]"
            print(f"- {msg}")
            return [False, msg]

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


    # [RECLAMANTE]
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

    def digitar_nomeReclamante(self, driver, value):

        for _ in range(self.qtdTentativas):
            try:
                field = WebDriverWait(driver, self.delay).until(
                    EC.presence_of_element_located((By.XPATH, '//input[@id="formulario:reclamanteNome"]')))
                field.send_keys(value)
                print("- [RECLAMANTE_PROCESSO]: [OK]")
                return [True, '']
            except Exception as e:
                print(f"- [except][digitar_nomeReclamante]: {e}")
                sleep(1)
        else:
            msg = "[tentativas_esgotadas][digitar_nomeReclamante]"
            print(f"- {msg}")
            return [False, msg]

    def get_nomeReclamante_and_digitar(self, driver):
        for indice, identificador in enumerate(self.planilha_base['IDENTIFICADOR']):
            # [TRATAR_VALORES_EM_BRANCO]
            if not pd.isna(identificador):
                if 'nome_parte1' in identificador:
                    try:
                        informacao = self.planilha_base.loc[indice, 'INFORMACAO']
                        print(f"- [CHAVE]: {identificador} | VALOR: {informacao}")
                        # [RECLAMANTE]
                        if valor_vazio(informacao):
                            print("- [RECLAMANTE_DEVE_SER_PREENCHIDO]")
                            return [False, f'[{identificador}][{informacao}]']
                        else:
                            self.nome_parte1 = informacao
                            print(f"- [NOMER_RECLAMANTE]: {self.nome_parte1}")
                            # [PJECALC][PARTE_1]
                            self.digitar_nomeReclamante(driver, informacao)
                            return [True, '']
                    except Exception as e:
                        msg = f"[except][get_nomeReclamante_and_digitar]: {e}"
                        print(f"- {msg}")
                        return [False, msg]
            else:
                continue
        else:
            msg = "[não informado: mantido o padrão do PJe-Calc][get_valor_causa_and_digitar]"
            print(f"- {msg}")
            return [False, msg]


    # [RECLAMANTE][DOC]
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
                    sleep(1)
                    # cpf1 = cpf.replace(".", "")
                    # cpf_util = cpf1.replace("-", "")
                    # Preencher PJeCalc
                    campo_cpf = WebDriverWait(driver, self.delay).until(
                        EC.presence_of_element_located((By.NAME, 'formulario:reclamanteNumeroDocumentoFiscal')))
                    campo_cpf.send_keys(cpf_str)
                    break


    def formatar_cpf(self, cpf):

        if isinstance(cpf, str):
            cpf = int(cpf)

        cpf_str = f'{cpf:011d}'
        # Formata a string para o padrão 000.000.000-00
        cpf_formatado = f'{cpf_str[:3]}.{cpf_str[3:6]}.{cpf_str[6:9]}-{cpf_str[9:]}'
        return cpf_formatado


    def digitar_CPFReclamante(self, driver, value):

        for _ in range(self.qtdTentativas):
            try:
                # [CLIQUE_ALTERNATIVA_CPF]
                field = WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.XPATH, '//input[@id="formulario:documentoFiscalReclamante:0"]')))
                field.click()
                field_2 = WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.XPATH, '//input[@id="formulario:reclamanteNumeroDocumentoFiscal"]')))
                field_2.clear()
                field_2.send_keys(self.formatar_cpf(value))
                print("- [CPF_RECLAMANTE]: [OK]")
                return [True, '']
            except Exception as e:
                print(f"- [except][digitar_CPFReclamante]: {e}")
                sleep(1)
        else:
            msg = "[tentativas_esgotadas][digitar_CPFReclamante]"
            print(f"- {msg}")
            return [False, msg]

    def get_numeroDocReclamante_and_digitar(self, driver):
        for indice, identificador in enumerate(self.planilha_base['IDENTIFICADOR']):
            # [TRATAR_VALORES_EM_BRANCO]
            if not pd.isna(identificador):
                if 'doc_parte1' in identificador:
                    try:
                        informacao = self.planilha_base.loc[indice, 'INFORMACAO']
                        print(f"- [CHAVE]: {identificador} | VALOR: {informacao}")
                        if valor_vazio(informacao):
                            print("- [CPF_DEVE_SER_PREENCHIDO]")
                            return [False, f'[{identificador}][{informacao}]']
                        informacao = documento_da_planilha(informacao)
                        # [RECLAMANTE]
                        if not informacao:
                            print("- [CPF_DEVE_SER_PREENCHIDO]")
                            return [False, f'[{identificador}][{informacao}]']
                        else:
                            print(f"- [CPF_RECLAMANTE]: {informacao}")
                            # [PJECALC][CPF_PARTE_1]
                            self.digitar_CPFReclamante(driver, informacao)
                            return [True, '']
                    except Exception as e:
                        msg = f"[except][get_numeroDocReclamante_and_digitar]: {e}"
                        print(f"- {msg}")
                        return [False, msg]
            else:
                continue
        else:
            msg = "[não informado: mantido o padrão do PJe-Calc][get_numeroDocReclamante_and_digitar]"
            print(f"- {msg}")
            return [False, msg]


    # [ADVOGADO]
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
                    sleep(1)
                    # Adicionar
                    btn_add = WebDriverWait(driver, self.delay).until(
                        EC.element_to_be_clickable((By.ID, 'formulario:incluirAdvogadoReclamante')))
                    btn_add.click()
                    # Aguardar carregamento
                    self.objTools.aguardar_carregamento(driver)
                    break

    # [ADVOGADOS] -------------------------------------------------------------------------------------------------
    def incluir_advogado(self, driver, sufixo, nome, oab=None, tipo=None, documento=None):
        """Preenche um advogado da parte (sufixo 'Reclamante'/'Reclamado'), clica no "+" e confere se entrou na lista.

        Sem o "+" o PJe-Calc não guarda o advogado. Com documento repetido na mesma parte ele não inclui e não avisa.
        """
        campo = WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.ID, f'formulario:nomeAdvogado{sufixo}')))
        campo.clear()
        campo.send_keys(nome)
        if oab:
            campo_oab = driver.find_element(By.ID, f'formulario:numeroOABAdvogado{sufixo}')
            campo_oab.clear()
            campo_oab.send_keys(oab)
        if tipo and documento:
            indice = {"CPF": 0, "CNPJ": 1, "CEI": 2}[tipo]
            WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, f'formulario:tipoDocumentoAdvogado{sufixo}:{indice}'))).click()
            sleep(1.5)
            campo_doc = driver.find_element(By.ID, f'formulario:numeroDocumentoAdvogado{sufixo}')
            campo_doc.clear()
            campo_doc.send_keys(documento)
        WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, f'formulario:incluirAdvogado{sufixo}'))).click()
        self.objTools.aguardar_carregamento(driver)
        sleep(1.5)
        nomes = driver.execute_script(
            f"""return [...document.querySelectorAll('tbody[id="formulario:listagemAdvogado{sufixo}:tb"] > tr')]
                .map(tr => {{ const tds = tr.querySelectorAll(':scope > td'); return tds.length > 1 ? tds[1].textContent.trim() : ''; }});""")
        if nome.upper() in [n.upper() for n in nomes]:
            print(f"- [ADVOGADO_{sufixo.upper()}]: '{nome}' incluído")
            return True
        registrar("Dados do Cálculo", f"advogado '{nome}' ({sufixo.lower()}) não entrou na lista do PJe-Calc")
        return False

    def lancar_advogados_do_pedido(self, driver, parte):
        """Bloco `advogados` do .json (chaves advogados_<parte>_qtd e advogado_<parte>_<n>_*). False se o pedido não os traz."""
        valores = {str(k).strip(): v for k, v in zip(self.planilha_base['IDENTIFICADOR'], self.planilha_base['INFORMACAO'])
                   if isinstance(k, str)}
        quantidade = valores.get(f"advogados_{parte}_qtd")
        if valor_vazio(quantidade):
            return False
        sufixo = "Reclamante" if parte == "reclamante" else "Reclamado"

        def campo(n, nome_campo):
            valor = valores.get(f"advogado_{parte}_{n}_{nome_campo}")
            return None if valor_vazio(valor) else str(valor).strip()

        for n in range(1, int(float(quantidade)) + 1):
            nome = campo(n, "nome")
            if nome:
                self.incluir_advogado(driver, sufixo, nome, campo(n, "oab"), campo(n, "tipodoc"), campo(n, "doc"))
        return True

    def digitar_nomeAdvogadoReclamante(self, driver, value):

        for _ in range(self.qtdTentativas):
            try:
                # [ADVOGADO_RECLAMADO]
                self.incluir_advogado(driver, "Reclamante", str(value).strip())
                return [True, '']
            except Exception as e:
                print(f"- [except][digitar_nomeAdvogadoReclamante]: {e}")
                sleep(1)
        else:
            msg = "[tentativas_esgotadas][digitar_nomeAdvogadoReclamante]"
            print(f"- {msg}")
            return [False, msg]

    def get_nomeAdvogadoReclamante_and_digitar(self, driver):

        for indice, identificador in enumerate(self.planilha_base['IDENTIFICADOR']):
            # [TRATAR_VALORES_EM_BRANCO]
            if not pd.isna(identificador):
                if 'advogado_parte1' in identificador:
                    try:
                        informacao = self.planilha_base.loc[indice, 'INFORMACAO']
                        print(f"- [CHAVE]: {identificador} | VALOR: {informacao}")
                        # [ADVOGADO_RECLAMANTE]
                        if valor_vazio(informacao):
                            print(f"- [ADVOGADO]: {informacao}")
                            return [False, f'[{identificador}][{informacao}]']
                        else:
                            print(f"- [ADVOGADO_RECLAMANTE]: {informacao}")
                            # [PJECALC][ADVOGADO_RECLAMANTE]
                            self.digitar_nomeAdvogadoReclamante(driver, informacao)
                            return [True, '']
                    except Exception as e:
                        msg = f"[except][get_nomeAdvogadoReclamante_and_digitar]: {e}"
                        print(f"- {msg}")
                        return [False, msg]
            else:
                continue
        else:
            msg = "[não informado: mantido o padrão do PJe-Calc][get_nomeAdvogadoReclamante_and_digitar]"
            print(f"- {msg}")
            return [False, msg]


    # [RECLAMADO]
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
                    sleep(1)
                    campo_numero_cnpj = WebDriverWait(driver, self.delay).until(
                        EC.presence_of_element_located((By.NAME, 'formulario:reclamadoNumeroDocumentoFiscal')))
                    campo_numero_cnpj.send_keys(self.doc_parte2)

    def digitar_nomeReclamado(self, driver, value):

        for _ in range(self.qtdTentativas):
            try:
                # [ADVOGADO_RECLAMADO]
                field = WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.XPATH, '//input[@id="formulario:reclamadoNome"]')))
                field.send_keys(value)
                print("- [NOME_RECLAMADO]: [OK]")
                return [True, '']
            except Exception as e:
                print(f"- [except][digitar_nomeReclamado]: {e}")
                sleep(1)
        else:
            msg = "[tentativas_esgotadas][digitar_nomeReclamado]"
            print(f"- {msg}")
            return [False, msg]

    def get_nomeReclamado_and_digitar(self, driver):

        for indice, identificador in enumerate(self.planilha_base['IDENTIFICADOR']):
            # [TRATAR_VALORES_EM_BRANCO]
            if not pd.isna(identificador):
                if 'nome_parte2' in identificador:
                    try:
                        informacao = self.planilha_base.loc[indice, 'INFORMACAO']
                        print(f"- [CHAVE]: {identificador} | VALOR: {informacao}")
                        # [ADVOGADO_RECLAMANTE]
                        if valor_vazio(informacao):
                            print(f"- [RECLAMADO]: {informacao}")
                            return [False, f'[{identificador}][{informacao}]']
                        else:
                            print(f"- [NOME_RECLAMADO]: {informacao}")
                            # [PJECALC][ADVOGADO_RECLAMANTE]
                            self.digitar_nomeReclamado(driver, informacao)
                            return [True, '']
                    except Exception as e:
                        msg = f"[except][get_nomeReclamado_and_digitar]: {e}"
                        print(f"- {msg}")
                        return [False, msg]
            else:
                continue
        else:
            msg = "[não informado: mantido o padrão do PJe-Calc][get_nomeReclamado_and_digitar]"
            print(f"- {msg}")
            return [False, msg]


    # [RECLAMADO][DOC]
    def digitar_DocFicalReclamado(self, driver, value):

        for _ in range(self.qtdTentativas):
            try:
                # [CLIQUE_ALTERNATIVA_CPF]
                field = WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.XPATH, '//input[@id="formulario:tipoDocumentoFiscalReclamado:1"]')))
                field.click()
                field_2 = WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.XPATH, '//input[@id="formulario:reclamadoNumeroDocumentoFiscal"]')))
                field_2.clear()
                # Verificar a quantidade de caracteres do CNPJ. Se for inferior a 14, adiciona um zero a esquerda.
                if len(value) < 14:
                    # Adicionar um zero à esquerda no CNPJ
                    value = f"{value:0>14}"

                field_2.send_keys(value)
                print("- [CNPJ_RECLAMADO]: [OK]")
                return [True, '']
            except Exception as e:
                print(f"- [except][digitar_DocFicalReclamado]: {e}")
                sleep(1)
        else:
            msg = "[tentativas_esgotadas][digitar_DocFicalReclamado]"
            print(f"- {msg}")
            return [False, msg]

    def get_numeroDocReclamado_and_digitar(self, driver):
        for indice, identificador in enumerate(self.planilha_base['IDENTIFICADOR']):
            # [TRATAR_VALORES_EM_BRANCO]
            if not pd.isna(identificador):

                if 'doc_parte2' in identificador:
                    try:
                        informacao = self.planilha_base.loc[indice, 'INFORMACAO']
                        print(f"- [CHAVE]: {identificador} | VALOR: {informacao}")
                        # [RECLAMANTE]
                        informacao = None if valor_vazio(informacao) else documento_da_planilha(informacao)
                        if not informacao:
                            print(f"- [CNPJ_RECLAMADO]: vazio")
                            return [False, f'[{identificador}][{informacao}]']
                        else:
                            print(f"- [CNPJ_RECLAMADO]: {informacao}")
                            # [PJECALC][CNPJ_RECLAMADO]
                            self.digitar_DocFicalReclamado(driver, informacao)
                            return [True, '']
                    except Exception as e:
                        msg = f"[except][get_numeroDocReclamado_and_digitar]: {e}"
                        print(f"- {msg}")
                        return [False, msg]
            else:
                continue
        else:
            msg = "[não informado: mantido o padrão do PJe-Calc][get_numeroDocReclamado_and_digitar]"
            print(f"- {msg}")
            return [False, msg]

    # [ADVOGADO][RECLAMADO]
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
                    sleep(1)
                    btn_add = WebDriverWait(driver, self.delay).until(
                        EC.element_to_be_clickable((By.ID, 'formulario:incluirAdvogadoReclamado')))
                    btn_add.click()
                    self.objTools.aguardar_carregamento(driver)
                    break

    def digitar_nomeAdvogadoReclamado(self, driver, value):

        for _ in range(self.qtdTentativas):
            try:
                # [ADVOGADO_RECLAMADO]
                self.incluir_advogado(driver, "Reclamado", str(value).strip())
                return [True, '']
            except Exception as e:
                print(f"- [except][digitar_advogadoReclamado]: {e}")
                sleep(1)
        else:
            msg = "[tentativas_esgotadas][digitar_advogadoReclamado]"
            print(f"- {msg}")
            return [False, msg]

    def get_nomeAdvogadoReclamado_and_digitar(self, driver):

        for indice, identificador in enumerate(self.planilha_base['IDENTIFICADOR']):
            # [TRATAR_VALORES_EM_BRANCO]
            if not pd.isna(identificador):
                if 'advogado_parte2' in identificador:
                    try:
                        informacao = self.planilha_base.loc[indice, 'INFORMACAO']
                        print(f"- [CHAVE]: {identificador} | VALOR: {informacao}")
                        # [ADVOGADO_RECLAMANTE]
                        if valor_vazio(informacao):
                            print(f"- [ADVOGADO_RECLAMADO]: {informacao}")
                            return [False, f'[{identificador}][{informacao}]']
                        else:
                            print(f"- [ADVOGADO_RECLAMADO]: {informacao}")
                            # [PJECALC][ADVOGADO_RECLAMADO]
                            self.digitar_nomeAdvogadoReclamado(driver, informacao)
                            return [True, '']
                    except Exception as e:
                        msg = f"[exept][get_nomeAdvogadoReclamado_and_digitar]: {e}"
                        print(f"- {msg}")
                        return [False, msg]
            else:
                continue
        else:
            msg = "[não informado: mantido o padrão do PJe-Calc][get_nomeAdvogadoReclamado_and_digitar]"
            print(f"- {msg}")
            return [False, msg]


    def clicar_btnSalvar(self, driver):

        for _ in range(self.qtdTentativas):
            try:
                btn_salvar = WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.XPATH, '//input[@id="formulario:salvar"]')))
                btn_salvar.click()
                return [True, '']
            except Exception as e:
                print(f"- [except][clicar_btnSalvar]: {e}")
                sleep(1)
        else:
            msg = "[tentativas_esgotadas][clicar_btnSalvar]"
            print(f"- {msg}")
            return [False, msg]


    def clicar_aba_parametrosCalculo(self, driver):

        for _ in range(self.qtdTentativas):
            try:
                selecionar_aba = WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.XPATH, '//td[@id="formulario:tabParametrosCalculo_lbl"]')))
                selecionar_aba.click()
                return [True, '']
            except Exception as e:
                print(f"- [except][aba_parametros_calculo]: {e}")
                sleep(1)
        else:
            msg = "[tentativas_esgotadas][aba_parametros_calculo]"
            print(f"- {msg}")
            return [False, msg]


    # [ESTADO]
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
                    sleep(1)
            elif coluna_identificador == "municipio":
                cidade = coluna_informacao
                cidade = unidecode.unidecode(cidade)
                # print('- Município: ', cidade)
                cidade = cidade.strip()
                print('- Município: ', cidade)
                selecionar_municipio = WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.ID, 'formulario:municipio')))
                selecao2 = Select(selecionar_municipio)
                selecao2.select_by_visible_text(cidade)

    def selecionar_estadoCalculo(self, driver, value):

        for _ in range(self.qtdTentativas):
            try:
                # [ADVOGADO_RECLAMADO]
                field = WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.XPATH, '//select[@id="formulario:estado"]')))
                value_field = Select(field)
                value_field.select_by_visible_text(value)
                print("- [ESTADO]: [OK]")
                return [True, '']
            except Exception as e:
                print(f"- [except][selecionar_estadoCalculo]: {e}")
                sleep(1)
        else:
            msg = "[tentativas_esgotadas][selecionar_estadoCalculo]"
            print(f"- {msg}")
            return [False, msg]

    def get_estadoCalculo_and_digitar(self, driver):

        for indice, identificador in enumerate(self.planilha_base['IDENTIFICADOR']):
            # [TRATAR_VALORES_EM_BRANCO]
            if not pd.isna(identificador):
                if 'uf' in identificador:
                    try:
                        informacao = self.planilha_base.loc[indice, 'INFORMACAO']
                        print(f"- [CHAVE]: {identificador} | VALOR: {informacao}")
                        # [ADVOGADO_RECLAMANTE]
                        if valor_vazio(informacao):
                            print(f"- [ESTADO/UF]: {informacao}")
                            return [False, f'[{identificador}][{informacao}]']
                        else:
                            print(f"- [ESTADO/UF]: {informacao}")
                            # [PJECALC][ESTADO/UF]
                            self.selecionar_estadoCalculo(driver, informacao)
                            return [True, '']
                    except Exception as e:
                        msg = f"[except][get_estadoCalculo_and_digitar]: {e}"
                        print(f"- {msg}")
                        return [False, msg]
            else:
                continue
        else:
            msg = "[não informado: mantido o padrão do PJe-Calc][get_estadoCalculo_and_digitar]"
            print(f"- {msg}")
            return [False, msg]


    # [MUNICIPIO]
    def selecionar_municipioCalculo(self, driver, value):

        for _ in range(self.qtdTentativas):
            try:
                # [ADVOGADO_RECLAMADO]
                field = WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.XPATH, '//select[@id="formulario:municipio"]')))
                value_field = Select(field)

                # [TRATAMENTO] a v3.41 manda 'RECIFE'; a planilha do SAP manda 'RECIFE-PE'.
                opcoes = [opcao.text for opcao in value_field.options]
                escolhida = opcao_de_municipio(value, opcoes)
                print(f"- [MUNICIPIO]: {escolhida}")
                print(f"- [VALOR_ORIGINAL_MUNICIPIO]: {value}")
                if escolhida is None:
                    raise ValueError(f"município '{value}' não está na lista do PJe-Calc para a UF selecionada")
                value_field.select_by_visible_text(escolhida)
                print("- [MUNICIPIO]: [OK]")
                return [True, '']
            except Exception as e:
                print(f"- [except][selecionar_municipioCalculo]: {e}")
                sleep(1)
        else:
            msg = "[tentativas_esgotadas][selecionar_municipioCalculo]"
            print(f"- {msg}")
            return [False, msg]


    def get_municipioCalculo_and_digitar(self, driver):

        for indice, identificador in enumerate(self.planilha_base['IDENTIFICADOR']):
            # [TRATAR_VALORES_EM_BRANCO]
            if not pd.isna(identificador):
                if 'municipio' in identificador:
                    try:
                        informacao = self.planilha_base.loc[indice, 'INFORMACAO']
                        print(f"- [CHAVE]: {identificador} | VALOR: {informacao}")
                        # [ADVOGADO_RECLAMANTE]
                        if valor_vazio(informacao):
                            print(f"- [MUNICIPIO]: {informacao}")
                            return [False, f'[{identificador}][{informacao}]']
                        else:
                            print(f"- [MUNICIPIO]: {informacao}")
                            # [PJECALC][ESTADO/UF]
                            self.selecionar_municipioCalculo(driver, informacao)
                            return [True, '']
                    except Exception as e:
                        msg = f"[except][get_municipioCalculo_and_digitar]: {e}"
                        print(f"- {msg}")
                        return [False, msg]
            else:
                continue
        else:
            msg = "[não informado: mantido o padrão do PJe-Calc][get_municipioCalculo_and_digitar]"
            print(f"- {msg}")
            return [False, msg]



    # [ADMISSAO]
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

    def digitar_dataAdmicaoCalculo(self, driver, value):

        for _ in range(self.qtdTentativas):
            try:
                # [ADMISSAO]
                field = WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.XPATH, '//input[@id="formulario:dataAdmissaoInputDate"]')))
                field.clear()
                field.send_keys(value)
                print("- [ADMISSAO]: [OK]")
                return [True, '']
            except Exception as e:
                print(f"- [except][digitar_dataAdmicaoCalculo]: {e}")
                sleep(1)
        else:
            msg = "[tentativas_esgotadas][digitar_dataAdmicaoCalculo]"
            print(f"- {msg}")
            return [False, msg]

    def get_dtAdmissao_and_digitar(self, driver):

        for indice, identificador in enumerate(self.planilha_base['IDENTIFICADOR']):
            # [TRATAR_VALORES_EM_BRANCO]
            if not pd.isna(identificador):
                if 'data_admissao' in identificador:
                    try:
                        informacao = self.planilha_base.loc[indice, 'INFORMACAO']
                        print(f"- [CHAVE]: {identificador} | VALOR: {informacao}")
                        # [FORMATACAO]
                        data_admissao = data_da_planilha(informacao)
                        if data_admissao:
                            self.datetime_admissao = data_admissao
                            data_admissao = data_admissao.strftime('%d/%m/%Y')
                            # [PJECALC][ADMISSAO]
                            print(f"- [ADMISSAO]: {data_admissao}")
                            self.digitar_dataAdmicaoCalculo(driver, data_admissao)
                            return [True, '']
                        else:
                            self.datetime_admissao = ""
                            print(f"- [ADMISSAO]: {informacao}")
                            return [False, f'[{identificador}][{informacao}]']
                    except Exception as e:
                        msg = f"[except][get_dtAdmissao_and_digitar]: {e}"
                        print(f"- {msg}")
                        return [False, msg]
            else:
                continue
        else:
            msg = "[não informado: mantido o padrão do PJe-Calc][get_dtAdmissao_and_digitar]"
            print(f"- {msg}")
            return [False, msg]


    # [DEMISSAO]
    def digitar_dataDemissaoCalculo(self, driver, value):

        for _ in range(self.qtdTentativas):
            try:
                # [DEMISSAO]
                # [TRATAMENTO]
                field = WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.XPATH, '//input[@id="formulario:dataDemissaoInputDate"]')))
                field.clear()
                field.send_keys(value)
                print("- [DEMISSAO]: [OK]")
                return [True, '']
            except Exception as e:
                print(f"- [except][digitar_dataDemissaoCalculo]: {e}")
                sleep(1)
        else:
            msg = "[tentativas_esgotadas][digitar_dataDemissaoCalculo]"
            print(f"- {msg}")
            return [False, msg]

    def get_dtDemissao_and_digitar(self, driver):

        for indice, identificador in enumerate(self.planilha_base['IDENTIFICADOR']):
            # [TRATAR_VALORES_EM_BRANCO]
            if not pd.isna(identificador):
                if 'data_rescisao' in identificador:
                    try:
                        informacao = self.planilha_base.loc[indice, 'INFORMACAO']
                        print(f"- [CHAVE]: {identificador} | VALOR: {informacao}")
                        # [DEMISSAO]
                        data_demissao = data_da_planilha(informacao)
                        if data_demissao:
                            self.datetime_demissao = data_demissao
                            data_demissao = data_demissao.strftime('%d/%m/%Y')
                            # [PJECALC][DEMISSAO]
                            print(f"- [DEMISSAO]: {data_demissao}")
                            self.digitar_dataDemissaoCalculo(driver, data_demissao)
                            return [True, '']
                        else:
                            self.datetime_demissao = ""
                            print(f"- [DEMISSAO]: {informacao}")
                            return [False, f'[{identificador}][{informacao}]']
                    except Exception as e:
                        msg = f"[except][get_dtDemissao_and_digitar]: {e}"
                        print(f"- {msg}")
                        return [False, msg]
            else:
                continue
        else:
            msg = "[não informado: mantido o padrão do PJe-Calc][get_dtDemissao_and_digitar]"
            print(f"- {msg}")
            return [False, msg]


    # [AJUIZAMENTO]
    def digitar_dataAjuizamentoCalculo(self, driver, value):

        for _ in range(self.qtdTentativas):
            try:
                # [AJUIZAMENTO]
                # [TRATAMENTO]
                field = WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.XPATH, '//input[@id="formulario:dataAjuizamentoInputDate"]')))
                field.clear()
                field.send_keys(value)
                print("- [DT_AJUIZAMENTO]: [OK]")
                return [True, '']
            except Exception as e:
                print(f"- [except][digitar_dataAjuizamentoCalculo]: {e}")
                sleep(1)
        else:
            msg = "[tentativas_esgotadas][digitar_dataAjuizamentoCalculo]"
            print(f"- {msg}")
            return [False, msg]

    def get_dtAjuizamento_and_digitar(self, driver):

        for indice, identificador in enumerate(self.planilha_base['IDENTIFICADOR']):
            # [TRATAR_VALORES_EM_BRANCO]
            if not pd.isna(identificador):
                if 'data_ajuizamento' in identificador:
                    try:
                        informacao = self.planilha_base.loc[indice, 'INFORMACAO']
                        print(f"- [CHAVE]: {identificador} | VALOR: {informacao}")
                        # [AJUIZAMENTO]
                        data_ajuizamento = data_da_planilha(informacao)
                        if data_ajuizamento:
                            data_ajuizamento = data_ajuizamento.strftime('%d/%m/%Y')
                            # [PJECALC][AJUIZAMENTO]
                            print(f"- [AJUIZAMENTO]: {data_ajuizamento}")
                            self.digitar_dataAjuizamentoCalculo(driver, data_ajuizamento)
                            return [True, '']
                        else:
                            print(f"- [AJUIZAMENTO]: {informacao}")
                            return [False, f'[{identificador}][{informacao}]']
                    except Exception as e:
                        msg = f"[except][get_dtAjuizamento_and_digitar]: {e}"
                        print(f"- {msg}")
                        return [False, msg]
            else:
                continue
        else:
            msg = "[não informado: mantido o padrão do PJe-Calc][get_dtAjuizamento_and_digitar]"
            print(f"- {msg}")
            return [False, msg]


    # [DT_INICIAL_CALCULO]
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

    def digitar_dataInicialCalculo(self, driver, value):

        for _ in range(self.qtdTentativas):
            try:
                # [DT_INICIAL_CALCULO]
                # [TRATAMENTO]
                field = WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.XPATH, '//input[@id="formulario:dataInicioCalculoInputDate"]')))
                field.clear()
                field.send_keys(value)
                print("- [DT_INICIAL_CALCULO]: [OK]")
                return [True, '']
            except Exception as e:
                print(f"- [except][digitar_dataInicialCalculo]: {e}")
                sleep(1)
        else:
            msg = "[tentativas_esgotadas][digitar_dataInicialCalculo]"
            print(f"- {msg}")
            return [False, msg]

    def get_dtInicialCalc_and_digitar(self, driver):

        for indice, identificador in enumerate(self.planilha_base['IDENTIFICADOR']):
            # [TRATAR_VALORES_EM_BRANCO]
            if not pd.isna(identificador):
                if 'inicio_calculo' in identificador:
                    try:
                        informacao = self.planilha_base.loc[indice, 'INFORMACAO']
                        print(f"- [CHAVE]: {identificador} | VALOR: {informacao}")
                        # [DT_INICIAL_CALCULO]
                        data_inicial = data_da_planilha(informacao)
                        if data_inicial:
                            self.datetime_inicio_calc = data_inicial
                            data_inicial_calc = data_inicial.strftime('%d/%m/%Y')
                            # [PJECALC][DT_INICIAL_CALCULO]
                            print(f"- [DT_INICIAL_CALCULO]: {data_inicial_calc}")
                            self.digitar_dataInicialCalculo(driver, data_inicial_calc)
                            return [True, '']
                        else:
                            self.datetime_inicio_calc = ""
                            print(f"- [DT_INICIAL_CALCULO]: {informacao}")
                            return [False, f'[{identificador}][{informacao}]']
                    except Exception as e:
                        msg = f"[except][get_dtInicialCalc_and_digitar]: {e}"
                        print(f"- {msg}")
                        return [False, msg]
            else:
                continue
        else:
            msg = "[não informado: mantido o padrão do PJe-Calc][get_dtInicialCalc_and_digitar]"
            print(f"- {msg}")
            return [False, msg]

    # [DT_FINAL_CALCULO]
    def digitar_dataFinalCalculo(self, driver, value):

        for _ in range(self.qtdTentativas):
            try:
                # [DT_FINAL_CALCULO]
                # [TRATAMENTO]
                field = WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.XPATH, '//input[@id="formulario:dataTerminoCalculoInputDate"]')))
                field.clear()
                field.send_keys(value)
                print("- [DT_FINAL_CALCULO]: [OK]")
                return [True, '']
            except Exception as e:
                print(f"- [except][digitar_dataFinalCalculo]: {e}")
                sleep(1)
        else:
            msg = "[tentativas_esgotadas][digitar_dataFinalCalculo]"
            print(f"- {msg}")
            return [False, msg]

    def get_dtFinalCalc_and_digitar(self, driver):

        for indice, identificador in enumerate(self.planilha_base['IDENTIFICADOR']):
            # [TRATAR_VALORES_EM_BRANCO]
            if not pd.isna(identificador):
                if 'termino_calculo' in identificador:
                    try:
                        informacao = self.planilha_base.loc[indice, 'INFORMACAO']
                        print(f"- [CHAVE]: {identificador} | VALOR: {informacao}")
                        # [DT_FINAL_CALCULO]
                        data_final = data_da_planilha(informacao)
                        if data_final:
                            self.datetime_final_calc = data_final
                            data_final_calc = data_final.strftime('%d/%m/%Y')
                            # [PJECALC][DT_FINAL_CALCULO]
                            print(f"- [DT_FINAL_CALCULO]: {data_final_calc}")
                            self.digitar_dataFinalCalculo(driver, data_final_calc)
                            return [True, '']
                        else:
                            self.datetime_final_calc = ""
                            print(f"- [DT_FINAL_CALCULO]: {informacao}")
                            return [False, f'[{identificador}][{informacao}]']
                    except Exception as e:
                        msg = f"[except][get_dtFinalCalc_and_digitar]: {e}"
                        print(f"- {msg}")
                        return [False, msg]
            else:
                continue
        else:
            msg = "[não informado: mantido o padrão do PJe-Calc][get_dtFinallCalc_and_digitar]"
            print(f"- {msg}")
            return [False, msg]


    # [APLICAR_PRESCRICAO][VERBAS (QUINQUENAL)]
    def aplicar_prescricaoVerbas(self, driver, value):
        for _ in range(self.qtdTentativas):
            try:
                field = WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.XPATH, '//input[@id="formulario:prescricaoQuinquenal"]')))
                if field.is_selected() != value:
                    field.click()
                print("- [aplicar_prescricao_verbas]: [OK]")
                return [True, '']
            except Exception as e:
                print(f"- [except][aplicar_prescricao_verbas]: {e}")
                sleep(1)
        else:
            msg = "[tentativas_esgotadas][aplicar_prescricao_verbas]"
            print(f"- {msg}")
            return [False, msg]

    def get_aplicar_prescricaoVerbas_and_aplicar(self, driver):

        for indice, identificador in enumerate(self.planilha_base['IDENTIFICADOR']):
            # [TRATAR_VALORES_EM_BRANCO]
            if not pd.isna(identificador):
                if 'aplicar_prescricao_verbas' in identificador:
                    try:
                        informacao = self.planilha_base.loc[indice, 'INFORMACAO']
                        print(f"- [CHAVE]: {identificador} | APLICAR_PRESCRICAO_VERBAS: {informacao} | TIPO: {type(informacao)}")
                        # [APLICAR_PRESCRICAO]
                        marcar = booleano_da_planilha(informacao)
                        if marcar is not None:
                            self.aplicar_prescricaoVerbas(driver, marcar)
                            return [True, '']
                        else:
                            print(f"- [APLICAR_PRESCRICAO_VERBAS]: {informacao}")
                            return [False, f'[{identificador}][{informacao}]']
                    except Exception as e:
                        msg = f"[except][get_aplicar_prescricaoVerbas_and_digitar]: {e}"
                        print(f"- {msg}")
                        return [False, msg]
            else:
                continue
        else:
            msg = "[não informado: mantido o padrão do PJe-Calc][get_aplicar_prescricaoVerbas_and_digitar]"
            print(f"- {msg}")
            return [False, msg]

    # [APLICAR_PRESCRICAO][FGTS]
    def aplicar_prescricaoFGTS(self, driver, value):
        for _ in range(self.qtdTentativas):
            try:
                field = WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.XPATH, '//input[@id="formulario:prescricaoFgts"]')))
                if field.is_selected() != value:
                    field.click()
                print("- [aplicar_prescricaoFGTS]: [OK]")
                return [True, '']
            except Exception as e:
                print(f"- [except][aplicar_prescricaoFGTS]: {e}")
                sleep(1)
        else:
            msg = "[tentativas_esgotadas][aplicar_prescricaoFGTS]"
            print(f"- {msg}")
            return [False, msg]

    def get_aplicar_prescricaoFGTS_and_digitar(self, driver):

        for indice, identificador in enumerate(self.planilha_base['IDENTIFICADOR']):
            # [TRATAR_VALORES_EM_BRANCO]
            if not pd.isna(identificador):
                if 'aplicar_prescricao_fgts' in identificador.lower():
                    try:
                        informacao = self.planilha_base.loc[indice, 'INFORMACAO']
                        print(f"- [CHAVE]: {identificador} | APLICAR_PRESCRICAO_FGTS: {informacao} | TIPO: {type(informacao)}")
                        # [APLICAR_PRESCRICAO]
                        marcar = booleano_da_planilha(informacao)
                        if marcar is not None:
                            self.aplicar_prescricaoFGTS(driver, marcar)
                            return [True, '']
                        else:
                            print(f"- [APLICAR_PRESCRICAO_FGTS]: {informacao}")
                            return [False, f'[{identificador}][{informacao}]']
                    except Exception as e:
                        msg = f"[except][get_aplicar_prescricaoFGTS_and_digitar]: {e}"
                        print(f"- {msg}")
                        return [False, msg]
            else:
                continue
        else:
            msg = "[não informado: mantido o padrão do PJe-Calc][get_aplicar_prescricaoFGTS_and_digitar]"
            print(f"- {msg}")
            return [False, msg]


    # [OLD]
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



    # [REGIME_DE_TRABALHO]
    def selecionar_regimeTrabalho(self, driver, value):

        for _ in range(self.qtdTentativas):
            try:
                field = WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.XPATH, '//select[@id="formulario:tipoDaBaseTabelada"]')))
                value_field = Select(field)
                # [TRATAMENTO]
                value_format = value.strip()
                value_field.select_by_visible_text(value_format)
                print("- [REGIME_DE_TRABALHO]: [OK]")
                return [True, '']
            except Exception as e:
                print(f"- [except][selecionar_regimeTrabalho]: {e}")
                sleep(1)
        else:
            msg = "[tentativas_esgotadas][selecionar_regimeTrabalho]"
            print(f"- {msg}")
            return [False, msg]

    def get_regimeTrabalho_and_selecionar(self, driver):

        for indice, identificador in enumerate(self.planilha_base['IDENTIFICADOR']):
            # [TRATAR_VALORES_EM_BRANCO]
            if not pd.isna(identificador):
                if 'regime_trabalho' in identificador:
                    try:
                        informacao = self.planilha_base.loc[indice, 'INFORMACAO']
                        print(f"- [CHAVE]: {identificador} | REGIME_DE_TRABALHO: {informacao} | TIPO: {type(informacao)}")
                        if valor_vazio(informacao):
                            return [False, f'[{identificador}][{informacao}]']
                        else:
                            self.selecionar_regimeTrabalho(driver, informacao)
                            return [True, '']
                    except Exception as e:
                        msg = f"[except][get_regimeTrabalho_and_digitar]: {e}"
                        print(f"- {msg}")
                        return [False, msg]
            else:
                continue
        else:
            msg = "[não informado: mantido o padrão do PJe-Calc][get_regimeTrabalho_and_digitar]"
            print(f"- {msg}")
            return [False, msg]

    # [OLD]
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



    # [MAIOR_REMUNERACAO]
    def digitar_maiorRemuneracao(self, driver, value):

        for _ in range(self.qtdTentativas):
            try:
                # [TRATAMENTO]
                value = f"{value:.2f}"

                field = WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.XPATH, '//input[@id="formulario:valorMaiorRemuneracao"]')))
                field.clear()
                field.send_keys(value)
                print("- [MAIOR_REMUNERACAO]: [OK]")
                return [True, '']
            except Exception as e:
                print(f"- [except][digitar_maiorRemuneracao]: {e}")
                sleep(1)
        else:
            msg = "[tentativas_esgotadas][digitar_maiorRemuneracao]"
            print(f"- {msg}")
            return [False, msg]

    def get_maiorRemuneracao_and_digitar(self, driver):

        for indice, identificador in enumerate(self.planilha_base['IDENTIFICADOR']):
            # [TRATAR_VALORES_EM_BRANCO]
            if not pd.isna(identificador):
                if 'maior_remuneracao' in identificador:
                    try:
                        informacao = self.planilha_base.loc[indice, 'INFORMACAO']
                        print(f"- [CHAVE]: {identificador} | MAIOR_REMUNERACAO: {informacao} | TIPO: {type(informacao)}")
                        valor = numero_da_planilha(informacao)
                        if valor is None:
                            return [False, f'[{identificador}][{informacao}]']
                        self.digitar_maiorRemuneracao(driver, valor)
                        return [True, '']

                    except Exception as e:
                        msg = f"[except][get_maiorRemuneracao_and_digitar]: {e}"
                        print(f"- {msg}")
                        return [False, msg]
            else:
                continue
        else:
            msg = "[não informado: mantido o padrão do PJe-Calc][get_maiorRemuneracao_and_digitar]"
            print(f"- {msg}")
            return [False, msg]


    # [ULTIMA_REMUNERACAO]
    def digitar_ultimaRemuneracao(self, driver, value):

        for _ in range(self.qtdTentativas):
            try:
                # [TRATAMENTO]
                value = f"{value:.2f}"

                field = WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.XPATH, '//input[@id="formulario:valorUltimaRemuneracao"]')))
                field.clear()
                field.send_keys(value)
                print("- [ULTIMA_REMUNERACAO]: [OK]")
                return [True, '']
            except Exception as e:
                print(f"- [except][digitar_ultimaRemuneracao]: {e}")
                sleep(1)
        else:
            msg = "[tentativas_esgotadas][digitar_ultimaRemuneracao]"
            print(f"- {msg}")
            return [False, msg]

    def get_ultimaRemuneracao_and_digitar(self, driver):

        for indice, identificador in enumerate(self.planilha_base['IDENTIFICADOR']):
            # [TRATAR_VALORES_EM_BRANCO]
            if not pd.isna(identificador):
                if 'ultima_remuneracao' in identificador:
                    try:
                        informacao = self.planilha_base.loc[indice, 'INFORMACAO']
                        print(
                            f"- [CHAVE]: {identificador} | ULTIMA_REMUNERACAO: {informacao} | TIPO: {type(informacao)}")
                        valor = numero_da_planilha(informacao)
                        if valor is None:
                            return [False, f'[{identificador}][{informacao}]']
                        self.digitar_ultimaRemuneracao(driver, valor)
                        return [True, '']

                    except Exception as e:
                        msg = f"[except][get_ultimaRemuneracao_and_digitar]: {e}"
                        print(f"- {msg}")
                        return [False, msg]
            else:
                continue
        else:
            msg = "[não informado: mantido o padrão do PJe-Calc][get_ultimaRemuneracao_and_digitar]"
            print(f"- {msg}")
            return [False, msg]

    # [OLD]
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


    # [PRAZO_DE_AVISO_PREVIO]
    def selecionar_prazoAvisoPrevio(self, driver, value):

        for _ in range(self.qtdTentativas):
            try:
                field = WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.XPATH, '//select[@id="formulario:apuracaoPrazoDoAvisoPrevio"]')))
                value_field = Select(field)
                # [TRATAMENTO]
                value_format = value.strip()
                value_field.select_by_visible_text(value_format)
                print("- [PRAZO_DE_AVISO_PREVIO]: [OK]")
                return [True, '']
            except Exception as e:
                print(f"- [except][selecionar_prazoAvisoPrevio]: {e}")
                sleep(1)
        else:
            msg = "[tentativas_esgotadas][selecionar_prazoAvisoPrevio]"
            print(f"- {msg}")
            return [False, msg]

    def get_prazoAvisoPrevio_and_selecionar(self, driver):

        for indice, identificador in enumerate(self.planilha_base['IDENTIFICADOR']):
            # [TRATAR_VALORES_EM_BRANCO]
            if not pd.isna(identificador):
                if 'prazo_de_aviso_previo' in identificador:
                    try:
                        informacao = self.planilha_base.loc[indice, 'INFORMACAO']
                        print(f"- [CHAVE]: {identificador} | PRAZO_DE_AVISO_PREVIO: {informacao} | TIPO: {type(informacao)}")
                        if not valor_vazio(informacao):
                            self.selecionar_prazoAvisoPrevio(driver, informacao)
                            return [True, informacao]
                        else:
                            return [False, f'[{identificador}][{informacao}]']
                    except Exception as e:
                        msg = f"[except][get_prazoAvisoPrevio_and_selecionar]: {e}"
                        print(f"- {msg}")
                        return [False, msg]
            else:
                continue
        else:
            msg = "[não informado: mantido o padrão do PJe-Calc][get_prazoAvisoPrevio_and_selecionar]"
            print(f"- {msg}")
            return [False, msg]


    # [QUANTIDADE_DIAS_AVISO_PREVIO]
    def digitar_qtdDiasAvisoPrevio(self, driver, value):

        for _ in range(self.qtdTentativas):
            try:
                # [TRATAMENTO]
                value = f"{value}"

                field = WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.XPATH, '//input[@id="formulario:prazoAvisoInformado"]')))
                field.clear()
                field.send_keys(value)
                print("- [ULTIMA_REMUNERACAO]: [OK]")
                return [True, '']
            except Exception as e:
                print(f"- [except][digitar_qtdDiasAvisoPrevio]: {e}")
                sleep(1)
        else:
            msg = "[tentativas_esgotadas][digitar_qtdDiasAvisoPrevio]"
            print(f"- {msg}")
            return [False, msg]

    def get_qtdDiasAvisoPrevio_and_digitar(self, driver):

        for indice, identificador in enumerate(self.planilha_base['IDENTIFICADOR']):
            # [TRATAR_VALORES_EM_BRANCO]
            if not pd.isna(identificador):
                if 'quantidade_dias_aviso_previo' in identificador:
                    try:
                        informacao = self.planilha_base.loc[indice, 'INFORMACAO']
                        print(f"- [CHAVE]: {identificador} | QUANTIDADE_DIAS_AVISO_PREVIO: {informacao} | TIPO: {type(informacao)}")
                        if not pd.isna(informacao):
                            # CONVERTER PARA INTEIRO
                            try:
                                valor = int(informacao)
                                self.digitar_qtdDiasAvisoPrevio(driver, valor)
                                return [True, '']
                            except Exception as e:
                                print(f"- [except][get_qtdDiasAvisoPrevio_and_digitar][conversao]: {e}")
                                return [False, '']
                        else:
                            return [False, '']

                    except Exception as e:
                        msg = f"[except][get_qtdDiasAvisoPrevio_and_digitar]: {e}"
                        print(f"- {msg}")
                        return [False, msg]
            else:
                continue
        else:
            msg = "[não informado: mantido o padrão do PJe-Calc][get_qtdDiasAvisoPrevio_and_digitar]"
            print(f"- {msg}")
            return [False, msg]


    # [OLD]
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

        # sleep(2)
        if self.prazo_de_aviso_previo == 'Informado':
            # Aguardar o campo condicional aparecer
            # aguardar_campo_quantidade()

            WebDriverWait(driver, self.delay).until(
                EC.visibility_of_element_located((By.NAME, 'formulario:prazoAvisoInformado')))

            # sleep(2)
            quantidade = WebDriverWait(driver, self.delay).until(
                EC.presence_of_element_located((By.NAME, 'formulario:prazoAvisoInformado')))
            quantidade.click()
            quantidade.send_keys(self.quantidade_dias_aviso_previo)



    # [PROJETAR_AVISO_PREVIO_INDENIZADO]
    def marcar_checkbox_avisoPrevioIndenizado(self, driver, value):
        for _ in range(self.qtdTentativas):
            try:
                field = WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.XPATH, '//input[@id="formulario:projetaAvisoIndenizado"]')))
                if 'true' in value.lower() and field.is_enabled() and not field.selected():
                    field.click()
                print("- [PROJETAR_AVISO_PREVIO_INDENIZADO]: [OK]")
                return [True, '']
            except Exception as e:
                print(f"- [except][marcar_checkbox_avisoPrevioIndenizado]: {e}")
                sleep(1)
        else:
            msg = "[tentativas_esgotadas][marcar_checkbox_avisoPrevioIndenizado]"
            print(f"- {msg}")
            return [False, msg]

    def get_avisoPrevioIndenizado_and_marcar(self, driver):

        for indice, identificador in enumerate(self.planilha_base['IDENTIFICADOR']):
            # [TRATAR_VALORES_EM_BRANCO]
            if not pd.isna(identificador):
                if 'projetar_aviso_previo_indenizado' in identificador:
                    try:
                        informacao = self.planilha_base.loc[indice, 'INFORMACAO']
                        print(f"- [CHAVE]: {identificador} | PROJETAR_AVISO_PREVIO_INDENIZADO: {informacao} | TIPO: {type(informacao)}")

                        if not pd.isna(informacao):
                            self.marcar_checkbox_avisoPrevioIndenizado(driver, informacao)
                            return [True, '']

                    except Exception as e:
                        msg = f"[except][get_avisoPrevioIndenizado_and_marcar]: {e}"
                        print(f"- {msg}")
                        return [False, msg]
            else:
                continue
        else:
            msg = "[não informado: mantido o padrão do PJe-Calc][get_avisoPrevioIndenizado_and_marcar]"
            print(f"- {msg}")
            return [False, msg]


    # [LIMITAR_AVOS_AO_PERIODO_DO_CALCULO]
    def marcar_checkbox_limitarAvos_ao_periodo_do_calculo(self, driver, value):
        for _ in range(self.qtdTentativas):
            try:
                field = WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.XPATH, '//input[@id="formulario:limitarAvos"]')))
                if 'true' in value.lower() and field.is_enabled() and not field.selected():
                    field.click()
                print("- [LIMITAR_AVOS_AO_PERIODO_DO_CALCULO]: [OK]")
                return [True, '']
            except Exception as e:
                print(f"- [except][marcar_checkbox_limitarAvos_ao_periodo_do_calculo]: {e}")
                sleep(1)
        else:
            msg = "[tentativas_esgotadas][marcar_checkbox_limitarAvos_ao_periodo_do_calculo]"
            print(f"- {msg}")
            return [False, msg]

    def get_limitarAvos_ao_periodo_do_calculo_and_marcar(self, driver):

        for indice, identificador in enumerate(self.planilha_base['IDENTIFICADOR']):
            # [TRATAR_VALORES_EM_BRANCO]
            if not pd.isna(identificador):
                if 'limitar_avos_ao_periodo_do_calculo' in identificador:
                    try:
                        informacao = self.planilha_base.loc[indice, 'INFORMACAO']
                        print(f"- [CHAVE]: {identificador} | LIMITAR_AVOS_AO_PERIODO_DO_CALCULO: {informacao} | TIPO: {type(informacao)}")
                        if not pd.isna(informacao):
                            self.marcar_checkbox_limitarAvos_ao_periodo_do_calculo(driver, informacao)
                            return [True, '']
                    except Exception as e:
                        msg = f"[except][get_limitarAvos_ao_periodo_do_calculo_and_marcar]: {e}"
                        print(f"- {msg}")
                        return [False, msg]
            else:
                continue
        else:
            msg = "[não informado: mantido o padrão do PJe-Calc][get_limitarAvos_ao_periodo_do_calculo_and_marcar]"
            print(f"- {msg}")
            return [False, msg]


    # [ZERAR_VALOR_NEGATIVO_(PADRAO)]
    def marcar_checkbox_zerarValorNegativoPadrao(self, driver, value):
        for _ in range(self.qtdTentativas):
            try:
                field = WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.XPATH, '//input[@id="formulario:zeraValorNegativo"]')))
                if 'true' in value.lower() and field.is_enabled() and not field.selected():
                    field.click()
                print("- [ZERAR_VALOR_NEGATIVO_(PADRAO)]: [OK]")
                return [True, '']
            except Exception as e:
                print(f"- [except][marcar_checkbox_zerarValorNegativoPadrao]: {e}")
                sleep(1)
        else:
            msg = "[tentativas_esgotadas][marcar_checkbox_zerarValorNegativoPadrao]"
            print(f"- {msg}")
            return [False, msg]

    def get_zerarValorNegativoPadrao_and_marcar(self, driver):

        for indice, identificador in enumerate(self.planilha_base['IDENTIFICADOR']):
            # [TRATAR_VALORES_EM_BRANCO]
            if not pd.isna(identificador):
                if 'zerar_valor_negativo_padrao' in identificador:
                    try:
                        informacao = self.planilha_base.loc[indice, 'INFORMACAO']
                        print(f"- [CHAVE]: {identificador} | ZERAR_VALOR_NEGATIVO_: {informacao} | TIPO: {type(informacao)}")
                        if not pd.isna(informacao):
                            self.marcar_checkbox_zerarValorNegativoPadrao(driver, informacao)
                            return [True, '']
                    except Exception as e:
                        msg = f"[except][get_zerarValorNegativoPadrao_and_marcar]: {e}"
                        print(f"- {msg}")
                        return [False, msg]
            else:
                continue
        else:
            msg = "[não informado: mantido o padrão do PJe-Calc][get_zerarValorNegativoPadrao_and_marcar]"
            print(f"- {msg}")
            return [False, msg]

    # [CONSIDERAR_FERIADOS_ESTATUAIS]
    def marcar_checkbox_considerar_feriadosEstaduais(self, driver, value):
        for _ in range(self.qtdTentativas):
            try:
                field = WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.XPATH, '//input[@id="formulario:consideraFeriadoEstadual"]')))
                if 'true' in value.lower() and field.is_enabled() and not field.selected():
                    field.click()
                print("- [CONSIDERAR_FERIADOS_ESTATUAIS]: [OK]")
                return [True, '']
            except Exception as e:
                print(f"- [except][marcar_checkbox_considerarFeriadosEstaduais]: {e}")
                sleep(1)
        else:
            msg = "[tentativas_esgotadas][marcar_checkbox_considerarFeriadosEstaduais]"
            print(f"- {msg}")
            return [False, msg]

    def get_considerar_feriadosEstaduais_and_marcar(self, driver):

        for indice, identificador in enumerate(self.planilha_base['IDENTIFICADOR']):
            # [TRATAR_VALORES_EM_BRANCO]
            if not pd.isna(identificador):
                if 'considerar_feriados_estaduais' in identificador:
                    try:
                        informacao = self.planilha_base.loc[indice, 'INFORMACAO']
                        print(f"- [CHAVE]: {identificador} | CONSIDERAR_FERIADOS_ESTATUAIS: {informacao} | TIPO: {type(informacao)}")
                        if not pd.isna(informacao):
                            self.marcar_checkbox_considerar_feriadosEstaduais(driver, informacao)
                            return [True, '']
                    except Exception as e:
                        msg = f"[except][get_considerar_feriadosEstaduais_and_marcar]: {e}"
                        print(f"- {msg}")
                        return [False, msg]
            else:
                continue
        else:
            msg = "[não informado: mantido o padrão do PJe-Calc][get_considerar_feriadosEstaduais_and_marcar]"
            print(f"- {msg}")
            return [False, msg]

    # [CONSIDERAR_FERIADOS_MUNICIPAIS]
    def marcar_checkbox_considerar_feriadosMunicipais(self, driver, value):
        for _ in range(self.qtdTentativas):
            try:
                field = WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.XPATH, '//input[@id="formulario:consideraFeriadoMunicipal"]')))
                if 'true' in value.lower() and field.is_enabled() and not field.selected():
                    field.click()
                print("- [CONSIDERAR_FERIADOS_MUNICIPAIS]: [OK]")
                return [True, '']
            except Exception as e:
                print(f"- [except][marcar_checkbox_considerar_feriadosMunicipais]: {e}")
                sleep(1)
        else:
            msg = "[tentativas_esgotadas][marcar_checkbox_considerar_feriadosMunicipais]"
            print(f"- {msg}")
            return [False, msg]

    def get_considerar_feriadosMunicipais_and_marcar(self, driver):

        for indice, identificador in enumerate(self.planilha_base['IDENTIFICADOR']):
            # [TRATAR_VALORES_EM_BRANCO]
            if not pd.isna(identificador):
                if 'considerar_feriados_municipais' in identificador:
                    try:
                        informacao = self.planilha_base.loc[indice, 'INFORMACAO']
                        print(f"- [CHAVE]: {identificador} | CONSIDERAR_FERIADOS_MUNICIPAIS: {informacao} | TIPO: {type(informacao)}")
                        if not pd.isna(informacao):
                            self.marcar_checkbox_considerar_feriadosMunicipais(driver, informacao)
                            return [True, '']
                    except Exception as e:
                        msg = f"[except][get_considerar_feriadosMunicipais_and_marcar]: {e}"
                        print(f"- {msg}")
                        return [False, msg]
            else:
                continue
        else:
            msg = "[não informado: mantido o padrão do PJe-Calc][get_considerar_feriadosMunicipais_and_marcar]"
            print(f"- {msg}")
            return [False, msg]

    # [OLD]
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

        if booleano_da_planilha(self.projetar_aviso_previo_indenizado) is True:
            campo_projetar = WebDriverWait(driver, self.delay).until(
                EC.element_to_be_clickable((By.ID, 'formulario:projetaAvisoIndenizado')))
            checkbox_projetar = campo_projetar.is_selected()
            # Condição para verificar se o checkbox está habilitador
            if checkbox_projetar:
                print('- Checkbox - Projetar Aviso Prévio Indenizado - Já Habilitado.')
            else:
                print('- Checkbox - Projetar Aviso Prévio Indenizado - Foi Habilitado.')
                campo_projetar.click()
        elif booleano_da_planilha(self.projetar_aviso_previo_indenizado) is False:
            campo_projetar = WebDriverWait(driver, self.delay).until(
                EC.element_to_be_clickable((By.ID, 'formulario:projetaAvisoIndenizado')))
            checkbox_projetar = campo_projetar.is_selected()
            if checkbox_projetar:
                print('- Checkbox - Projetar Aviso Prévio Indenizado - Foi Desabilitado.')
                campo_projetar.click()

        if booleano_da_planilha(self.limitar_avos_ao_periodo_do_calculo) is True:
            campo_limitar = WebDriverWait(driver, self.delay).until(
                EC.element_to_be_clickable((By.ID, 'formulario:limitarAvos')))
            checkbox_limitar = campo_limitar.is_selected()
            if checkbox_limitar:
                print('- Checkbox - Limitar Avos ao Período do Cálculo - Já Habilitado.')
            else:
                print('- Checkbox - Limitar Avos ao Período do Cálculo - Foi Habilitado.')
                campo_limitar.click()
        elif booleano_da_planilha(self.limitar_avos_ao_periodo_do_calculo) is False:
            try:
                campo_limitar = WebDriverWait(driver, self.delay).until(
                    EC.element_to_be_clickable((By.ID, 'formulario:limitarAvos')))
                checkbox_limitar = campo_limitar.is_selected()
                if checkbox_limitar:
                    print('- Checkbox - Limitar Avos ao Período do Cálculo - Foi Desabilitado.')
                    campo_limitar.click()
            except TimeoutException:
                print("- Checkbox - 'Limitar Avos ao Período do Cálculo' - Desativado")

        if booleano_da_planilha(self.zerar_valor_negativo_padrao) is True:
            zerar_val_negativo = WebDriverWait(driver, self.delay).until(
                EC.element_to_be_clickable((By.ID, 'formulario:zeraValorNegativo')))
            checkbox_zerar = zerar_val_negativo.is_selected()
            if checkbox_zerar:
                print('- Checkbox - Zerar Valor Negativo (Padrão) - Já Habilitado.')
            else:
                print('- Checkbox - Zerar Valor Negativo (Padrão) - Foi Habilitado.')
                zerar_val_negativo.click()
        elif booleano_da_planilha(self.zerar_valor_negativo_padrao) is False:
            zerar_val_negativo = WebDriverWait(driver, self.delay).until(
                EC.element_to_be_clickable((By.ID, 'formulario:zeraValorNegativo')))
            checkbox_zerar = zerar_val_negativo.is_selected()
            if checkbox_zerar:
                print('- Checkbox - Zerar Valor Negativo (Padrão) - Foi Desabilitado.')
                zerar_val_negativo.click()

        if booleano_da_planilha(self.considerar_feriados_estaduais) is True:
            considerar_estaduais = WebDriverWait(driver, self.delay).until(
                EC.element_to_be_clickable((By.ID, 'formulario:consideraFeriadoEstadual')))
            checkbox_estaduais = considerar_estaduais.is_selected()
            if checkbox_estaduais:
                print('- Checkbox - Considerar Feriados Estaduais - Já Habilitado.')
            else:
                print('- Checkbox - Considerar Feriados Estaduais - Foi Habilitado.')
                considerar_estaduais.click()
        elif booleano_da_planilha(self.considerar_feriados_estaduais) is False:
            considerar_estaduais = WebDriverWait(driver, self.delay).until(
                EC.element_to_be_clickable((By.ID, 'formulario:consideraFeriadoEstadual')))
            checkbox_estaduais = considerar_estaduais.is_selected()
            if checkbox_estaduais:
                print('- Checkbox - Considerar Feriados Estaduais - Foi Desabilitado.')
                considerar_estaduais.click()

        if booleano_da_planilha(self.considerar_feriados_municipais) is True:
            considerar_municipais = WebDriverWait(driver, self.delay).until(
                EC.element_to_be_clickable((By.ID, 'formulario:consideraFeriadoMunicipal')))
            checkbox_municipais = considerar_municipais.is_selected()
            if checkbox_municipais:
                print('- Checkbox - Considerar Feriados Municipais - Já Habilitado.')
            else:
                print('- Checkbox - Considerar Feriados Municipais - Foi Habilitado.')
                considerar_municipais.click()
        elif booleano_da_planilha(self.considerar_feriados_municipais) is False:
            considerar_municipais = WebDriverWait(driver, self.delay).until(
                EC.element_to_be_clickable((By.ID, 'formulario:consideraFeriadoMunicipal')))
            checkbox_municipais = considerar_municipais.is_selected()
            if checkbox_municipais:
                print('- Checkbox - Considerar Feriados Municipais - Foi Desabilitado.')
                considerar_municipais.click()



    # [CARGA_HORARIA]
    def digitar_cargaHoraria(self, driver, value):

        for _ in range(self.qtdTentativas):
            try:
                # [TRATAMENTO]
                value = f"{value}"

                field = WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.XPATH, '//input[@id="formulario:prazoAvisoInformado"]')))
                field.clear()
                field.send_keys(value)
                print("- [ULTIMA_REMUNERACAO]: [OK]")
                return [True, '']
            except Exception as e:
                print(f"- [except][digitar_qtdDiasAvisoPrevio]: {e}")
                sleep(1)
        else:
            msg = "[tentativas_esgotadas][digitar_qtdDiasAvisoPrevio]"
            print(f"- {msg}")
            return [False, msg]

    def get_cargaHoraria_and_digitar(self, driver):

        for indice, identificador in enumerate(self.planilha_base['IDENTIFICADOR']):
            # [TRATAR_VALORES_EM_BRANCO]
            if not pd.isna(identificador):
                if 'quantidade_dias_aviso_previo' in identificador:
                    try:
                        informacao = self.planilha_base.loc[indice, 'INFORMACAO']
                        print(f"- [CHAVE]: {identificador} | QUANTIDADE_DIAS_AVISO_PREVIO: {informacao} | TIPO: {type(informacao)}")
                        if not pd.isna(informacao):
                            # CONVERTER PARA INTEIRO
                            try:
                                valor = int(informacao)
                                self.digitar_qtdDiasAvisoPrevio(driver, valor)
                                return [True, '']
                            except Exception as e:
                                print(f"- [except][get_qtdDiasAvisoPrevio_and_digitar][conversao]: {e}")
                                return [False, '']
                        else:
                            return [False, '']

                    except Exception as e:
                        msg = f"[except][get_qtdDiasAvisoPrevio_and_digitar]: {e}"
                        print(f"- {msg}")
                        return [False, msg]
            else:
                continue
        else:
            msg = "[não informado: mantido o padrão do PJe-Calc][get_qtdDiasAvisoPrevio_and_digitar]"
            print(f"- {msg}")
            return [False, msg]



    # [OLD]
    def preencher_cargaHoraria(self, driver):

        for i in range(len(self.planilha_base)):

            coluna_identificador = self.planilha_base.loc[i, 'IDENTIFICADOR']
            coluna_informacao = self.planilha_base.loc[i, 'INFORMACAO']

            # Condição para pular as linhas em branco da coluna Identificador na planilha base
            if type(coluna_identificador) == type(self.var_controle_float):
                # print('* Pulando linhas em branco ...')
                continue
            elif coluna_identificador == "carga_horaria":
                carga_horaria = numero_da_planilha(coluna_informacao)
                print('- Carga Horária: ', coluna_informacao)
                if carga_horaria is not None:
                    # O campo já vem com 220,00: sem limpar, o valor digitado não substitui o padrão.
                    campo_carga_horaria = WebDriverWait(driver, self.delay).until(
                        EC.presence_of_element_located((By.NAME, 'formulario:valorCargaHorariaPadrao')))
                    campo_carga_horaria.send_keys(Keys.CONTROL, 'a')
                    campo_carga_horaria.send_keys(Keys.DELETE)
                    campo_carga_horaria.send_keys('{:.2f}'.format(carga_horaria))
                break




    # [OLD]
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

        if booleano_da_planilha(self.sabado_como_dia_util) is True:
            campo_sabado_util = WebDriverWait(driver, self.delay).until(
                EC.element_to_be_clickable((By.ID, 'formulario:sabadoDiaUtil')))
            checkbox_sabado = campo_sabado_util.is_selected()
            if checkbox_sabado:
                print('- Checkbox - Sábado como Dia Útil - Já Habilitado.')
            else:
                print('- Checkbox - Sábado como Dia Útil - Foi Habilitado.')
                campo_sabado_util.click()
        elif booleano_da_planilha(self.sabado_como_dia_util) is False:
            campo_sabado_util = WebDriverWait(driver, self.delay).until(
                EC.element_to_be_clickable((By.ID, 'formulario:sabadoDiaUtil')))
            checkbox_sabado = campo_sabado_util.is_selected()
            if checkbox_sabado:
                print('- Checkbox - Sábado como Dia Útil - Foi Desabilitado.')
                campo_sabado_util.click()


    # [PONTOS_FACULTATIVOS]
    def remover_ponto_facultativo_carnaval(self, driver):

        try:
            # Aguarda até que os elementos da tabela estejam visíveis
            elementos = WebDriverWait(driver, self.delay).until(EC.presence_of_all_elements_located((By.XPATH, '//tr[contains(@class, "rich-table-row")]')))

            # Itera sobre os elementos encontrados para verificar se contêm o texto "CORPUS CHRISTI"
            for indice, elemento in enumerate(elementos):
                # Procura pela célula que contém o texto
                celula_texto = elemento.find_element(By.XPATH, './td[contains(@class, "rich-table-cell")][2]')  # Índice [2] refere-se à segunda célula <td>
                # print(f"{indice}) - {celula_texto.text}")
                if celula_texto.text == "CARNAVAL":
                    # print(f"- [LOCALIZADO]: {indice}) - {celula_texto.text}")
                    # Encontra o link para clicar baseado no id do primeiro elemento <td>
                    link_para_clicar = elemento.find_element(By.XPATH, f'./td[@id="formulario:listagemPontosFacultativos:{indice}:j_id578"]/a[contains(@class, "linkExcluir")]')
                    link_para_clicar.click()
                    break
        except Exception as e:
            print(f"- [except][remover_ponto_facultativo_carnaval]: {e}")

    def remover_ponto_facultativo_corpus_christi(self, driver):

        try:
            # Aguarda até que os elementos da tabela estejam visíveis
            elementos = WebDriverWait(driver, self.delay).until(EC.presence_of_all_elements_located((By.XPATH, '//tr[contains(@class, "rich-table-row")]')))

            # Itera sobre os elementos encontrados para verificar se contêm o texto "CORPUS CHRISTI"
            for indice, elemento in enumerate(elementos):
                # Procura pela célula que contém o texto
                celula_texto = elemento.find_element(By.XPATH, './td[contains(@class, "rich-table-cell")][2]')  # Índice [2] refere-se à segunda célula <td>
                # print(f"{indice}) - {celula_texto.text}")
                if celula_texto.text == "CORPUS CHRISTI":
                    # print(f"- [LOCALIZADO]: {indice}) - {celula_texto.text}")
                    # Encontra o link para clicar baseado no id do primeiro elemento <td>
                    link_para_clicar = elemento.find_element(By.XPATH, f'./td[@id="formulario:listagemPontosFacultativos:{indice}:j_id578"]/a[contains(@class, "linkExcluir")]')
                    link_para_clicar.click()
                    break
        except Exception as e:
            print(f"- [except][remover_ponto_facultativo_corpus_christi]: {e}")

    def remover_ponto_facultativo_sexta_santa(self, driver):

        try:
            # Aguarda até que os elementos da tabela estejam visíveis
            elementos = WebDriverWait(driver, self.delay).until(EC.presence_of_all_elements_located((By.XPATH, '//tr[contains(@class, "rich-table-row")]')))

            # Itera sobre os elementos encontrados para verificar se contêm o texto "CORPUS CHRISTI"
            for indice, elemento in enumerate(elementos):
                # Procura pela célula que contém o texto
                celula_texto = elemento.find_element(By.XPATH, './td[contains(@class, "rich-table-cell")][2]')  # Índice [2] refere-se à segunda célula <td>
                # print(f"{indice}) - {celula_texto.text}")
                if celula_texto.text == "SEXTA-FEIRA SANTA":
                    # print(f"- [LOCALIZADO]: {indice}) - {celula_texto.text}")
                    # Encontra o link para clicar baseado no id do primeiro elemento <td>
                    link_para_clicar = elemento.find_element(By.XPATH, f'./td[@id="formulario:listagemPontosFacultativos:{indice}:j_id578"]/a[contains(@class, "linkExcluir")]')
                    link_para_clicar.click()
                    break
        except Exception as e:
            print(f"- [except][remover_ponto_facultativo_sexta_santa]: {e}")

    def ler_pontos_facultativos(self):
        """v3.41: aba PJE-DIV (B3 a D3). Planilha do SAP, sem PJE-DIV: chaves ponto_facultutativo_* da PJE-BD (grafia da v3.41)."""
        with pd.ExcelFile(self.source) as arquivo:
            tem_pje_div = "PJE-DIV" in arquivo.sheet_names
        if tem_pje_div:
            planilha = pd.read_excel(self.source, sheet_name="PJE-DIV", header=1)
            print("- [PONTO_FACULTATIVO][PJE-DIV]: ", planilha.iloc[0, 0])
            return planilha.iloc[0, 1], planilha.iloc[0, 2], planilha.iloc[0, 3]  # B3, C3, D3
        valores = {}
        for indice, identificador in enumerate(self.planilha_base['IDENTIFICADOR']):
            if isinstance(identificador, str):
                valores[identificador.strip()] = self.planilha_base.loc[indice, 'INFORMACAO']
        return (valores.get('ponto_facultutativo_sextafeirasanta'),
                valores.get('ponto_facultutativo_corpuschristi'),
                valores.get('ponto_facultutativo_carnaval'))

    def definir_ponto_facultativo(self, driver):

        sexta_feira_santa, corpus_christi, carnaval = self.ler_pontos_facultativos()

        print("- [PONTO_FACULTATIVO]: ", sexta_feira_santa, carnaval, corpus_christi)
        if booleano_da_planilha(sexta_feira_santa) is False:
            self.remover_ponto_facultativo_sexta_santa(driver)

        if booleano_da_planilha(corpus_christi) is False:
            self.remover_ponto_facultativo_corpus_christi(driver)

        if booleano_da_planilha(carnaval) is False:
            self.remover_ponto_facultativo_carnaval(driver)


    # [OLD]
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
                if valor_vazio(comentarios_parametros):
                    break
                else:
                    # Preencher PJeCalc
                    comentarios = WebDriverWait(driver, self.delay).until(
                        EC.presence_of_element_located((By.NAME, 'formulario:comentarios')))
                    comentarios.send_keys(comentarios_parametros)
                    break


    def main_dados_calculo_bkp(self, driver):

        dados_processo = self.identificacao_processo(driver)
        id_processo = dados_processo[0]
        numero_processo = dados_processo[1]
        # Tempo de Controle
        sleep(self.delayG)
        self.preencher_valor_causa(driver)
        # Tempo de Controle
        sleep(self.delayG)
        nome_reclamente = self.preencher_nome_reclamante(driver)
        # Tempo de controle
        sleep(self.delayG)
        self.preencher_documento_reclamente(driver)
        # Tempo de controle
        sleep(self.delayG)
        self.preencher_advogado(driver)
        # Tempo de controle
        sleep(self.delayG)
        self.preencher_reclamado(driver)
        # Tempo de Controle
        sleep(self.delayG)
        self.preencher_advogado_parte2(driver)
        # Tempo de Controle
        sleep(self.delayG)
        # Parâmetros do Cálculo
        self.aba_parametros_calculo(driver)
        # Tempo de controle
        sleep(self.delayG)
        self.preencher_estado_municipio(driver)
        # Tempo de controle
        sleep(self.delayG)
        datas = self.preencher_datas_calculo(driver)
        admissao = datas[0]
        rescisao = datas[1]
        # Tempo de controle
        sleep(self.delayG)
        escopo_calc = self.limitar_calculo(driver)
        inicio_calculo = escopo_calc[0]
        termino_calculo = escopo_calc[1]
        # Tempo de controle
        sleep(self.delayG)
        self.aplicar_prescricao_verbas_fgts(driver)
        # Tempo de controle
        sleep(self.delayG)
        self.selecionar_regime_trabalho(driver)
        # Tempo de controle
        sleep(self.delayG)
        self.selecionar_prazo_aviso_previo(driver)
        # Tempo de controle
        sleep(self.delayG)
        self.checkboxs(driver)
        # Tempo de controle
        sleep(self.delayG)
        self.preencher_maior_ultima_remuneracao(driver)
        # Tempo de controle
        sleep(self.delayG)
        self.preencher_cargaHoraria(driver)
        # Tempo de controle
        sleep(self.delayG)
        self.sabadoUtil(driver)
        # Tempo de controle
        sleep(self.delayG)
        # Somente para versão v.34 da planilha base
        self.definir_ponto_facultativo(driver)
        # Tempo de controle
        sleep(self.delayG)
        self.preencher_comentarios(driver)
        # Tempo de controle
        sleep(self.delayG)
        self.salvar(driver)
        self.objTools.aguardar_carregamento(driver)
        sleep(self.delayG)
        self.salvar(driver)
        # Aguardar Processamento
        self.objTools.aguardar_carregamento(driver)
        sleep(self.delayG)
        self.verificacao_new(driver)
        print('# ========== [DADOS_CALCULO] ========== #')

        # [Limpar_arquivos_temporarios]
        self.objTools.limparFilesTemp()

        return [nome_reclamente, id_processo, admissao, rescisao, inicio_calculo, termino_calculo, numero_processo]

    def main_dados_calculo(self, driver):


        self.get_id_processo()
        self.get_numero_processo_and_digitar(driver)
        sleep(self.delayDefault)

        self.get_valor_causa_and_digitar(driver)
        sleep(self.delayDefault)

        self.get_nomeReclamante_and_digitar(driver)
        sleep(self.delayDefault)

        self.get_numeroDocReclamante_and_digitar(driver)
        sleep(self.delayDefault)

        if not self.lancar_advogados_do_pedido(driver, "reclamante"):
            self.get_nomeAdvogadoReclamante_and_digitar(driver)
        sleep(self.delayDefault)

        self.get_nomeReclamado_and_digitar(driver)
        sleep(self.delayDefault)

        self.get_numeroDocReclamado_and_digitar(driver)
        sleep(self.delayDefault)

        if not self.lancar_advogados_do_pedido(driver, "reclamado"):
            self.get_nomeAdvogadoReclamado_and_digitar(driver)
        sleep(self.delayDefault)

        self.clicar_aba_parametrosCalculo(driver)
        sleep(self.delayG)

        self.get_estadoCalculo_and_digitar(driver)
        sleep(self.delayDefault)

        self.get_municipioCalculo_and_digitar(driver)
        sleep(self.delayDefault)

        self.get_dtAdmissao_and_digitar(driver)
        sleep(self.delayDefault)

        self.get_dtDemissao_and_digitar(driver)
        sleep(self.delayDefault)

        self.get_dtAjuizamento_and_digitar(driver)
        sleep(self.delayDefault)

        self.get_dtInicialCalc_and_digitar(driver)
        sleep(self.delayDefault)

        self.get_dtFinalCalc_and_digitar(driver)
        sleep(self.delayDefault)

        self.get_aplicar_prescricaoVerbas_and_aplicar(driver)
        sleep(self.delayDefault)

        self.get_aplicar_prescricaoFGTS_and_digitar(driver)
        sleep(self.delayDefault)

        self.get_regimeTrabalho_and_selecionar(driver)
        sleep(self.delayDefault)

        self.get_maiorRemuneracao_and_digitar(driver)
        sleep(self.delayDefault)

        self.get_ultimaRemuneracao_and_digitar(driver)
        sleep(self.delayDefault)

        retorno_function = self.get_prazoAvisoPrevio_and_selecionar(driver)
        sleep(self.delayDefault)

        if retorno_function[0] and 'Informado' in retorno_function[1]:
            self.get_qtdDiasAvisoPrevio_and_digitar(driver)


        # ----------------------- [Antigo] ----------------------- #

        # self.aplicar_prescricao_verbas_fgts(driver)
        # Tempo de controle
        # sleep(self.delayG)
        # self.selecionar_regime_trabalho(driver)
        # # Tempo de controle
        # sleep(self.delayG)
        # self.selecionar_prazo_aviso_previo(driver)
        # Tempo de controle
        # sleep(self.delayG)
        self.checkboxs(driver)
        # Tempo de controle
        sleep(self.delayG)
        # self.preencher_maior_ultima_remuneracao(driver)
        # Tempo de controle
        # sleep(self.delayG)
        self.preencher_cargaHoraria(driver)
        # Tempo de controle
        sleep(self.delayG)
        self.sabadoUtil(driver)
        # Tempo de controle
        sleep(self.delayG)
        # Somente para versão v.34 da planilha base
        self.definir_ponto_facultativo(driver)
        # Tempo de controle
        sleep(self.delayG)
        self.preencher_comentarios(driver)
        # Tempo de controle
        sleep(self.delayG)
        # -------------------------------------------------------- #

        self.clicar_btnSalvar(driver)
        self.objTools.aguardar_carregamento(driver)
        sleep(self.delayG)
        self.verificacao_new(driver)
        print('# ========== [DADOS_CALCULO] ========== #')

        # [Limpar_arquivos_temporarios]
        self.objTools.limparFilesTemp()

        return [self.nome_parte1, self.id_processo, self.datetime_admissao, self.datetime_demissao, self.datetime_inicio_calc, self.datetime_final_calc, self.numero_processo]
