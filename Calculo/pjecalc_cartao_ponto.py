import os
import shutil
import time
from datetime import datetime

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.wait import WebDriverWait

from Calculo.leitura_planilha import ler_pje_bd, valor_vazio
from Tools.pendencias import interromper, registrar
from Tools.pjecalc_control import Control


class CartaoPonto:
    """Tela Cartão de Ponto a partir de arquivos.cartao-de-ponto do .json (chaves cartao_ponto_* da PJE-BD).

    Critérios de Apuração com o padrão do PJe-Calc no período das batidas → Grade de Ocorrências › Importar Jornada
    (o .csv no layout do ExemploJornadaCartaoDePonto.csv) → Visualizar Cartão › Apurar. As verbas com divisor ou
    quantidade "Importada do Cartão de Ponto" leem as colunas dessa apuração (Dias Trabalhados, Hs EXT, Hs Trabalhadas).
    Sem o arquivo, a tela não é aberta. Qualquer recusa do PJe-Calc interrompe: as verbas do cartão sairiam zeradas.
    """

    TELA = "Cartão de Ponto"

    def __init__(self, source):
        self.planilha_base = ler_pje_bd(source)
        self.delay = 10
        self.delayG = 1.5
        self.objTools = Control()

    def _pedido(self):
        return {str(k).strip(): v for k, v in zip(self.planilha_base['IDENTIFICADOR'], self.planilha_base['INFORMACAO'])
                if isinstance(k, str) and str(k).strip().startswith('cartao_ponto_') and not valor_vazio(v)}

    def _clicar(self, driver, por, valor):
        WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((por, valor))).click()
        self.objTools.aguardar_carregamento(driver)
        time.sleep(self.delayG)

    def _mensagens(self, driver):
        return driver.execute_script(r"""return [...document.querySelectorAll('[id*=painelMensagens]')]
            .map(m => m.textContent.split('//<!')[0].replace(/jQuery\(function[\s\S]*?\}\);/g, '').replace(/window\.location[^;]*;/g, '')
            .trim().replace(/\s+/g, ' ')).filter(t => t).join(' | ');""")

    def _conferir(self, driver, etapa):
        texto = self._mensagens(driver)
        if 'Operação realizada com sucesso' in texto and 'Erro.' not in texto:
            print(f"- [{self.TELA}] {etapa}: [OK]")
            return True
        interromper(self.TELA, f"{etapa}: {texto or 'o PJe-Calc não confirmou a operação'}")
        return False

    def _data(self, driver, campo, valor):
        caixa = WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, f"formulario:{campo}")))
        caixa.click()
        caixa.send_keys(Keys.CONTROL, "a")
        caixa.send_keys(Keys.DELETE)
        caixa.send_keys(valor)
        caixa.send_keys(Keys.TAB)
        self.objTools.aguardar_carregamento(driver)
        time.sleep(0.5)

    def _periodo(self, driver, inicio, fim):
        """Período das batidas, dentro do que a tela propõe (admissão a demissão do cálculo)."""
        lido = lambda campo: driver.find_element(By.ID, f"formulario:{campo}").get_attribute("value")
        como_data = lambda texto: datetime.strptime(texto, "%d/%m/%Y")
        padrao_inicio, padrao_fim = lido("competenciaInicialInputDate"), lido("competenciaFinalInputDate")
        try:
            if padrao_inicio and como_data(padrao_inicio) > como_data(inicio):
                registrar(self.TELA, f"batidas antes de {padrao_inicio} (admissão) ficam fora da apuração", origem="automacao")
                inicio = padrao_inicio
            if padrao_fim and como_data(padrao_fim) < como_data(fim):
                registrar(self.TELA, f"batidas depois de {padrao_fim} (demissão) ficam fora da apuração", origem="automacao")
                fim = padrao_fim
        except ValueError:
            pass
        self._data(driver, "competenciaInicialInputDate", inicio)
        self._data(driver, "competenciaFinalInputDate", fim)
        return inicio, fim

    def main_cartao_ponto(self, driver):
        print('\n# ========== [CARTAO_DE_PONTO] ========== #\n')
        pedido = self._pedido()
        arquivo = pedido.get("cartao_ponto_arquivo")
        if not arquivo:
            print(f"- [{self.TELA}]: o pedido não traz cartão de ponto; tela não preenchida")
            return
        inicio, fim = str(pedido.get("cartao_ponto_inicio")), str(pedido.get("cartao_ponto_fim"))

        # Critérios de Apuração: o padrão do PJe-Calc, no período das batidas
        self._clicar(driver, By.CLASS_NAME, "menuImageCartaoPonto")
        self._clicar(driver, By.ID, "formulario:incluir")
        inicio, fim = self._periodo(driver, inicio, fim)
        self._clicar(driver, By.ID, "formulario:salvar")
        if not self._conferir(driver, f"critérios de apuração ({inicio} a {fim})"):
            return

        # Grade de Ocorrências › Importar Jornada
        self._clicar(driver, By.ID, "formulario:visualizarOcorrencias")
        self._clicar(driver, By.ID, "formulario:tabImportar_lbl")
        local = os.path.join(os.getcwd(), "cartao_de_ponto_importar.csv")
        shutil.copyfile(arquivo, local)  # o upload do navegador não depende de caminho de rede
        try:
            driver.find_element(By.ID, "formulario:arquivo:file").send_keys(local)
            time.sleep(3)
            self.objTools.aguardar_carregamento(driver)
            self._clicar(driver, By.ID, "formulario:confirmarImportacao")
        finally:
            if os.path.exists(local):
                os.remove(local)
        if not self._conferir(driver, "importação das batidas"):
            return

        # Visualizar Cartão › Apurar: gera as colunas mensais que as verbas importam
        self._clicar(driver, By.CLASS_NAME, "menuImageCartaoPonto")
        self._clicar(driver, By.ID, "formulario:importarCartao")
        self._clicar(driver, By.ID, "formulario:montarApartirDaApuracao")
        if not self._conferir(driver, "apuração"):
            return
        print('-- Fim - (Cartão de Ponto) --')


