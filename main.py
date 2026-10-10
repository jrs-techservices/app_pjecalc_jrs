import os
import pyautogui as pa
import pjecalc_main_base as base
import pjecalc_main_verbas as vb
from browser_pjecalc import WebDriver
import pjecalc_main_full_switch as full
from Tools.pjecalc_control import Control
from Tools.script_get_source_file import GUIAutomationJRS



def switch_decision(driver, value):

    alternative_case = {
        0: base.function_main(driver, value),
        1: vb.function_main_vb(driver, value),
        2: full.function_main(driver, value),
    }
    try:
        alternative_case.get(value[0], "Valor inválido!")
    except IndexError as e:
        print(f"- (Status da operação): Valor inválido - {e}")
        exit()


def function_main(driver):

    arquivo_permissao = r'C:\Windows\System32\FilePathJRS.txt'

    if os.path.exists(arquivo_permissao):

        objTools = Control()
        objTools.limparFilesTemp()
        objGUI = GUIAutomationJRS()
        objGUI.show_animation()
        lista_planilhas = objGUI.lista_ordenada
        print(f"- (Lista): {lista_planilhas}")

        # Switch Case
        switch_decision(driver, lista_planilhas)
    else:
        pa.alert(title='Rôberto', text='Operação não permitida! Entre em contato com o setor de TI.')


if __name__ == '__main__':

    objWeb = WebDriver()
    driver = objWeb.driver_web()
    function_main(driver)
    pa.alert(title='Rôberto', text='Automação finalizada!')
    driver.quit()