"""Fase 0 — Gate de setup: pacote importável e fontes de dados localizáveis."""

from emporio import config


def test_pacote_importavel():
    import emporio

    assert emporio.__version__


def test_todos_os_csvs_existem():
    faltando = [nome for nome, caminho in config.CSV_FILES.items() if not caminho.is_file()]
    assert not faltando, f"CSVs não encontrados: {faltando}"


def test_pdf_de_politicas_existe():
    assert config.POLICIES_PDF.is_file(), config.POLICIES_PDF


def test_dependencias_principais_importaveis():
    import gradio  # noqa: F401
    import langchain  # noqa: F401
    import langchain_core  # noqa: F401
    import langchain_google_genai  # noqa: F401
    import numpy  # noqa: F401
    import pandas  # noqa: F401
    import pypdf  # noqa: F401

