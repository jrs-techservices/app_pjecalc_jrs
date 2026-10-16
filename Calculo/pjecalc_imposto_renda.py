from Tools.pendencias import registrar
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait, TimeoutException
from selenium.webdriver.support import expected_conditions as EC
import time
#
from Tools.pjecalc_control import Control
from Calculo.leitura_planilha import ler_pje_bd, booleano_da_planilha, numero_da_planilha, valor_vazio


# chave da PJE-BD (vinda de telas.imposto-de-renda do .json) → caixa da tela
CAIXAS = {
    "ir_sobre_juros": "incidirSobreJurosDeMora",
    "ir_cobrar_reclamado": "cobrarDoReclamado",
    "ir_tributacao_exclusiva": "considerarTributacaoExclusiva",
    "ir_tributacao_em_separado": "considerarTributacaoEmSeparado",
    "ir_regime_caixa": "regimeDeCaixa",
    "ir_deduzir_cs_reclamante": "deduzirContribuicaoSocialDevidaPeloReclamante",
    "ir_deduzir_previdencia_privada": "deduzirPrevidenciaPrivada",
    "ir_deduzir_pensao_alimenticia": "deduzirPensaoAlimenticia",
    "ir_deduzir_honorarios_reclamante": "deduzirHonorariosDevidosPeloReclamante",
    "ir_aposentado_65": "aposentadoMaiorQue65Anos",
}


class ImpostoRenda:
    """Tela Imposto de Renda a partir das chaves ir_* do .json. Sem nenhuma delas, a tela fica no padrão do PJe-Calc
    (a planilha da casa nunca lançou esta tela)."""

    def __init__(self, source):
        self.source = source
        self.planilha_base = ler_pje_bd(source)
        self.delay = 10
        self.delayG = 1.5
        self.objTools = Control()

    def _pedido(self):
        return {str(k).strip(): v for k, v in zip(self.planilha_base['IDENTIFICADOR'], self.planilha_base['INFORMACAO'])
                if isinstance(k, str) and str(k).strip().startswith('ir_') and not valor_vazio(v)}

    def _marcar(self, driver, campo, marcar):
        caixa = WebDriverWait(driver, self.delay).until(EC.presence_of_element_located((By.ID, f"formulario:{campo}")))
        if not caixa.is_enabled():
            registrar("Imposto de Renda", f"'{campo}' desabilitado na tela; não aplicado", origem="automacao")
            return
        if caixa.is_selected() != marcar:
            caixa.click()
            self.objTools.aguardar_carregamento(driver)
            time.sleep(0.5)

    def _dependentes(self, driver, quantidade):
        self._marcar(driver, "possuiDependentes", quantidade > 0)
        if quantidade > 0:
            campo = WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, "formulario:quantidadeDependentes")))
            campo.click()
            campo.send_keys(Keys.CONTROL, "a")
            campo.send_keys(Keys.DELETE)
            campo.send_keys(str(quantidade))
            campo.send_keys(Keys.TAB)
            self.objTools.aguardar_carregamento(driver)

    def _verificar(self, driver):
        try:
            mensagem = WebDriverWait(driver, self.delay).until(
                EC.presence_of_element_located((By.ID, 'formulario:painelMensagens:j_id69'))).text
        except TimeoutException:
            registrar("Imposto de Renda", "o PJe-Calc não respondeu ao salvar")
            return
        if 'Operação realizada com sucesso.' in mensagem:
            print("- [Imposto de Renda]: salvo")
        else:
            erros = driver.execute_script("""return [...document.querySelectorAll('.linkErro, .rich-message-label, .rich-messages-label')]
                .map(e => e.textContent.split('//<!')[0].trim()).filter(t => t && !/sucesso/i.test(t));""")
            registrar("Imposto de Renda", " | ".join(erros) or mensagem)

    def main_imposto_renda(self, driver):
        pedido = self._pedido()
        if not pedido:
            print("- [Imposto de Renda]: o pedido não traz a tela; fica o padrão do PJe-Calc")
            return
        WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.CLASS_NAME, "menuImageIrpf"))).click()
        self.objTools.aguardar_carregamento(driver)
        time.sleep(self.delayG)
        apurar = booleano_da_planilha(pedido.get("ir_apurar"))
        if apurar is not None:
            self._marcar(driver, "apurarImpostoRenda", apurar)
        if apurar is not False:
            for chave, campo in CAIXAS.items():
                marcar = booleano_da_planilha(pedido.get(chave))
                if marcar is not None:
                    self._marcar(driver, campo, marcar)
            quantidade = numero_da_planilha(pedido.get("ir_dependentes"))
            if quantidade is not None:
                self._dependentes(driver, int(quantidade))
        print(f"- [Imposto de Renda]: {', '.join(f'{k}={v}' for k, v in sorted(pedido.items()))}")
        WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, 'formulario:salvar'))).click()
        self.objTools.aguardar_carregamento(driver)
        time.sleep(self.delayG)
        self._verificar(driver)
        print('-- Fim - (Imposto de Renda) --')
