# -*- coding: utf-8 -*-
"""Configuração do serviço HTTP, lida do .env na raiz do projeto."""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

API_TOKEN = os.getenv("PJECALC_API_TOKEN", "").strip()
HOST = os.getenv("PJECALC_HOST", "0.0.0.0")
PORTA = int(os.getenv("PJECALC_PORTA", "9300"))
PJECALC_URL = os.getenv("PJECALC_URL", "http://localhost:9257/pjecalc/pages/principal.jsf")
RAIZES_PERMITIDAS = [r.strip() for r in os.getenv("PJECALC_RAIZES_PERMITIDAS", "").split(";") if r.strip()]

ARQUIVO_PERMISSAO = Path(r"C:\Windows\System32\FilePathJRS.txt")
EXTENSOES_PLANILHA = {".xlsx", ".xlsm", ".xlsb", ".xls"}

DB_DIR = BASE_DIR / "db-sqlite"
DB_PATH = DB_DIR / "servico.db"
LOCK_PATH = DB_DIR / "servico.lock"
LIMITE_LOG_POR_EXECUCAO = 5000
CAPTURAS_DIR = BASE_DIR / "diagnostico" / "falhas"

DB_DIR.mkdir(exist_ok=True)
CAPTURAS_DIR.mkdir(parents=True, exist_ok=True)