def selecionar_coluna_do_cartao(driver, campo, valor, tela="Verbas"):
    """Verba com divisor/quantidade "Importada do Cartão de Ponto": inclui as colunas da apuração (texto do seletor,
    várias separadas por '|', que o PJe-Calc soma). campo: 'Divisor' ou 'Quantidade'. Escolher no seletor não basta: a
    coluna só vale depois do "+" (incluirCartaoDePonto…), que a põe na lista. Coluna que não existe: interrompe."""
    controle = Control()
    procuradas = [" ".join(c.split()) for c in str(valor).split("|") if c.strip()]
    for procurada in procuradas:
        try:
            caixa = WebDriverWait(driver, 5).until(
                EC.visibility_of_element_located((By.ID, f"formulario:tipoImportadadoDoCartaoDePonto{campo}")))
        except Exception:
            interromper(tela, f"{campo.lower()} importada do cartão: o seletor de colunas não apareceu")
            return
        seletor = Select(caixa)
        opcoes = [o.text.strip() for o in seletor.options if o.text.strip()]
        achada = next((o for o in opcoes if o.upper() == procurada.upper()), None)
        if achada is None:
            interromper(tela, f"{campo.lower()} importada do cartão: coluna {procurada!r} não existe na apuração "
                              f"(há: {', '.join(opcoes) or 'nenhuma — o cartão não foi apurado'})")
            return
        seletor.select_by_visible_text(achada)
        controle.aguardar_carregamento(driver)
        time.sleep(0.5)
        WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.ID, f"formulario:incluirCartaoDePonto{campo}"))).click()
        controle.aguardar_carregamento(driver)
        time.sleep(1)
    incluidas = driver.execute_script(
        "const t = document.getElementById(arguments[0]); return t ? [...t.querySelectorAll('tbody tr')].map(r => r.textContent.trim()) : [];",
        f"formulario:listagemCartaoDePonto{campo}")
    faltam = [c for c in procuradas if not any(c.upper() in linha.upper() for linha in incluidas)]
    if faltam:
        interromper(tela, f"{campo.lower()} importada do cartão: o PJe-Calc não incluiu {', '.join(faltam)}")
        return
    print(f"- [{tela}] {campo.lower()} importada do cartão: {' + '.join(procuradas)}")
