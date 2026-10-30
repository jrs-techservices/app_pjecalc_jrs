import os
import gc
import time
import shutil
import pyautogui as pa
from selenium.webdriver.common.by import By
from selenium.common import TimeoutException
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC



class Control:


    def limparFilesTemp_v2(self):

        dirs_temp = [
            "C:\\Windows\\Temp",
            os.path.expanduser("~\\AppData\\Local\\Temp"),
            os.path.expanduser("~\\Recent"),
        ]

        for dir_temp in dirs_temp:
            try:
                for item in os.listdir(dir_temp):
                    path = os.path.join(dir_temp, item)

                    if 'base_' in item:
                        print(f"- [!!] [{item}] [!!]")
                    try:
                        if os.path.isfile(path) or os.path.islink(path):
                            os.remove(path)
                            print(f"- [!!] [{item}] - [DELETADO] [!!]")
                        elif os.path.isdir(path):
                            shutil.rmtree(path)
                    except Exception:
                        continue
            except Exception:
                continue

        gc.collect(generation=0)
        gc.collect(generation=1)
        gc.collect(generation=2)


    def limparFilesTemp(self):

        dirSystemTemp = "C:\Windows\Temp"
        dirUserTemp = os.path.expanduser("~\AppData\Local\Temp")
        dirUserRecent = os.path.expanduser("~\Recent")

        try:
            for f in os.listdir(dirSystemTemp):
                try:
                    os.remove(os.path.join(dirSystemTemp, f))
                except (PermissionError, FileNotFoundError):  # outro processo pode apagar o arquivo antes
                    continue
        except:
            pass
            # print("- [Except dirSystemTemp]")

        for g in os.listdir(dirUserTemp):

            try:
                os.remove(os.path.join(dirUserTemp, g))
            except (PermissionError, FileNotFoundError):  # outro processo pode apagar o arquivo antes
                continue

        try:
            for h in os.listdir(dirUserRecent):
                try:
                    os.remove(os.path.join(dirUserTemp, h))
                except (PermissionError, FileNotFoundError):  # outro processo pode apagar o arquivo antes
                    continue
        except:
            pass
            # print("- [Except Folder Recent]")

        gc.collect(generation=0)
        gc.collect(generation=1)
        gc.collect(generation=2)


    def function_please_wait(self, driver):

        # try:

        while WebDriverWait(driver, 0.5).until(EC.visibility_of_element_located((By.CLASS_NAME, 'aguarde'))):
            print(" '-_-' ", end='')
            time.sleep(1.5)
        print("\nContinuando!")

        # except TimeoutException:
        #     pass

    # Conta as requisições ajax da página (o PJe-Calc é RichFaces/A4J: XMLHttpRequest). Instalado na 1ª espera de cada página.
    CONTADOR_AJAX = r"""if (!window.__ajaxContador) {
        window.__ajaxPendentes = 0; window.__ajaxContador = true;
        const enviar = XMLHttpRequest.prototype.send;
        XMLHttpRequest.prototype.send = function () {
            window.__ajaxPendentes++;
            this.addEventListener('loadend', () => { window.__ajaxPendentes = Math.max(0, window.__ajaxPendentes - 1); });
            return enviar.apply(this, arguments);
        };
        return true;
    }
    return false;"""
    PAGINA_PRONTA = r"""const a = document.getElementById('formulario:msgAguardeContentTable');
        const aguarde = !!(a && (a.offsetWidth || a.offsetHeight) && getComputedStyle(a).visibility !== 'hidden');
        return document.readyState === 'complete' && !aguarde && (window.__ajaxPendentes || 0) === 0;"""

    def _aguardar_classico(self, driver):
        try:
            while WebDriverWait(driver, 3).until(EC.visibility_of_element_located((By.ID, 'formulario:msgAguardeContentTable'))):
                print("...", end="")
                time.sleep(1)
        except TimeoutException:
            time.sleep(1)

    def aguardar_carregamento(self, driver):
        """Espera a tela ficar pronta: sem a janela "Aguarde", sem ajax pendente e com a página carregada, estável por 0,4 s.
        Antes, cada chamada esperava até 3 s a janela aparecer e mais 1 s (~4 s mesmo com a tela pronta; ~10 min por
        cálculo). Na 1ª chamada de cada página o contador de ajax acaba de ser instalado e não veria um pedido já em curso:
        essa usa a espera antiga. AGUARDAR_CLASSICO=1 volta ao comportamento antigo em todas."""
        if os.environ.get("AGUARDAR_CLASSICO") == "1":
            return self._aguardar_classico(driver)
        try:
            instalou_agora = driver.execute_script(self.CONTADOR_AJAX)
        except Exception:
            return self._aguardar_classico(driver)
        if instalou_agora:
            return self._aguardar_classico(driver)
        limite = time.time() + 60
        estavel_desde = None
        while time.time() < limite:
            try:
                pronta = driver.execute_script(self.PAGINA_PRONTA)
            except Exception:
                pronta = False  # página trocando: espera
            if pronta:
                estavel_desde = estavel_desde or time.time()
                if time.time() - estavel_desde >= 0.4:
                    return
            else:
                estavel_desde = None
                print("...", end="")
            time.sleep(0.1)


    def remover_filesDiretorioProcesso(self, diretorio):

        if diretorio:
            for file in diretorio:
                # print(f"- [Delete]: {file}")
                if '03 Automação' in file:
                    try:
                        os.remove(file)
                    except FileNotFoundError as e:
                        print(f"- [except][delete]: {e}")
                else:
                    continue

    # - Implement
    def enviar_relatorio_email(self, id_processo):

        texto = f"Não foi possível encontrar os arquivos (Planinhas Base/Verbas) no diretório 03 Automação, referente ao processo: {id_processo}\n\nO responsável pode ter esquecido de copiar os arquivos para a pasta.\n\nATT.: Rô-berto"

        contas = ["marcos.santos@jrspericia.com.br", "wylber.andrade@jrspericia.com.br", "lucas.fonseca@jrspericia.com.br"]

        # Assunto
        assunto = "Automação - PJeCalc"

        # Percorrer a lista de emails de destino e enviar o relatório do Push
        for email in contas:
            msg = MIMEMultipart()
            mensagem = texto
            password = os.getenv('ROBERTO_SMTP_SENHA', '')  # no .env (fora do repositório)
            msg['Subject'] = assunto
            msg['From'] = "ro-berto@jrspericia.com.br"
            msg['To'] = email
            msg.attach(MIMEText(mensagem, 'plain'))
            # create server
            server = smtplib.SMTP('mail.jrspericia.com.br', 587)
            server.starttls()
            # Login Credentials for sending the mail
            server.login(msg['From'], password)
            # send the message via the server.
            server.sendmail(msg['From'], msg['To'], msg.as_string())
            server.quit()
            print("E-mail enviado com sucesso para %s:" % (msg['To']))
            sleep(0.5)


if __name__ == '__main__':

    objTools = Control()
    diretorio = [r"J:\01 Perícias\01 Análise Pericial\9652_0000518-68.2022.5.06.0311 PJe\01 Laudo Pericial\03 Automação\9652 - Planilha Base v3.37.4.xlsb", r"J:\01 Perícias\01 Análise Pericial\9652_0000518-68.2022.5.06.0311 PJe\01 Laudo Pericial\03 Automação\9652 - Verbas v1.08.xlsm"]
    objTools.remover_filesDiretorioProcesso(diretorio)