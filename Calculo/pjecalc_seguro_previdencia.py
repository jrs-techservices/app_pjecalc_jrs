import json
import re
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.wait import WebDriverWait

from Calculo.leitura_planilha import ler_pje_bd, valor_vazio
from Tools.pendencias import interromper
from Tools.pjecalc_control import Control


class SeguroPrevidencia:
    """Telas Seguro-desemprego e Previdência Privada a partir de seguroDesemprego e previdenciaPrivada do .json (chaves
    seguro_desemprego_ops e previdencia_privada_ops da PJE-BD, já validadas na porta). Sem elas, as telas ficam no padrão.
    Roda depois das Verbas (a lista de salários devidos do seguro mostra as verbas do cálculo). O que a tela recusar ou
    não deixar como pedido interrompe: o cálculo sairia sem o seguro ou a previdência pedidos."""

    def __init__(self, source):
        self.planilha_base = ler_pje_bd(source)
        self.delay = 10
        self.objTools = Control()

    def _pedido(self, chave):
        for k, v in zip(self.planilha_base['IDENTIFICADOR'], self.planilha_base['INFORMACAO']):
            if isinstance(k, str) and k.strip() == chave and not valor_vazio(v):
                return json.loads(v)
        return None

    def _esperar(self, driver, segundos=1.0):
        self.objTools.aguardar_carregamento(driver)
        time.sleep(segundos)

    def _mensagens(self, driver):
        return driver.execute_script(r"""return [...document.querySelectorAll('[id^="formulario:painelMensagens"] table, .rich-message-label')]
            .map(e => e.textContent.split('//<!')[0].trim().replace(/\s+/g, ' ')).filter(t => t).join(' | ');""")

    def _rotulo(self, driver, elemento):
        return driver.execute_script(
            "const l = document.querySelector(`label[for='${arguments[0].id}']`); return l ? l.textContent.trim() : '';", elemento)

    def _radio(self, driver, alvo, rotulo):
        return next((e for e in driver.find_elements(By.CSS_SELECTOR, f"input[type=radio][id^='formulario:{alvo}:']")
                     if self._rotulo(driver, e) == rotulo), None)

    def _linhas(self, driver, tabela):
        return driver.execute_script("""const t = document.getElementById(arguments[0]);
            return t ? [...t.querySelectorAll('tbody tr')].map(r => r.innerText.replace(/\\s+/g, ' ').trim()).filter(x => x) : [];""",
                                     f"formulario:{tabela}")

    def _texto(self, driver, alvo, valor):
        campo = driver.find_element(By.ID, f"formulario:{alvo}")
        campo.click()
        campo.send_keys(Keys.CONTROL, "a")
        campo.send_keys(Keys.DELETE)
        campo.send_keys(valor)
        campo.send_keys(Keys.TAB)
        self._esperar(driver, 0.5)

    def _aplicar(self, driver, tela, ops):
        """caixa → rádio → lista → '+' (históricos e verbas) → texto: o ajax de caixas, rádios e '+' redesenha painéis e
        apagaria o que fosse só digitado antes. No fim, confere tudo."""
        fase = {"caixa": 0, "radio": 1, "lista": 2, "mais": 3, "texto": 4}
        ops = sorted(ops, key=lambda op: fase[op[0]])
        for tipo, alvo, valor in ops:
            if tipo == "caixa":
                caixa = driver.find_element(By.ID, f"formulario:{alvo}")
                if caixa.is_selected() != valor:
                    if not caixa.is_enabled() or not caixa.is_displayed():
                        return interromper(tela, f"'{alvo}' não está disponível na tela neste cálculo")
                    driver.execute_script("arguments[0].click();", caixa)
                    self._esperar(driver, 2)
            elif tipo == "radio":
                radio = self._radio(driver, alvo, valor)
                if radio is None:
                    opcoes = [self._rotulo(driver, e) for e in driver.find_elements(By.CSS_SELECTOR, f"input[type=radio][id^='formulario:{alvo}:']")]
                    return interromper(tela, f"opção '{valor}' não existe em '{alvo}' neste cálculo (há: {', '.join(opcoes) or 'nenhuma'})")
                if not radio.is_selected():
                    driver.execute_script("arguments[0].click();", radio)
                    self._esperar(driver, 2)
            elif tipo == "lista":
                campos = driver.find_elements(By.ID, f"formulario:{alvo}")
                if not campos or not campos[0].is_displayed() or not campos[0].is_enabled():
                    return interromper(tela, f"'{alvo}' não está disponível na tela neste cálculo")
                opcoes = [o.text.strip() for o in Select(campos[0]).options]
                if valor not in opcoes:
                    return interromper(tela, f"opção '{valor}' não existe em '{alvo}' (há: {', '.join(o for o in opcoes if o)})")
                Select(campos[0]).select_by_visible_text(valor)
                self._esperar(driver)
            elif tipo == "mais":
                if alvo == "historico":
                    lista, botao, escolha = "historicoSalarial", "cmdAdicionarHistoricoSalarial", valor
                else:
                    lista, botao, escolha = "verba", "cmdAdicionarSalarioDevido", valor[0]
                seletor = Select(driver.find_element(By.ID, f"formulario:{lista}"))
                opcoes = [o.text.strip() for o in seletor.options]
                achada = next((o for o in opcoes if o.upper() == escolha.upper()), None)
                if achada is None:
                    return interromper(tela, f"{alvo} '{escolha}' não está na lista da tela (há: {', '.join(o for o in opcoes if o) or 'nenhum'})")
                seletor.select_by_visible_text(achada)
                self._esperar(driver, 0.5)
                if alvo == "verba":
                    Select(driver.find_element(By.ID, "formulario:integralizar")).select_by_visible_text(valor[1])
                    self._esperar(driver, 0.5)
                driver.execute_script("arguments[0].click();", driver.find_element(By.ID, f"formulario:{botao}"))
                self._esperar(driver, 2)
            elif tipo == "texto":
                campo = driver.find_elements(By.ID, f"formulario:{alvo}")
                if not campo or not campo[0].is_displayed() or not campo[0].is_enabled():
                    return interromper(tela, f"'{alvo}' não está disponível na tela (valor {valor!r} não aplicado)")
                self._texto(driver, alvo, valor)
        # conferência antes de salvar
        digitos = lambda t: re.sub(r"\D", "", str(t)).lstrip("0")
        for tipo, alvo, valor in ops:
            if tipo == "caixa" and driver.find_element(By.ID, f"formulario:{alvo}").is_selected() != valor:
                return interromper(tela, f"'{alvo}' não ficou {'marcado' if valor else 'desmarcado'}")
            if tipo == "radio" and not ((radio := self._radio(driver, alvo, valor)) and radio.is_selected()):
                return interromper(tela, f"'{valor}' não ficou marcado em '{alvo}'")
            if tipo == "lista" and Select(driver.find_element(By.ID, f"formulario:{alvo}")).first_selected_option.text.strip() != valor:
                return interromper(tela, f"'{alvo}' não ficou em '{valor}'")
            if tipo == "texto" and digitos(driver.find_element(By.ID, f"formulario:{alvo}").get_attribute("value")) != digitos(valor):
                return interromper(tela, f"'{alvo}' ficou {driver.find_element(By.ID, f'formulario:{alvo}').get_attribute('value')!r} em vez de {valor!r}")
            if tipo == "mais":
                tabela = "listagemHistoricoSalarial" if alvo == "historico" else "listagemSalarioDevido"
                procurado = (valor if alvo == "historico" else valor[0]).upper()
                if not any(procurado in linha.upper() for linha in self._linhas(driver, tabela)):
                    return interromper(tela, f"{alvo} '{procurado}' não entrou na lista da tela")
        return True

    def _salvar(self, driver, tela):
        WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.ID, "formulario:salvar"))).click()
        self._esperar(driver, 2)
        texto = self._mensagens(driver)
        if "Operação realizada com sucesso" not in texto:
            return interromper(tela, texto or "o PJe-Calc não confirmou ao salvar")
        print(f"- [{tela}]: salvo")
        return True

    def _abrir_seguro(self, driver):
        link = next((a for a in driver.find_elements(By.CSS_SELECTOR, "a[id^='formulario:j_id38']") if a.text.strip() == "Seguro-desemprego"), None)
        if link is None:
            return interromper("Seguro-desemprego", "item do menu não encontrado")
        driver.execute_script("arguments[0].click();", link)
        self._esperar(driver, 2)
        return True

    def main_seguro_desemprego(self, driver):
        ops = self._pedido("seguro_desemprego_ops")
        if not ops:
            print("- [Seguro-desemprego]: o pedido não traz a tela; fica o padrão do PJe-Calc")
            return
        if self._abrir_seguro(driver) and self._aplicar(driver, "Seguro-desemprego", ops):
            self._salvar(driver, "Seguro-desemprego")
        print('-- Fim - (Seguro-desemprego) --')

    def main_previdencia_privada(self, driver):
        ops = self._pedido("previdencia_privada_ops")
        if not ops:
            print("- [Previdência Privada]: o pedido não traz a tela; fica o padrão do PJe-Calc")
            return
        tela = "Previdência Privada"
        WebDriverWait(driver, self.delay).until(EC.element_to_be_clickable((By.CLASS_NAME, "menuImagePrevidenciaPrivada"))).click()
        self._esperar(driver, 2)
        caixas = [op for op in ops if op[0] == "caixa"]
        if caixas and self._aplicar(driver, tela, caixas) is not True:
            return
        periodos = [op for op in ops if op[0] == "periodo"]
        for _, inicio, fim, aliquota in periodos:
            self._texto(driver, "dataInicioPeriodoInputDate", inicio)
            self._texto(driver, "dataTerminoPeriodoInputDate", fim)
            self._texto(driver, "aliquota", aliquota)
            driver.execute_script("arguments[0].click();", driver.find_element(By.ID, "formulario:cmdIncluirAliquota"))
            self._esperar(driver, 2)
            texto = self._mensagens(driver)
            if texto and "sucesso" not in texto.lower():
                # ex.: "O valor do campo Competência Inicial deve ser igual ou maior que Data de Admissão"
                return interromper(tela, f"período {inicio} a {fim}: {texto}")
        linhas = self._linhas(driver, "listagem")
        faltam = [f"{i} a {f}" for _, i, f, _ in periodos if not any(i in linha and f in linha for linha in linhas)]
        if faltam:
            return interromper(tela, f"período(s) não entraram na lista: {', '.join(faltam)}")
        if self._salvar(driver, tela):
            print(f"- [{tela}]: {len(periodos)} período(s) de alíquota")
        print('-- Fim - (Previdência Privada) --')
