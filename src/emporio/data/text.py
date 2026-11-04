"""Utilitários de normalização de texto e contato.

Usados para comparar o que o cliente digita com os dados dos CSVs de forma
tolerante a acentos, maiúsculas/minúsculas, espaços e pontuação.
"""

from __future__ import annotations

import re
import unicodedata

_WHITESPACE_RE = re.compile(r"\s+")
_NON_DIGIT_RE = re.compile(r"\D")


def normalize_text(value: object) -> str:
    """Minúsculas, sem acentos e com espaços colapsados.

    >>> normalize_text("  Violão   CLÁSSICO ")
    'violao classico'
    """
    if value is None or (isinstance(value, float) and value != value):  # None / NaN
        return ""
    decomposed = unicodedata.normalize("NFKD", str(value))
    without_accents = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return _WHITESPACE_RE.sub(" ", without_accents).strip().lower()


def normalize_phone(value: object) -> str:
    """Mantém só os dígitos e remove o DDI 55, se houver.

    >>> normalize_phone("(67) 99812-3456")
    '67998123456'
    >>> normalize_phone("+55 67 99812 3456")
    '67998123456'
    """
    digits = _NON_DIGIT_RE.sub("", "" if value is None else str(value))
    if len(digits) in (12, 13) and digits.startswith("55"):
        digits = digits[2:]
    return digits


def normalize_email(value: object) -> str:
    """E-mail em minúsculas e sem espaços nas pontas."""
    return "" if value is None else str(value).strip().lower()

