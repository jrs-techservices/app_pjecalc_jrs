# -*- coding: utf-8 -*-
"""Sobe o serviço HTTP da automação PJe-Calc (uma instância por máquina)."""
import msvcrt
import os
import sys

from waitress import serve

from servico import banco, config
from servico.api import criar_app
from servico.fila import gerenciador

SAIDA_CONFIGURACAO = 2
SAIDA_JA_RODANDO = 3


def _travar_instancia():
    arquivo = open(config.LOCK_PATH, "a+")
    try:
        msvcrt.locking(arquivo.fileno(), msvcrt.LK_NBLCK, 1)
    except OSError:
        print("Já existe uma instância do serviço rodando nesta máquina.")
        sys.exit(SAIDA_JA_RODANDO)
    return arquivo


def main():
    for fluxo in (sys.stdout, sys.stderr):
        fluxo.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
    os.chdir(config.BASE_DIR)
    os.environ["PJECALC_SERVICO"] = "1"

    if not config.API_TOKEN:
        print("Defina PJECALC_API_TOKEN no arquivo .env antes de subir o serviço.")
        sys.exit(SAIDA_CONFIGURACAO)

    trava = _travar_instancia()
    banco.inicializar()
    recuperados = banco.recuperar_na_subida()
    gerenciador.iniciar(recuperados)

    print(f"- [servico] PJe-Calc automação ouvindo em http://{config.HOST}:{config.PORTA}/api/v1")
    print(f"- [servico] {len(recuperados)} execução(ões) retomada(s) da fila")
    if not config.RAIZES_PERMITIDAS:
        print("- [servico] aviso: PJECALC_RAIZES_PERMITIDAS vazio, qualquer pasta é aceita")
    try:
        serve(criar_app(), host=config.HOST, port=config.PORTA, threads=4)
    finally:
        trava.close()


if __name__ == "__main__":
    main()
