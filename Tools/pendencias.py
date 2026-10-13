# -*- coding: utf-8 -*-
"""Pendências da execução: o que o PJe-Calc recusou ou a automação contornou.

Cada pendência sai numa linha marcada no console; o serviço a recolhe e devolve no bloco `pendencias` da API.
No Rôberto desktop só aparece no console, como antes.
"""
import os
import re

MARCA = "- [PENDÊNCIA]"
LINHA = re.compile(r"^- \[PENDÊNCIA\]\[(pjecalc|automacao)\]\[([^\]]+)\]: (.*)$")


def no_servico():
    return os.environ.get("PJECALC_SERVICO") == "1"


def registrar(tela, mensagem, origem="pjecalc"):
    mensagem = " ".join(str(mensagem or "").split()) or "o PJe-Calc não confirmou a operação"
    print(f"{MARCA}[{origem}][{tela}]: {mensagem}")


def de_relatorio(campo, *resto):
    """Chamada ao lado dos gerar_relatorio(..., '---------- Erro! ----------') das telas."""
    tela, _, detalhe = str(campo).partition(":")
    mensagem = resto[0] if resto else detalhe
    registrar(tela.strip(), mensagem)


def interromper(tela, mensagem):
    """Erro que deixa o cálculo inválido: registra e, no serviço, encerra a execução como `falhou`.

    O serviço intercepta o pyautogui.alert e interrompe a rodada (é o mesmo caminho das outras paradas da automação).
    No Rôberto desktop, só registra e segue, como antes.
    """
    registrar(tela, mensagem)
    if no_servico():
        import pyautogui as pa
        pa.alert(title="Rôberto", text=f"{tela}: {' '.join(str(mensagem).split())}")


def ler_linha(linha):
    """Linha do console → {tela, mensagem, origem} (ou None)."""
    achado = LINHA.match(linha.strip())
    if not achado:
        return None
    return {"tela": achado.group(2), "mensagem": achado.group(3), "origem": achado.group(1)}
