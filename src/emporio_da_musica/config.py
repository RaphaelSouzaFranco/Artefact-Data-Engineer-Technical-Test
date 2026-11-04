"""Configuração central do projeto.

Todos os caminhos de arquivos e parâmetros de modelo ficam aqui, para que o
restante do código nunca dependa de nomes de arquivos "hard-coded".
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# Raiz do repositório: src/emporio/config.py -> parents[2]
PROJECT_ROOT: Path = Path(__file__).resolve().parents[2]

load_dotenv(PROJECT_ROOT / ".env")

# --------------------------------------------------------------------------- #
# Fontes de dados
# --------------------------------------------------------------------------- #
ASSETS_DIR: Path = PROJECT_ROOT / "assets"
CSV_DIR: Path = ASSETS_DIR / "csv"
_CSV_PREFIX = "desafio_tecnico_ai_eng - "

# Nome lógico (usado no código) -> arquivo físico
CSV_FILES: dict[str, Path] = {
    "categories": CSV_DIR / f"{_CSV_PREFIX}categories.csv",
    "customers": CSV_DIR / f"{_CSV_PREFIX}customers.csv",
    "orders": CSV_DIR / f"{_CSV_PREFIX}orders.csv",
    "order_items": CSV_DIR / f"{_CSV_PREFIX}order_items.csv",
    "products": CSV_DIR / f"{_CSV_PREFIX}products.csv",
    "promotions": CSV_DIR / f"{_CSV_PREFIX}promotions.csv",
}

POLICIES_PDF: Path = ASSETS_DIR / "business rules" / "políticas_da_loja.pdf"

# --------------------------------------------------------------------------- #
# Artefatos gerados em runtime (ignorados pelo git)
# --------------------------------------------------------------------------- #
STORAGE_DIR: Path = PROJECT_ROOT / "storage"
VECTOR_INDEX_DIR: Path = STORAGE_DIR / "vector_index"
MEMORY_DB_PATH: Path = STORAGE_DIR / "memory.sqlite3"

# --------------------------------------------------------------------------- #
# Modelos (Gemini)
# --------------------------------------------------------------------------- #
GOOGLE_API_KEY: str | None = os.getenv("GOOGLE_API_KEY") or None
CHAT_MODEL: str = os.getenv("EMPORIO_CHAT_MODEL", "gemini-2.5-flash")
EMBEDDING_MODEL: str = os.getenv("EMPORIO_EMBEDDING_MODEL", "models/text-embedding-004")

