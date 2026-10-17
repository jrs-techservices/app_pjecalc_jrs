from Tools.pendencias import de_relatorio, registrar
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait, TimeoutException
from selenium.webdriver.support import expected_conditions as EC
import time
import os
import gc
from Calculo.pjecalc_dados_calculo import DadosCalculo
from Tools.pjecalc_control import Control
from Calculo.leitura_planilha import valor_vazio, booleano_da_planilha


class FGTS(DadosCalculo):


    def __init__(self, source):
        super().__init__(source)
        self.delay = 10
        self.delayG = 1.5
        self.objTools = Control()


    destino_fgts = ''
    compor_principal = ''
    multa_fgts = ''

    def verificacao(self, driver):

        def gerar_relatorio(campo, status):
            file_txt_log = open(os.getcwd() + '\log.txt', "a")
            file_txt_log.write('- ' + campo + ' | ' + status + '\n')
            return file_txt_log.close()

        delay = 10
        try:
            mensagem = WebDriverWait(driver, delay).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "table[id^='formulario:painelMensagens:']")))
            msg = mensagem.text
            if 'Operação realizada com sucesso.' in msg:
                # print('* Operação realizada com sucesso.')
                gerar_relatorio('FGTS', 'Ok')
            else:
                # print('* ERRO!', msg)
                gerar_relatorio('FGTS', '---------- Erro! ----------')
                de_relatorio('FGTS')
        except TimeoutException:
            print('- [Except][FGTS] - Elemento não encontrado/A Página demorou para responder. Encerrando...')

        # Tempo de controle
        time.sleep(2)

    def acessar_fgts(self, driver):
        WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.CLASS_NAME, "menuImageFgts"))).click()
        # WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, 'formulario:j_id46:0:j_id49:14:j_id1141')))

    def selecionar_destino(self, driver):


        for i in range(len(self.planilha_base)):

            coluna_identificador = self.planilha_base.loc[i, 'IDENTIFICADOR']
            coluna_informacao = self.planilha_base.loc[i, 'INFORMACAO']

            # Condição para pular as linhas em branco da coluna Identificador na planilha base
            if type(coluna_identificador) == type(self.var_controle_float):
                # print('* Pulando linhas em branco ...')
                continue
            # Dados de FGTS
            elif coluna_identificador == 'destino_fgts':
                self.destino_fgts = coluna_informacao
                print('- Destino FGTS: ', self.destino_fgts)
                # Após encontrar o conteúdo, interromper o loop.
                break

        if valor_vazio(self.destino_fgts):
            print('- Destino FGTS: sem valor na planilha; mantido o padrão do PJe-Calc')
        elif str(self.destino_fgts).strip().lower() == 'pagar':
            opcao_pagar = WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, 'formulario:tipoDeVerba:0')))
            checkbox_pagar = opcao_pagar.is_selected()
            print('- Status - Opção Pagar: ', checkbox_pagar)
            if checkbox_pagar:
                print('- OptionButton - Destino "Pagar" - Já Habilitado.')
            else:
                print('- OptionButton - Destino "Pagar" - Foi Habilitado.')
                opcao_pagar.click()
        else:
            opcao_recolher = WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, 'formulario:tipoDeVerba:1')))
            checkbox_recolher = opcao_recolher.is_selected()
            print('- Status - Opção Recolher: ', checkbox_recolher)
            if checkbox_recolher:
                print('- OptionButton - Destino "Recolher" - Já Habilitado.')
            else:
                print('- OptionButton - Destino "Recolher" - Foi Habilitado.')
                opcao_recolher.click()

    def selecionar_compor_principal(self, driver):


        for i in range(len(self.planilha_base)):

            coluna_identificador = self.planilha_base.loc[i, 'IDENTIFICADOR']
            coluna_informacao = self.planilha_base.loc[i, 'INFORMACAO']

            # Condição para pular as linhas em branco da coluna Identificador na planilha base
            if type(coluna_identificador) == type(self.var_controle_float) and type(coluna_informacao) == type(self.var_controle_float):
                # print('* Pulando linhas em branco ...')
                continue
            elif coluna_identificador == 'compor_principal':
                self.compor_principal = coluna_informacao
                print('- Compor Principal: ', self.compor_principal)
                # Após encontrar o elemento e atribuir o valor, encerrar o loop
                break


        compor = booleano_da_planilha(self.compor_principal)
        if compor is True:
            opcao_sim = WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, 'formulario:comporPrincipal:0')))
            checkbox_sim = opcao_sim.is_selected()
            print('- Status - Compor Principal: ', checkbox_sim)
            if checkbox_sim:
                print('- OptionButton - Compor Princial "Sim" - Já Habilitado.')
            else:
                print('- OptionButton - Compor Princial "Sim" - Foi Habilitado.')
                opcao_sim.click()

        elif compor is False:
            opcao_nao = WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, 'formulario:comporPrincipal:1')))
            checkbox_nao = opcao_nao.is_selected()
            print('- Status - Compor Principal: ', checkbox_nao)
            if checkbox_nao:
                print('- OptionButton - Compor Princial "Não" - Já Habilitado.')
            else:
                opcao_nao.click()

    def _pedido(self):
        """Chaves fgts_* do .json (vazio se a planilha não as tem: aí vale o fluxo de sempre)."""
        return {str(k).strip(): v for k, v in zip(self.planilha_base['IDENTIFICADOR'], self.planilha_base['INFORMACAO'])
                if isinstance(k, str) and str(k).strip().startswith('fgts_') and not valor_vazio(v)}

    def _marcar(self, driver, id_campo, marcar, rotulo):
        caixa = WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.ID, id_campo)))
        if not caixa.is_enabled():
            # desabilitada já no estado pedido (ex.: Deduzir false com o quadro vazio) não é pendência
            if caixa.is_selected() != marcar:
                registrar("FGTS", f"'{rotulo}' desabilitado na tela; não aplicado", origem="automacao")
            return
        if caixa.is_selected() != marcar:
            caixa.click()
            self.objTools.aguardar_carregamento(driver)
            time.sleep(1)
        print(f"- [FGTS] {rotulo}: {'marcado' if marcar else 'desmarcado'}")

    def aplicar_parametros_do_pedido(self, driver):
        """Campos de telas.fgts do .json, na ordem da tela: tipo do valor (troca os campos) → percentual/incidência ou valor
        → excluir aviso e 467 → LC 110. A multa já foi marcada em checkbox_multa."""
        pedido = self._pedido()
        if not pedido:
            return
        tipo = pedido.get('fgts_tipo_valor_multa')
        if tipo:
            WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable(
                (By.ID, f"formulario:tipoDoValorDaMulta:{0 if tipo == 'Calculado' else 1}"))).click()
            self.objTools.aguardar_carregamento(driver)
            time.sleep(2)
            print(f"- [FGTS] tipo do valor da multa: {tipo}")
        if pedido.get('fgts_percentual_multa'):
            indice = 0 if pedido['fgts_percentual_multa'] == '20%' else 1
            WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, f"formulario:multaDoFgts:{indice}"))).click()
            time.sleep(1)
            print(f"- [FGTS] percentual da multa: {pedido['fgts_percentual_multa']}")
        if pedido.get('fgts_incidencia_multa'):
            Select(WebDriverWait(driver, self.delay).until(EC.presence_of_element_located(
                (By.ID, 'formulario:incidenciaDoFgts')))).select_by_value(pedido['fgts_incidencia_multa'])
            time.sleep(1)
            print(f"- [FGTS] incidência da multa: {pedido['fgts_incidencia_multa']}")
        if pedido.get('fgts_valor_multa_informado') is not None and tipo == 'Informado':
            campo = WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.ID, 'formulario:valorInformadoDaMulta')))
            campo.click()
            campo.send_keys(Keys.CONTROL, "a")
            campo.send_keys(Keys.DELETE)
            campo.send_keys(f"{float(pedido['fgts_valor_multa_informado']):.2f}".replace(".", ","))
            campo.send_keys(Keys.TAB)
            print(f"- [FGTS] valor informado da multa: {pedido['fgts_valor_multa_informado']}")
        for chave, id_campo, rotulo in (("fgts_excluir_aviso_multa", "formulario:excluirAvisoDaMulta", "Excluir aviso da base da multa"),
                                        ("fgts_multa_467", "formulario:multaDoArtigo467", "Multa do artigo 467"),
                                        ("fgts_multa_lc110", "formulario:multa10", "Contribuição Social 10% (LC 110)"),
                                        ("fgts_contribuicao_lc110", "formulario:contribuiçãoSocial", "Contribuição Social 0,5% (LC 110)")):
            valor = booleano_da_planilha(pedido.get(chave)) if pedido.get(chave) != "PADRAO" else None
            if valor is not None:
                self._marcar(driver, id_campo, valor, rotulo)
        # pensão alimentícia: a caixa "sobre a multa" só aparece depois da multa e da pensão sobre o FGTS
        for chave, id_campo, rotulo in (("fgts_pensao_alimenticia", "formulario:incidenciaPensaoAlimenticia", "Pensão alimentícia sobre FGTS"),
                                        ("fgts_pensao_alimenticia_multa", "formulario:incidenciaPensaoAlimenticiaSobreMulta", "Pensão alimentícia sobre a multa")):
            valor = booleano_da_planilha(pedido.get(chave))
            if valor is not None:
                self._marcar(driver, id_campo, valor, rotulo)
        self.lancar_saldo_e_saque_do_pedido(driver, pedido)

    def lancar_saldo_e_saque_do_pedido(self, driver, pedido):
        """Quadro "Saldo e/ou Saque" (data DD/MM/AAAA + valor + Adicionar) e, depois das linhas, "Deduzir do FGTS" — a caixa
        fica desabilitada enquanto o quadro está vazio e vale para o quadro inteiro (o PJe-Calc grava as linhas como DEPOSITO)."""
        import json
        linhas = json.loads(pedido['fgts_saldo_saque']) if pedido.get('fgts_saldo_saque') else []
        for data, valor in linhas:
            for id_campo, texto in (('formulario:competenciaInputDate', data), ('formulario:valor', f"{float(valor):.2f}".replace(".", ","))):
                campo = WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, id_campo)))
                campo.click()
                campo.send_keys(Keys.CONTROL, "a")
                campo.send_keys(Keys.DELETE)
                campo.send_keys(texto)
                campo.send_keys(Keys.TAB)
                time.sleep(0.5)
            WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, 'formulario:cmdIncluir'))).click()
            self.objTools.aguardar_carregamento(driver)
            time.sleep(1)
            erros = driver.execute_script("""return [...document.querySelectorAll('.linkErro, .rich-messages-label, .rich-message-label')]
                .filter(e => e.offsetWidth || e.offsetHeight).map(e => e.textContent.split('//<!')[0].trim()).filter(t => t && !/sucesso/i.test(t));""")
            if erros:
                registrar("FGTS", f"saldo/saque de {data} (R$ {valor}) não incluído: {' | '.join(erros)}")
            else:
                print(f"- [FGTS] saldo/saque: {data} R$ {valor}")
        deduzir = booleano_da_planilha(pedido.get('fgts_deduzir'))
        if deduzir is not None:
            self._marcar(driver, "formulario:deduzirDoFGTS", deduzir, "Deduzir do FGTS")

    def aplicar_aliquota_do_pedido(self, driver):
        """A alíquota é por ocorrência: 8% é o padrão; 2% vale o contrato todo, por Ocorrências › Regerar."""
        if self._pedido().get('fgts_aliquota') != '2%':
            return
        WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, 'formulario:ocorrencias'))).click()
        self.objTools.aguardar_carregamento(driver)
        time.sleep(2)
        WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, 'formulario:regerar'))).click()
        self.objTools.aguardar_carregamento(driver)
        time.sleep(2)
        WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, 'formulario:aliquota:0'))).click()
        time.sleep(1)
        WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, 'formulario:confirmarGeracao'))).click()
        self.objTools.aguardar_carregamento(driver)
        time.sleep(2)
        texto = driver.execute_script("return [...document.querySelectorAll('[id*=painelMensagens]')].map(m => m.textContent).join(' ');")
        if 'Operação realizada com sucesso' in texto:
            print("- [FGTS] alíquota 2% aplicada às ocorrências")
        else:
            registrar("FGTS", "alíquota 2% não confirmada nas ocorrências")

    def checkbox_multa(self, driver):

        # elementoCheckboxMulta = ""

        for i in range(len(self.planilha_base)):

            coluna_identificador = self.planilha_base.loc[i, 'IDENTIFICADOR']
            coluna_informacao = self.planilha_base.loc[i, 'INFORMACAO']
            # Condição para pular as linhas em branco da coluna Identificador na planilha base
            if type(coluna_identificador) == type(self.var_controle_float):
                # print('* Pulando linhas em branco ...')
                continue
            # Dados de FGTS
            elif coluna_identificador == 'multa_fgts':
                self.multa_fgts = coluna_informacao
                print('- Multa: ', self.multa_fgts)
                # Valor coletado, atribuído e loop encerrado.
                break

        multa = booleano_da_planilha(self.multa_fgts)
        if multa is None:
            print('- Multa FGTS: sem valor na planilha; mantido o padrão do PJe-Calc')
        elif multa:
            try:
                elementoCheckboxMulta = WebDriverWait(driver, 3).until(EC.element_to_be_clickable((By.ID, 'formulario:multa')))
                checkbox_multas = elementoCheckboxMulta.is_selected()
                print('- Status - Multa: ', checkbox_multas)
                if checkbox_multas:
                    print('- Checkbox - Multa - Já Habilitado.')
                    # --- Nova Funcionalidade ---#
                    # Nova Funcionalidade — Desmarcar a opção 'Excluir da Base da Multa o valor de FGTS sobre Aviso prévio'
                    checkbox_excluir_base = WebDriverWait(driver, 3).until(EC.element_to_be_clickable((By.ID, "formulario:excluirAvisoDaMulta")))
                    if checkbox_excluir_base.is_selected() and 'fgts_excluir_aviso_multa' not in self._pedido():
                        checkbox_excluir_base.click()
                        print("- Checkbox Desabilitado - 'Excluir da Base da Multa o valor de FGTS sobre Aviso prévio'")
                else:
                    elementoCheckboxMulta.click()
                    print('- Checkbox - Multa - Foi Habilitado.')
                    # --- Nova Funcionalidade ---#
                    # Nova Funcionalidade — Desmarcar a opção 'Excluir da Base da Multa o valor de FGTS sobre Aviso prévio'
                    checkbox_excluir_base = WebDriverWait(driver, 3).until(EC.element_to_be_clickable((By.ID, "formulario:excluirAvisoDaMulta")))
                    if checkbox_excluir_base.is_selected() and 'fgts_excluir_aviso_multa' not in self._pedido():
                        checkbox_excluir_base.click()
                        print("- Checkbox Desabilitado - 'Excluir da Base da Multa o valor de FGTS sobre Aviso prévio'")
            except TimeoutException:
                pass
        else:
            try:
                campo_checkbox = WebDriverWait(driver, 3).until(EC.element_to_be_clickable((By.ID, 'formulario:multa')))
                checkbox_multas = campo_checkbox.is_selected()
                print('- Status - Multa: ', checkbox_multas)
                if checkbox_multas:
                    print('- Checkbox - Multa - Foi Desabilitado.')
                    campo_checkbox.click()
            except TimeoutException:
                pass

    def salvar(self, driver):
        WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, 'formulario:salvar'))).click()

    def main_fgts(self, driver):

        self.acessar_fgts(driver)
        # Aguardar Processamento
        self.objTools.aguardar_carregamento(driver)
        # Tempo de Controle
        time.sleep(5)
        self.selecionar_destino(driver)
        # Tempo de Controle
        time.sleep(self.delayG)
        self.selecionar_compor_principal(driver)
        # Tempo de Controle
        time.sleep(self.delayG)
        self.checkbox_multa(driver)
        # Tempo de Controle
        time.sleep(self.delayG)
        self.aplicar_parametros_do_pedido(driver)
        self.salvar(driver)
        # Aguardar Processamento
        self.objTools.aguardar_carregamento(driver)
        # Tempo de Controle
        time.sleep(5)
        self.verificacao(driver)
        # Tempo de Controle
        time.sleep(self.delayG)
        self.aplicar_aliquota_do_pedido(driver)

        # - Limpar Temp
        self.objTools.limparFilesTemp()
        gc.collect(generation=0)
        gc.collect(generation=1)
        gc.collect(generation=2)

        print('-- Fim - (FGTS) --')