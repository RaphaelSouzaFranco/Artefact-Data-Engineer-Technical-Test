"""Fase 1 — Normalização de texto e contato."""

import pytest

from emporio.data.text import normalize_email, normalize_phone, normalize_text


@pytest.mark.parametrize(
    ("entrada", "esperado"),
    [
        ("Violão", "violao"),
        ("  Violão   CLÁSSICO ", "violao classico"),
        ("Percussão e Teclados", "percussao e teclados"),
        ("Três Lagoas", "tres lagoas"),
        ("", ""),
        (None, ""),
        (float("nan"), ""),
    ],
)
def test_normalize_text(entrada, esperado):
    assert normalize_text(entrada) == esperado


@pytest.mark.parametrize(
    ("entrada", "esperado"),
    [
        ("(67) 99812-3456", "67998123456"),
        ("67 99812 3456", "67998123456"),
        ("+55 (67) 99812-3456", "67998123456"),
        ("5567998123456", "67998123456"),
        ("", ""),
        (None, ""),
    ],
)
def test_normalize_phone(entrada, esperado):
    assert normalize_phone(entrada) == esperado


def test_normalize_email():
    assert normalize_email("  Lucas.Mendes@JMail.com ") == "lucas.mendes@jmail.com"
    assert normalize_email(None) == ""

