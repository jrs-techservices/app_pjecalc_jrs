from selenium.webdriver.support.wait import WebDriverWait, TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from time import sleep
import os
import pandas as pd
#
from Tools.pjecalc_control import Control
from browser_pjecalc import WebDriver


class Verbas:

    delay = 10

    # NOVO TRECHO (Início)

    # planilha_base = pd.read_excel(os.getcwd() + "\TBVERBA_v2.xlsm", sheet_name="TBVERBABD")
    planilha_base = pd.read_excel(os.getcwd() + "\TBVERBA_v2.xlsm", sheet_name="TBVERBABD")

    # --------------------- PJeCalc - Página Inicial --------------------- #
    def importarCalculo(self, driver):
        WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.CSS_SELECTOR, '.sprite-importar > a:nth-child(1)'))).click()

    def esolherArquivo(self, driver):
        arquivo_base = os.getcwd() + r"\automacao_verbas.PJC"
        # print("- ", arquivo_base)
        WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.NAME, "formulario:arquivo:file"))).send_keys(arquivo_base)

    def confirmarOperacao(self, driver):
        WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, "formulario:confirmarImportacao"))).click()

    # --------------------- PJeCalc - Verificação --------------------- #

    def verificar_verba_criada(self, driver):

        def gerar_relatorio(campo, status):
            file_txt_log = open(os.getcwd() + '\log.txt', "a")
            file_txt_log.write(f'- {campo} | {status}\n')
            return file_txt_log.close()

        try:
            mensagem = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.ID, 'formulario:painelMensagens:j_id77')))
            msg = mensagem.text
            if 'Operação realizada com sucesso.' in msg:
                print('* Operação realizada com sucesso.')
                gerar_relatorio('Verbas: Nova verba criada', 'Ok')
            else:
                print('* ERRO!', msg)
                gerar_relatorio('Verbas: Nova verba criada ', '---------- Erro! ----------')
        except TimeoutException:
            print('* Exceção - Verificação -  A Página demorou para responder ou o elemento não foi encontrado. Encerrando...')
            exit()

    def verificacao(self, driver):

        def gerar_relatorio(campo, status):
            file_txt_log = open(os.getcwd() + '\log.txt', "a")
            file_txt_log.write(f'- {campo} | {status}\n')
            return file_txt_log.close()
        try:
            mensagem = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.ID, 'formulario:painelMensagens:j_id77'))).text
            if 'Operação realizada com sucesso.' in mensagem:
                print('* Operação realizada com sucesso.')
                gerar_relatorio('Verbas', 'Ok')
            else:
                print('* ERRO!', mensagem)
                gerar_relatorio('Verbas', '---------- Erro! ----------')
        except TimeoutException:
            print('!! (Elemento não foi encontrado/ A Página demorou para responder / Erro na página) Encerrando... !!')
            exit()

    # --------------------- PJeCalc - Verbas - Página Inicial --------------------- #

    def acessarVerbas(self, driver):
        WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.CLASS_NAME, "menuImageVerba"))).click()

    def acessarExpresso(self, driver):
        WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, "formulario:lancamentoExpresso"))).click()

    def selecionarVerbaPrincipal(self, driver, valor):

        # PRÊMIO PRODUÇÃO

        indice = 0
        statusWhile = True

        try:
            while statusWhile:

                # nome_verba = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.ID, f'formulario:j_id90:{indice}:j_id92:0:nome'))).text

                listagem_verbas = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.ID, f'formulario:j_id90:{indice}:j_id92:0:nome')))
                nome_verba = listagem_verbas.get_attribute("textContent")

                # print(indice, " - ", nome_verba)

                if valor == nome_verba:
                    # print(indice, " - Lista: ", nome_verba, " | - Definida: ", valor)
                    WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.ID, f'formulario:j_id90:{indice}:j_id92:0:selecionada'))).click()
                    # print("- Verba encontrada na Coluna 1.")
                    statusWhile = False

                indice += 1
        except TimeoutException:

            # print("- Verba não localizada na Coluna 1.")

            indice = 0
            statusWhile = True
            try:
                while statusWhile:

                    # nome_verba = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.ID, f'formulario:j_id90:{indice}:j_id92:1:nome'))).text

                    listagem_verbas2 = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.ID, f'formulario:j_id90:{indice}:j_id92:1:nome')))
                    nome_verba2 = listagem_verbas2.get_attribute("textContent")
                    # print(indice, " - ", nome_verba2)

                    if valor == nome_verba2:
                        # print(indice, " - Lista: ", nome_verba2, " | - Definida: ", valor)
                        WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.ID, f'formulario:j_id90:{indice}:j_id92:1:selecionada'))).click()
                        # print("- Verba encontrada na Coluna 2.")
                        statusWhile = False

                    indice += 1
            except TimeoutException:
                # print("- Verba não localizada na Coluna 2.")

                indice = 0
                statusWhile = True

                try:
                    while statusWhile:

                        # nome_verba = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.ID, f'formulario:j_id90:{indice}:j_id92:2:nome'))).text
                        listagem_verbas3 = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.ID, f'formulario:j_id90:{indice}:j_id92:2:nome')))
                        nome_verba3 = listagem_verbas3.get_attribute("textContent")

                        # print(indice, " - ", nome_verba3)

                        if valor == nome_verba3:
                            # print(indice, " - Lista: ", nome_verba3, " | - Definida: ", valor)
                            WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.ID, f'formulario:j_id90:{indice}:j_id92:2:selecionada'))).click()
                            # print("- Verba encontrada na Coluna 3.")
                            statusWhile = False

                        indice += 1
                except TimeoutException:
                    # print("- Verba não encontrada na lista do PJeCalc.")
                    exit()


        del valor
        del indice

    def salvarOperacao(self, driver):

        btn_salvar = WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.XPATH, "//*[@id='formulario:salvar']")))
        valor_btn = btn_salvar.get_attribute("value")
        if "Salvar" in valor_btn:
            btn_salvar.click()

    def acessarParametrosVerba(self, driver):
        WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, "formulario:listagem:0:j_id566"))).click()

    def acessarParametrosVerbaPreechida(self, driver, valor):


        statusWhile = True
        indice = 0

        try:
            while statusWhile:
                coluna_verba = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.ID, f'formulario:listagem:{str(indice)}:j_id569'))).text

                if valor == coluna_verba:
                    WebDriverWait(driver, 3).until(EC.element_to_be_clickable((By.ID, f'formulario:listagem:{str(indice)}:j_id566'))).click()
                    statusWhile = False

                indice += 1
        except TimeoutException:
            pass

        del valor
        del indice

    # --------------------- PJECALC - VERBAS - DADOS DA VERBA --------------------- #

    # STPPARCELA
    def marcar_stpparcela(self, driver, valor):

        if valor == 'F':
            WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, "formulario:tipoVariacaoDaParcela:0"))).click()
        elif valor == 'V':
            WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, "formulario:tipoVariacaoDaParcela:1"))).click()

        del valor

    # STPVALOR
    def marcar_stpvalor(self, driver, valor):

        if valor == 'C':
            WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, "formulario:valor:0"))).click()
        elif valor == 'I':
            WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, "formulario:valor:1"))).click()

        del valor

    # SNMDESCRICAOVERBA
    def modificar_snmdescricaoverba(self, driver, nome):

        campo_nome = WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.ID, "formulario:descricao")))
        campo_nome.send_keys(Keys.CONTROL, "a")
        campo_nome.send_keys(nome)

        del nome

    # SFLINCIDENCIAIRPF
    def marcar_sflincidenciairpf(self, driver, valor):

        elementoCheckbox = WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, "formulario:irpf")))
        situacaoCheckbox = elementoCheckbox.is_selected()

        if valor == 'S':
            if not situacaoCheckbox:
                elementoCheckbox.click()
        elif valor == 'N':
            if situacaoCheckbox:
                elementoCheckbox.click()

        del valor

    # SFLINCIDENCIAFGTS
    def marcar_sflincidenciafgts(self, driver, valor):

        elementoCheckbox = WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, "formulario:fgts")))
        situacaoCheckbox = elementoCheckbox.is_selected()

        if valor == 'S':
            if not situacaoCheckbox:
                elementoCheckbox.click()

        elif valor == 'N':
            if situacaoCheckbox:
                elementoCheckbox.click()

        del valor

    # SFLINCIDENCIAINSS
    def marcar_sflincidenciainss(self, driver, valor):

        elementoCheckbox = WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, "formulario:inss")))
        situacaoCheckbox = elementoCheckbox.is_selected()

        if valor == 'S':
            if not situacaoCheckbox:
                elementoCheckbox.click()
        elif valor == 'N':
            if situacaoCheckbox:
                elementoCheckbox.click()

        del valor

    # SFLINCIDENCIAPREVPRIVADA
    def marcar_sflincidenciaprevprivada(self, driver, valor):

        elementoCheckbox = WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, "formulario:previdenciaPrivada")))
        situacaoCheckbox = elementoCheckbox.is_selected()

        if valor == 'S':
            if not situacaoCheckbox:
                elementoCheckbox.click()
        elif valor == 'N':
            if situacaoCheckbox:
                elementoCheckbox.click()

        del valor

    # SFLINCIDENCIAPENSAO
    def marcar_sflincidenciapensao(self, driver, valor):

        elementoCheckbox = WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, "formulario:pensaoAlimenticia")))
        situacaoCheckbox = elementoCheckbox.is_selected()

        if valor == 'S':
            if not situacaoCheckbox:
                elementoCheckbox.click()
        elif valor == 'N':
            if situacaoCheckbox:
                elementoCheckbox.click()

        del valor

    # SFLCOMPORPRINCIPAL
    def marcar_sflcomporprincipal(self, driver, valor):

        if valor == 'S':
            WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, "formulario:comporPrincipal:0"))).click()
        else:
            WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, "formulario:comporPrincipal:1"))).click()

        del valor

    # SFLPADRAOZERARVALORNEGATIVO
    def marcar_sflpadraozerarvalornegativo(self, driver, valor):

        elementoCheckbox = WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, "formulario:zeraValorNegativo")))
        situacaoCheckbox = elementoCheckbox.is_selected()

        if valor == 'S':
            if not situacaoCheckbox:
                elementoCheckbox.click()
        elif valor == 'N':
            if situacaoCheckbox:
                elementoCheckbox.click()

        del valor

    # -- STPCARACTERISTICAVERBA
    def marcar_stpcaracteristicaverba(self, driver, valor):

        # - GABARITO
        # C: Comum
        # DT: Décimo Terceiro
        # AP: Aviso Prévio
        # F: Férias

        if valor == 'C':
            WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, 'formulario:caracteristicaVerba:0'))).click()
        elif valor == 'DT':
            WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, 'formulario:caracteristicaVerba:1'))).click()
        elif valor == 'AP':
            WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, 'formulario:caracteristicaVerba:2'))).click()
        elif valor == 'F':
            WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, 'formulario:caracteristicaVerba:3'))).click()

        del valor

    # -- STPOCORRENCIAPAGAMENTO
    def marcar_stpocorrenciapagamento(self, driver, valor):

        # - GABARITO
        # DL: Desligamento
        # DZ: Dezembro
        # M: Mensal
        # PA: Período Aquisitivo

        elemento = WebDriverWait(driver, self.delay).until(EC.visibility_of_element_located((By.NAME, 'formulario:ocorrenciaPagto')))
        if elemento.is_enabled():

            if valor == 'DL':
                WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, 'formulario:ocorrenciaPagto:0'))).click()
            elif valor == 'DZ':
                WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, 'formulario:ocorrenciaPagto:1'))).click()
            elif valor == 'M':
                WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, 'formulario:ocorrenciaPagto:2'))).click()
            elif valor == 'PA':
                WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, 'formulario:ocorrenciaPagto:3'))).click()

        del valor

    # -- STPJUROSSUMULA
    def marcar_stpjurossumula(self, driver, valor):

        if valor == 'S':
            WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, 'formulario:ocorrenciaAjuizamento:0'))).click()
        else:
            WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, 'formulario:ocorrenciaAjuizamento:1'))).click()

        del valor

    # -- STPTIPOVERBA
    def marcar_stptipoverba(self, driver, valor):

        try:

            if WebDriverWait(driver, self.delay).until(EC.visibility_of_element_located((By.NAME, 'formulario:tipoDeVerba'))):
                elemento = WebDriverWait(driver, self.delay).until(EC.visibility_of_element_located((By.NAME, 'formulario:tipoDeVerba')))
                if elemento.is_enabled():
                    if valor == 'P':
                        WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, 'formulario:tipoDeVerba:0'))).click()
                    elif valor == 'R':
                        WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, 'formulario:tipoDeVerba:1'))).click()

        except TimeoutException:
            pass


        del valor

    # -- STPGERARVERBAREFLEXA
    def marcar_stpgerarverbareflexa(self, driver, valor):

        if valor == 'DV':
            WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, 'formulario:geraReflexo:0'))).click()
        elif valor == 'DF':
            WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, 'formulario:geraReflexo:1'))).click()

        del valor

    # -- STPGERARVERBAPRINCIPAL
    def marcar_stpgerarverbaprincipal(self, driver, valor):

        if valor == 'DV':
            WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, 'formulario:gerarPrincipal:0'))).click()
        elif valor == 'DF':
            WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, 'formulario:gerarPrincipal:1'))).click()

        del valor


    # --------------------- PJeCalc - Verbas - Dados de Verba - (Incompletas) --------------------- #

    def selecionarAssuntoCNJ(self, driver):
        WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, 'formulario:linkModalAssunto'))).click()

    def definirAssuntoCNJ(self, driver, valor):

        assunto = valor.split(" ")
        id_assunto = assunto[0]
        # print("- Assunto: ", assunto, "- Id Assunto: ", id_assunto)

        try:
            WebDriverWait(driver, 3).until(EC.element_to_be_clickable((By.ID, f'formularioModalCNJ:arv:864:{id_assunto}::_defaultNodeFaceOutput'))).click()
        except TimeoutException:
            # 864 - Direito do Trabalho -- formularioModalCNJ:arv:864::_defaultNodeFaceOutput
            WebDriverWait(driver, 3).until(EC.element_to_be_clickable((By.ID, 'formularioModalCNJ:arv:864::_defaultNodeFaceOutput'))).click()

    def btnSelecionarAssuntoCNJ(self, driver):
        WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, 'btnSelecionarCNJ'))).click()


    # --------------------- PJECALC - VERBAS - VALOR DEVIDO - PERÍODO --------------------- #
    # DDTINICIO
    def modificar_ddtinicio(self, driver, valor):

        dataInicial = valor.strftime('%d/%m/%Y')

        campoPeriodoInicial = WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.NAME, "formulario:periodoInicialInputDate")))
        campoPeriodoInicial.click()
        campoPeriodoInicial.send_keys(dataInicial)

        del valor

    # DDTTERMINO
    def modificar_ddttermino(self, driver, valor):

        dataFinal = valor.strftime('%d/%m/%Y')

        campoPeriodoFinal = WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.NAME, "formulario:periodoFinalInputDate")))
        campoPeriodoFinal.click()
        campoPeriodoFinal.send_keys(dataFinal)

        del valor

    # --------------------- PJECALC - VERBAS - VALOR DEVIDO - EXCLUSÕES --------------------- #

    # SFLEXCLUIRFALTAJUSTIFICADA
    def marcar_sflexcluirfaltajustificada(self, driver, valor):

        elementoCheckbox = WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, "formulario:excluirFaltaJustificada")))
        situacaoCheckbox = elementoCheckbox.is_selected()
        if valor == 'S':
            if not situacaoCheckbox:
                elementoCheckbox.click()
        elif valor == 'N':
            if situacaoCheckbox:
                elementoCheckbox.click()

        del valor

    # SFLEXCLUIRFALTANAOJUSTIFICADA
    def marcar_sflexcluirfaltanaojustificada(self, driver, valor):

        elementoCheckbox = WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, "formulario:excluirFaltaNaoJustificada")))
        situacaoCheckbox = elementoCheckbox.is_selected()
        if valor == 'S':
            if not situacaoCheckbox:
                elementoCheckbox.click()
        elif valor == 'N':
            if situacaoCheckbox:
                elementoCheckbox.click()

        del valor

    # SFLEXCLUIRFERIASGOZADAS
    def marcar_sflexcluirferiasgozadas(self, driver, valor):

        elementoCheckbox = WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, "formulario:excluirFeriasGozadas")))
        situacaoCheckbox = elementoCheckbox.is_selected()
        if valor == 'S':
            if not situacaoCheckbox:
                elementoCheckbox.click()
        elif valor == 'N':
            if situacaoCheckbox:
                elementoCheckbox.click()

        del valor

    # SFLDOBRARVALOR
    def marcar_sfldobrarvalor(self, driver, valor):

        try:
            if WebDriverWait(driver, 2).until(EC.visibility_of_element_located((By.ID, "formulario:dobraValorDevido"))):
                elementoCheckbox = WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, "formulario:dobraValorDevido")))
                situacaoCheckbox = elementoCheckbox.is_selected()
                if valor == 'S':
                    if not situacaoCheckbox:
                        elementoCheckbox.click()
                elif valor == 'N':
                    if situacaoCheckbox:
                        elementoCheckbox.click()

        except TimeoutException:
            pass

        del valor

    # RVLVALORDEVIDO
    def modificar_rvlvalordevido(self, driver, valor):

        try:

            if WebDriverWait(driver, 2).until(EC.visibility_of_element_located((By.ID, "formulario:valorInformadoDoDevido"))):
                val = f"{valor:.2f}"
                WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.NAME, 'formulario:valorInformadoDoDevido'))).send_keys(val)

        except TimeoutException:
            pass


        del valor

    # SFLPROPORCIONALIDADE
    def marcar_sflproporcionalidade(self, driver, valor):

        try:

            if WebDriverWait(driver, 2).until(EC.visibility_of_element_located((By.ID, "formulario:aplicarProporcionalidadeAoValorDevido"))):
                elementoCheckbox = WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, "formulario:aplicarProporcionalidadeAoValorDevido")))
                situacaoCheckbox = elementoCheckbox.is_selected()
                if valor == 'S':
                    if not situacaoCheckbox:
                        elementoCheckbox.click()
                elif valor == 'N':
                    if situacaoCheckbox:
                        elementoCheckbox.click()

        except TimeoutException:
            pass

        del valor

    # --------------------- PJECALC - VERBAS - VALOR DEVIDO - FORMULA - BASE DE CÁLCULO --------------------- #
    # STPBASEDEVIDO
    def modificar_stpbasedevido(self, driver, valor):

        # GABARITO
        # MR: Maior Remuneração
        # HS: Histórico Salarial
        # PS: Piso Salarial
        # SM: Salário Mínimo
        # VT: Vale Transporte

        campoSelecaoBases = WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.NAME, 'formulario:tipoDaBaseTabelada')))
        selecaoBases = Select(campoSelecaoBases)

        if valor == 'MR':
            selecaoBases.select_by_visible_text('Maior Remuneração')
        elif valor == 'HS':
            selecaoBases.select_by_visible_text('Histórico Salarial')
        elif valor == 'PS':
            selecaoBases.select_by_visible_text('Piso Salarial')
        elif valor == 'SM':
            selecaoBases.select_by_visible_text('Salário Mínimo')
        elif valor == 'VT':
            selecaoBases.select_by_visible_text('Vale Transporte')


        del valor


    # ----

    def definirHistoricoSalarial(self, driver, valor):
        campoHistoricoSalarial = WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.NAME, 'formulario:baseHistoricos')))
        selecaoHistorico = Select(campoHistoricoSalarial)
        selecaoHistorico.select_by_visible_text(valor)

        del valor

    def proporcionalizar(self, driver, valor):

        positivo = 'Sim'
        negativo = 'Não'

        campoProporcionalizar = WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.NAME, 'formulario:proporcionalizaHistorico')))
        selecaoProporcionalizar = Select(campoProporcionalizar)

        if valor == positivo:
            selecaoProporcionalizar.select_by_visible_text(negativo)
            selecaoProporcionalizar.select_by_visible_text(valor)
        else:
            selecaoProporcionalizar.select_by_visible_text(positivo)
            selecaoProporcionalizar.select_by_visible_text(valor)

        del valor

    def adicionarBase(self, driver):
        WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, 'formulario:incluirBaseHistorico'))).click()

    def definirVerba(self, driver, valor):

        try:
            campoVerba = WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.NAME, 'formulario:baseVerbaDeCalculo')))
            selecaoVerba = Select(campoVerba)
            selecaoVerba.select_by_visible_text(valor)
        except NoSuchElementException:
            print("- Verba não encontrada na lista!")

        del valor

    def integralizar(self, driver, valor):
        campoIntegralizar = WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.NAME, 'formulario:integralizarBase')))
        selecaoIntegralizar = Select(campoIntegralizar)
        selecaoIntegralizar.select_by_visible_text(valor)

        del valor

    def adicionarVerba(self, driver):
        WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, 'formulario:incluirItemProp'))).click()

    # --------------------- PJECALC - VERBAS - VALOR DEVIDO - FORMULA - DIVIDOR --------------------- #

    # STPDIVISOR
    def modificar_stpdivisor(self, driver, valor):

        # GABARITO
        # IN: Informado
        # CH: Carga Horária
        # DU: Dias Úteis
        # ICP: Importada do Cartão de Ponto

        if valor == 'IN':
            WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, 'formulario:tipoDeDivisor:0'))).click()
        elif valor == 'CH':
            WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, 'formulario:tipoDeDivisor:1'))).click()
        elif valor == 'DU':
            WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, 'formulario:tipoDeDivisor:2'))).click()
        elif valor == 'ICP':
            WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, 'formulario:tipoDeDivisor:3'))).click()

        del valor

    # RVLOUTRODIVISOR
    def modificar_rvloutrodivisor(self, driver, valor):

        try:
            if WebDriverWait(driver, 2).until(EC.visibility_of_element_located((By.ID, 'formulario:outroValorDoDivisor'))):

                valor = f"{valor:.4f}".replace(".", ",")
                campoValor = WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.NAME, 'formulario:outroValorDoDivisor')))
                campoValor.click()
                campoValor.send_keys(valor)

        except TimeoutException:
            pass

        del valor

    # RVLMULTIPLICADOR
    def modificar_rvlmultiplicador(self, driver, valor):

        try:
            if WebDriverWait(driver, 2).until(EC.visibility_of_element_located((By.ID, 'formulario:outroValorDoMultiplicador'))):

                valor = f"{valor:.8f}".replace(".", ",")
                campoValor = WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.NAME, 'formulario:outroValorDoMultiplicador')))
                campoValor.click()
                campoValor.send_keys(valor)

        except TimeoutException:
            pass

        del valor

    # STPQUANTIDADE
    def marcar_stpquantidade(self, driver, valor):

        # GABARITO
        # IN: Informada
        # ICL: Importada do Calendário
        # ICP: Importada do Cartão de Ponto
        # AV: Avos

        if valor == 'IN':
            WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, 'formulario:tipoDaQuantidade:0'))).click()
        elif valor == 'ICL':
            WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, 'formulario:tipoDaQuantidade:1'))).click()
        elif valor == 'ICP':
            WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, 'formulario:tipoDaQuantidade:2'))).click()
        elif valor == 'AV':
            WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, 'formulario:tipoDaQuantidade:1'))).click()

        del valor

    # STPCALENDARIO
    def modificar_stpcalendario(self, driver, valor):

        # GABARITO
        # RF: Repousos e Feriados
        # R: Repousos
        # F: Feriados
        # DU: Dias Úteis

        try:
            if WebDriverWait(driver, 2).until(EC.visibility_of_element_located((By.NAME, 'formulario:tipoImportadaCalendario'))):

                campoSelecao = WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.NAME, 'formulario:tipoImportadaCalendario')))
                elemento = Select(campoSelecao)

                if valor == 'RF':
                    elemento.select_by_visible_text('Repousos e Feriados/Pontos Facultativos')
                elif valor == 'R':
                    elemento.select_by_visible_text('Repousos')
                elif valor == 'F':
                    elemento.select_by_visible_text('Feriados/Pontos Facultativos')
                elif valor == 'DU':
                    elemento.select_by_visible_text('Dias Úteis')

        except TimeoutException:
            pass


        del valor

    # STPCARTAOPONTO
    def modificar_stpcartaoponto(self, driver, valor):
        pass
        del valor

    # RVLOUTROVALORQTD
    def modificar_rvloutrovalorqtd(self, driver, valor):

        try:
            if WebDriverWait(driver, 2).until(EC.visibility_of_element_located((By.ID, 'formulario:valorInformadoDaQuantidade'))):

                valor = f"{valor:.4f}".replace(".", ",")
                campoValor = WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.NAME, 'formulario:valorInformadoDaQuantidade')))
                campoValor.click()
                campoValor.send_keys(valor)

        except TimeoutException:
            pass

        del valor

    # SFLQTDPROPORCIONALIDADE
    def marcar_sflqtdproporcionalidade(self, driver, valor):

        try:

            if WebDriverWait(driver, 2).until(EC.visibility_of_element_located((By.ID, "formulario:aplicarProporcionalidadeAQuantidade"))):
                elementoCheckbox = WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, "formulario:aplicarProporcionalidadeAQuantidade")))
                situacaoCheckbox = elementoCheckbox.is_selected()
                if valor == 'S':
                    if not situacaoCheckbox:
                        elementoCheckbox.click()
                elif valor == 'N':
                    if situacaoCheckbox:
                        elementoCheckbox.click()

        except TimeoutException:
            pass

        del valor


    # --------------------- PJECALC - VERBAS - VALOR PAGO --------------------- #

    # STPVALORPAGO
    def marcar_stpvalorpago(self, driver, valor):

        # GABARITO
        # I: Informado
        # C: Calculado

        if valor == 'I':
            WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, 'formulario:tipoDoValorPago:0'))).click()
        elif valor == 'C':
            WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, 'formulario:tipoDoValorPago:1'))).click()

        del valor

    # STPBASEPAGO
    def modificar_stpbasepago(self, driver, valor):

        # GABARITO
        # MR: Maior Remuneração
        # HS: Histórico Salarial
        # PS: Piso Salarial
        # SM: Salário Mínimo
        # VT: Vale Transporte

        try:
            if WebDriverWait(driver, 2).until(EC.visibility_of_element_located((By.ID, 'formulario:baseTabelada'))):

                campoSelecaoBases = WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.ID, 'formulario:baseTabelada')))
                selecaoBases = Select(campoSelecaoBases)

                if valor == 'MR':
                    selecaoBases.select_by_visible_text('Maior Remuneração')
                elif valor == 'HS':
                    selecaoBases.select_by_visible_text('Histórico Salarial')
                elif valor == 'PS':
                    selecaoBases.select_by_visible_text('Piso Salarial')
                elif valor == 'SM':
                    selecaoBases.select_by_visible_text('Salário Mínimo')
                elif valor == 'VT':
                    selecaoBases.select_by_visible_text('Vale Transporte')
        except TimeoutException:
            pass

        del valor

    # RVLINOUTROVALOR
    def modificar_rvlinoutrovalor(self, driver, valor):

        try:
            if WebDriverWait(driver, 2).until(EC.visibility_of_element_located((By.ID, 'formulario:valorInformadoPago'))):

                valor = f"{valor:.2f}".replace(".", ",")
                campoValor = WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.NAME, 'formulario:valorInformadoPago')))
                campoValor.click()
                campoValor.send_keys(valor)

        except TimeoutException:
            pass

        del valor

    # SFLVPGPROPORCIONALIDADE
    def marcar_sflvpgproporcionalidade(self, driver, valor):

        try:

            if WebDriverWait(driver, 2).until(EC.visibility_of_element_located((By.ID, "formulario:aplicarProporcionalidadeValorPago"))):
                elementoCheckbox = WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, "formulario:aplicarProporcionalidadeValorPago")))
                situacaoCheckbox = elementoCheckbox.is_selected()
                if valor == 'S':
                    if not situacaoCheckbox:
                        elementoCheckbox.click()
                elif valor == 'N':
                    if situacaoCheckbox:
                        elementoCheckbox.click()

        except TimeoutException:
            pass


        del valor

    # RVLQUANTIDADE
    def modificar_rvlquantidade(self, driver, valor):

        try:
            if WebDriverWait(driver, 2).until(EC.visibility_of_element_located((By.ID, 'formulario:valorPagoQuantidade'))):

                valor = int(valor)
                val = str(valor)
                campoQuantidade = WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.NAME, 'formulario:valorPagoQuantidade')))
                campoQuantidade.click()
                campoQuantidade.send_keys(val)

        except TimeoutException:
            pass

        del valor

    # SDSCOMENTARIO
    def modificar_sdscomentario(self, driver, valor):

        try:
            if WebDriverWait(driver, 2).until(EC.visibility_of_element_located((By.ID, 'formulario:comentarios'))):
                campoComentatios = WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.NAME, 'formulario:comentarios')))
                campoComentatios.click()
                campoComentatios.send_keys(valor)

        except TimeoutException:
            pass

        del valor

    # SFLREFLEXO13TERCEIRO
    def marcar_sflreflexo13terceiro(self, driver, valor, snmdescricaoverba):

        indice = 0
        var_loop = True

        verba_principal = '13º SALÁRIO SOBRE ' + snmdescricaoverba

        try:

            while var_loop:

                elemento_verba_principal = WebDriverWait(driver, 2).until(EC.visibility_of_element_located((By.ID, f'formulario:listagem:0:listaReflexo:{indice}:j_id582')))

                # print("- # WEB: ", elemento_verba_principal.get_attribute("textContent"))
                # print("- # VAR: ", verba_principal)

                if verba_principal == elemento_verba_principal.get_attribute("textContent"):
                    elementoCheckbox = WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, f'formulario:listagem:0:listaReflexo:{indice}:ativo')))
                    situacaoCheckbox = elementoCheckbox.is_selected()

                    if valor == 'S':
                        if not situacaoCheckbox:
                            elementoCheckbox.click()
                            var_loop = False
                    elif valor == 'N':
                        if situacaoCheckbox:
                            elementoCheckbox.click()
                            var_loop = False

                indice += 1

        except TimeoutException:
            pass

        del valor

    # SFLREFLEXOFERIAS
    def marcar_sflreflexoferias(self, driver, valor, snmdescricaoverba):

        indice = 0
        var_loop = True

        # formulario:listagem:0:divDestinacoes
        verba_principal = 'FÉRIAS + 1/3 SOBRE ' + snmdescricaoverba

        try:

            while var_loop:

                elemento_verba_principal = WebDriverWait(driver, 2).until(EC.visibility_of_element_located((By.ID, f'formulario:listagem:0:listaReflexo:{indice}:j_id582')))

                # print("- # WEB: ", elemento_verba_principal.get_attribute("textContent"))
                # print("- # VAR: ", verba_principal)

                if verba_principal == elemento_verba_principal.get_attribute("textContent"):
                    elementoCheckbox = WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, f'formulario:listagem:0:listaReflexo:{indice}:ativo')))
                    situacaoCheckbox = elementoCheckbox.is_selected()

                    if valor == 'S':
                        if not situacaoCheckbox:
                            elementoCheckbox.click()
                            var_loop = False
                    elif valor == 'N':
                        if situacaoCheckbox:
                            elementoCheckbox.click()
                            var_loop = False

                indice += 1

        except TimeoutException:
            pass

        del valor

    # SFLREFLEXOAVISO
    def marcar_sflreflexoaviso(self, driver, valor, snmdescricaoverba):

        indice = 0
        var_loop = True

        # formulario:listagem:0:divDestinacoes
        verba_principal = 'AVISO PRÉVIO SOBRE ' + snmdescricaoverba

        try:

            while var_loop:

                elemento_verba_principal = WebDriverWait(driver, 2).until(EC.visibility_of_element_located((By.ID, f'formulario:listagem:0:listaReflexo:{indice}:j_id582')))

                # print("- # WEB: ", elemento_verba_principal.get_attribute("textContent"))
                # print("- # VAR: ", verba_principal)

                if verba_principal == elemento_verba_principal.get_attribute("textContent"):
                    elementoCheckbox = WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, f'formulario:listagem:0:listaReflexo:{indice}:ativo')))
                    situacaoCheckbox = elementoCheckbox.is_selected()

                    if valor == 'S':
                        if not situacaoCheckbox:
                            elementoCheckbox.click()
                            var_loop = False
                    elif valor == 'N':
                        if situacaoCheckbox:
                            elementoCheckbox.click()
                            var_loop = False

                indice += 1

        except TimeoutException:
            pass

        del valor

    # SFLREFLEXOREPOUSO
    def marcar_sflreflexorepouso(self, driver, valor, snmdescricaoverba):

        indice = 0
        var_loop = True

        # formulario:listagem:0:divDestinacoes
        verba_principal = 'REPOUSO SEMANAL REMUNERADO E FERIADO SOBRE ' + snmdescricaoverba

        try:

            while var_loop:

                elemento_verba_principal = WebDriverWait(driver, 2).until(EC.visibility_of_element_located((By.ID, f'formulario:listagem:0:listaReflexo:{indice}:j_id582')))

                # print("- # WEB: ", elemento_verba_principal.get_attribute("textContent"))
                # print("- # VAR: ", verba_principal)

                if verba_principal == elemento_verba_principal.get_attribute("textContent"):
                    elementoCheckbox = WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, f'formulario:listagem:0:listaReflexo:{indice}:ativo')))
                    situacaoCheckbox = elementoCheckbox.is_selected()

                    if valor == 'S':
                        if not situacaoCheckbox:
                            elementoCheckbox.click()
                            var_loop = False
                    elif valor == 'N':
                        if situacaoCheckbox:
                            elementoCheckbox.click()
                            var_loop = False

                indice += 1

        except TimeoutException:
            pass

        del valor

    # SFLREFLEXOART477CLT
    def marcar_sflreflexoart477clt(self, driver, valor, snmdescricaoverba):

        indice = 0
        var_loop = True

        # formulario:listagem:0:divDestinacoes
        verba_principal = 'MULTA DO ARTIGO 477 DA CLT SOBRE ' + snmdescricaoverba

        try:

            while var_loop:

                elemento_verba_principal = WebDriverWait(driver, 2).until(EC.visibility_of_element_located((By.ID, f'formulario:listagem:0:listaReflexo:{indice}:j_id582')))

                # print("- # WEB: ", elemento_verba_principal.get_attribute("textContent"))
                # print("- # VAR: ", verba_principal)

                if verba_principal == elemento_verba_principal.get_attribute("textContent"):
                    elementoCheckbox = WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, f'formulario:listagem:0:listaReflexo:{indice}:ativo')))
                    situacaoCheckbox = elementoCheckbox.is_selected()

                    if valor == 'S':
                        if not situacaoCheckbox:
                            elementoCheckbox.click()
                            var_loop = False
                    elif valor == 'N':
                        if situacaoCheckbox:
                            elementoCheckbox.click()
                            var_loop = False

                indice += 1

        except TimeoutException:
            pass

        del valor

    # --- OUTRAS FUNCIONALIDADES
    # VERBA REFLEXA
    def expandir_verba_reflexa(self, driver, valor):

        s_loop = True
        indice = 0

        while s_loop:

            try:

                if WebDriverWait(driver, 1).until(EC.visibility_of_element_located((By.ID, f'formulario:listagem:{indice}:j_id569'))):

                    elemento_verba_principal = WebDriverWait(driver, 1).until(EC.presence_of_element_located((By.ID, f'formulario:listagem:{indice}:j_id569')))
                    # print("- ELEMENTO: ", elemento_verba_principal.text)
                    # print("- PARÂMETRO: ", valor)
                    if elemento_verba_principal.text == valor:
                        WebDriverWait(driver, 1).until(EC.element_to_be_clickable((By.ID, f'formulario:listagem:{indice}:divDestinacoes'))).click()
                        s_loop = False

            except TimeoutException:
                # print("- ELEMENTO NÃO ENCONTRADO!")
                break

            indice += 1

    # SALVAR
    def selecionar_btnSalvarOperacao(self, driver):
        WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, 'formulario:salvar'))).click()





    def definirValorPagoBase(self, driver, valor):

        control = True

        while control:

            try:
                if WebDriverWait(driver, self.delay).until(EC.visibility_of_element_located((By.ID, 'formulario:baseTabelada'))):

                    campoBase = WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.NAME, 'formulario:baseTabelada')))
                    selecaoBase = Select(campoBase)
                    selecaoBase.select_by_visible_text(valor)

                    control = False
            except TimeoutException:
                print('- Campo não encontrado! Repetindo a operação...')
                continue

        del valor

    def definirValorPagoHistorico(self, driver, valor):

        #
        campoHistorico = WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.NAME, 'formulario:baseHistoricosValorPago')))
        selecaoHistorico = Select(campoHistorico)
        selecaoHistorico.select_by_visible_text(valor)

        del valor

    def definirValorPagoProporcionalizar(self, driver, valor):

        positivo = 'Sim'
        negativo = 'Não'

        campoProporcionalizar = WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.NAME, 'formulario:proporcionalizaHistoricoDoValorPago')))
        selecaoProporcionalizar = Select(campoProporcionalizar)

        if valor == positivo:
            selecaoProporcionalizar.select_by_visible_text(negativo)
            selecaoProporcionalizar.select_by_visible_text(valor)
        else:
            selecaoProporcionalizar.select_by_visible_text(positivo)
            selecaoProporcionalizar.select_by_visible_text(valor)


        del valor

    def definirValorPagoAdicionar(self, driver):
        WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, 'formulario:incluirBaseHistoricoValorPago'))).click()



    def functionMain(self):

        delayG = 2.5

        objetoweb = WebDriver()
        objetoTime = Control()
        objetoVerba = Verbas()

        #  -- PJECALC PAGINA INICIAL -- #
        driver = objetoweb.driver_web()
        driver.get("http://localhost:9257/pjecalc/pages/principal.jsf?conversationId=11")
        sleep(5)

        objetoVerba.importarCalculo(driver)
        sleep(delayG)
        objetoVerba.esolherArquivo(driver)
        sleep(delayG)
        objetoVerba.confirmarOperacao(driver)
        objetoTime.aguardar_processamento()
        sleep(delayG)

        #  -- PJECALC - VERBAS -- #
        objetoVerba.acessarVerbas(driver)
        objetoTime.aguardar_processamento()
        sleep(delayG)

        # objetoVerba.acessarExpresso(driver)
        # objetoTime.aguardar_processamento()
        # sleep(delayG)

        # -- VERBAS TBVERBABD
        for vl in self.planilha_base['IIDVERBAJRS']:

            if vl > 0:

                # IIDVERBAJRS
                iidverbajrs = int(vl)
                snmdescricaoverba = ""
                sflreflexo13terceiro = ""
                sflreflexoferias = ""
                sflreflexoaviso = ""
                sflreflexorepouso = ""
                sflreflexoart477clt = ""

                objetoVerba.acessarExpresso(driver)
                objetoTime.aguardar_processamento()
                sleep(delayG)

                for vc in self.planilha_base.columns:

                    dado = self.planilha_base.loc[iidverbajrs - 1, vc]

                    if vc == 'SNMDESCRICAOVERBA':
                        snmdescricaoverba = dado
                        print("- SNMDESCRICAOVERBA: ", dado)

                    if vc == 'SNMVERBAEXPRESSOPJECALC':
                        print("- SNMVERBAEXPRESSOPJECALC: ", dado)
                        objetoVerba.selecionarVerbaPrincipal(driver, dado)
                        objetoVerba.salvarOperacao(driver)
                        objetoTime.aguardar_processamento()
                        sleep(delayG)
                        objetoVerba.acessarParametrosVerba(driver)
                        objetoTime.aguardar_processamento()
                        sleep(delayG)

                    if vc == 'SNMDESCRICAOVERBA':
                        print("- SNMDESCRICAOVERBA: ", dado)
                        objetoVerba.modificar_snmdescricaoverba(driver, dado)

                    if vc == 'STPPARCELA':
                        print("- STPPARCELA: ", dado)
                        objetoVerba.marcar_stpparcela(driver, dado)

                    if vc == 'STPVALOR':
                        print("- STPVALOR: ", dado)
                        objetoVerba.marcar_stpvalor(driver, dado)

                    if vc == 'SFLINCIDENCIAINSS':
                        print("- SFLINCIDENCIAINSS: ", dado)
                        objetoVerba.marcar_sflincidenciainss(driver, dado)

                    if vc == 'SFLINCIDENCIAIRPF':
                        print("- SFLINCIDENCIAIRPF: ", dado)
                        objetoVerba.marcar_sflincidenciairpf(driver, dado)

                    if vc == 'SFLINCIDENCIAFGTS':
                        print("- SFLINCIDENCIAFGTS: ", dado)
                        objetoVerba.marcar_sflincidenciafgts(driver, dado)

                    if vc == 'SFLINCIDENCIAPREVPRIVADA':
                        print("- SFLINCIDENCIAPREVPRIVADA: ", dado)
                        objetoVerba.marcar_sflincidenciaprevprivada(driver, dado)

                    if vc == 'SFLINCIDENCIAPENSAO':
                        print("- SFLINCIDENCIAPENSAO: ", dado)
                        objetoVerba.marcar_sflincidenciapensao(driver, dado)

                    if vc == 'STPCARACTERISTICAVERBA':
                       print("- STPCARACTERISTICAVERBA: ", dado)
                       objetoVerba.marcar_stpcaracteristicaverba(driver, dado)

                    if vc == 'STPOCORRENCIAPAGAMENTO':
                        print("- STPOCORRENCIAPAGAMENTO: ", dado)
                        objetoVerba.marcar_stpocorrenciapagamento(driver, dado)

                    if vc == 'STPJUROSSUMULA':
                        print("- STPJUROSSUMULA: ", dado)
                        objetoVerba.marcar_stpjurossumula(driver, dado)

                    if vc == 'STPTIPOVERBA':
                        print("- STPTIPOVERBA: ", dado)
                        objetoVerba.marcar_stptipoverba(driver, dado)

                    if vc == 'STPGERARVERBAREFLEXA':
                        print("- STPGERARVERBAREFLEXA: ", dado)
                        objetoVerba.marcar_stpgerarverbareflexa(driver, dado)

                    if vc == 'STPGERARVERBAPRINCIPAL':
                        print("- STPGERARVERBAPRINCIPAL: ", dado)
                        objetoVerba.marcar_stpgerarverbaprincipal(driver, dado)

                    if vc == 'SFLCOMPORPRINCIPAL':
                        print("- SFLCOMPORPRINCIPAL: ", dado)
                        objetoVerba.marcar_sflcomporprincipal(driver, dado)

                    if vc == 'SFLPADRAOZERARVALORNEGATIVO':
                        print("- SFLPADRAOZERARVALORNEGATIVO: ", dado)
                        objetoVerba.marcar_sflpadraozerarvalornegativo(driver, dado)

                    if vc == 'DDTINICIO':
                        print("- DDTINICIO: ", dado)
                        objetoVerba.modificar_ddtinicio(driver, dado)

                    if vc == 'DDTTERMINO':
                        print("- DDTTERMINO: ", dado)
                        objetoVerba.modificar_ddttermino(driver, dado)

                    if vc == 'SFLEXCLUIRFALTAJUSTIFICADA':
                        print("- SFLEXCLUIRFALTAJUSTIFICADA: ", dado)
                        objetoVerba.marcar_sflexcluirfaltajustificada(driver, dado)

                    if vc == 'SFLEXCLUIRFALTANAOJUSTIFICADA':
                        print("- SFLEXCLUIRFALTANAOJUSTIFICADA: ", dado)
                        objetoVerba.marcar_sflexcluirfaltanaojustificada(driver, dado)

                    if vc == 'SFLEXCLUIRFERIASGOZADAS':
                        print("- SFLEXCLUIRFERIASGOZADAS: ", dado)
                        objetoVerba.marcar_sflexcluirferiasgozadas(driver, dado)

                    if vc == 'SFLDOBRARVALOR':
                        print("- SFLDOBRARVALOR: ", dado)
                        objetoVerba.marcar_sfldobrarvalor(driver, dado)

                    if vc == 'RVLVALORDEVIDO':
                        print("- RVLVALORDEVIDO: ", dado)
                        objetoVerba.modificar_rvlvalordevido(driver, dado)

                    if vc == 'SFLPROPORCIONALIDADE':
                        print("- SFLPROPORCIONALIDADE: ", dado)
                        objetoVerba.marcar_sflproporcionalidade(driver, dado)

                    if vc == 'STPBASEDEVIDO':
                        print("- STPBASEDEVIDO: ", dado)
                        objetoVerba.modificar_stpbasedevido(driver, dado)

                    if vc == 'STPDIVISOR':
                        print("- STPDIVISOR: ", dado)
                        objetoVerba.modificar_stpdivisor(driver, dado)

                    if vc == 'RVLOUTRODIVISOR':
                        print("- RVLOUTRODIVISOR: ", dado)
                        objetoVerba.modificar_rvloutrodivisor(driver, dado)

                    if vc == 'RVLMULTIPLICADOR':
                        print("- RVLMULTIPLICADOR: ", dado)
                        objetoVerba.modificar_rvlmultiplicador(driver, dado)

                    if vc == 'STPQUANTIDADE':
                        print("- STPQUANTIDADE: ", dado)
                        objetoVerba.marcar_stpquantidade(driver, dado)

                    if vc == 'STPCALENDARIO':
                        print("- STPCALENDARIO: ", dado)
                        objetoVerba.modificar_stpcalendario(driver, dado)

                    if vc == 'RVLOUTROVALORQTD':
                        print("- RVLOUTROVALORQTD: ", dado)
                        objetoVerba.modificar_rvloutrovalorqtd(driver, dado)

                    if vc == 'SFLQTDPROPORCIONALIDADE':
                        print("- SFLQTDPROPORCIONALIDADE: ", dado)
                        objetoVerba.marcar_sflqtdproporcionalidade(driver, dado)

                    if vc == 'STPVALORPAGO':
                        print("- STPVALORPAGO: ", dado)
                        objetoVerba.marcar_stpvalorpago(driver, dado)

                    if vc == 'STPBASEPAGO':
                        print("- STPBASEPAGO: ", dado)
                        objetoVerba.modificar_stpbasepago(driver, dado)

                    if vc == 'RVLINOUTROVALOR':
                        print("- RVLINOUTROVALOR: ", dado)
                        objetoVerba.modificar_rvlinoutrovalor(driver, dado)

                    if vc == 'SFLVPGPROPORCIONALIDADE':
                        print("- SFLVPGPROPORCIONALIDADE: ", dado)
                        objetoVerba.marcar_sflvpgproporcionalidade(driver, dado)

                    if vc == 'RVLQUANTIDADE':
                        print("- RVLQUANTIDADE: ", dado)
                        objetoVerba.modificar_rvlquantidade(driver, dado)

                    if vc == 'SDSCOMENTARIO':
                        print("- SDSCOMENTARIO: ", dado)
                        objetoVerba.modificar_sdscomentario(driver, dado)

                    if vc == 'SFLREFLEXO13TERCEIRO':
                        sflreflexo13terceiro = dado
                        print("- SFLREFLEXO13TERCEIRO: ", dado)

                    if vc == 'SFLREFLEXOAVISO':
                        sflreflexoaviso = dado
                        print("- SFLREFLEXOAVISO: ", dado)

                    if vc == 'SFLREFLEXOFERIAS':
                        sflreflexoferias = dado
                        print("- SFLREFLEXOFERIAS: ", dado)

                    if vc == 'SFLREFLEXOART477CLT':
                        sflreflexoart477clt = dado
                        print("- SFLREFLEXOART477CLT: ", dado)

                    if vc == 'SFLREFLEXOREPOUSO':
                        sflreflexorepouso = dado
                        print("- SFLREFLEXOREPOUSO: ", dado)


                # SALVAR
                objetoVerba.selecionar_btnSalvarOperacao(driver)
                objetoTime.aguardar_processamento()
                sleep(delayG)

                # EXPANDIR O CONTEUDO DA VERBA REFLEXA
                objetoVerba.expandir_verba_reflexa(driver, snmdescricaoverba)
                objetoTime.aguardar_processamento()
                sleep(delayG)

                # SFLREFLEXO13TERCEIRO
                objetoVerba.marcar_sflreflexo13terceiro(driver, sflreflexo13terceiro, snmdescricaoverba)
                objetoTime.aguardar_processamento()
                sleep(0.5)

                # SFLREFLEXOAVISO
                objetoVerba.marcar_sflreflexoaviso(driver, sflreflexoaviso, snmdescricaoverba)
                objetoTime.aguardar_processamento()
                sleep(0.5)

                # SFLREFLEXOFERIAS
                objetoVerba.marcar_sflreflexoferias(driver, sflreflexoferias, snmdescricaoverba)
                objetoTime.aguardar_processamento()
                sleep(0.5)

                # SFLREFLEXOART477CLT
                objetoVerba.marcar_sflreflexoart477clt(driver, sflreflexoart477clt, snmdescricaoverba)
                objetoTime.aguardar_processamento()
                sleep(0.5)

                # SFLREFLEXOREPOUSO
                objetoVerba.marcar_sflreflexorepouso(driver, sflreflexorepouso, snmdescricaoverba)
                objetoTime.aguardar_processamento()
                sleep(0.5)

                # LIMPAR VARIÁVEL
                del dado
                del snmdescricaoverba

                break
                # print("")
            else:
                continue


if __name__ == '__main__':

    # OBJETO VERBA
    objetoVerba = Verbas()

    # FUNÇÃO PRINCIPAL
    objetoVerba.functionMain()
