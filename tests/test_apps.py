"""Fase 6 — Testes de inicialização e estrutura das interfaces CLI e Web."""

from unittest.mock import patch
import pytest

from emporio_da_musica.app.web import create_app, respond, reset_session


def test_gradio_app_structure():
    demo = create_app()
    assert demo is not None
    # Deve conter componentes chave
    assert any("Empório da Música" in str(getattr(block, "value", "")) for block in demo.blocks.values())


def test_reset_session():
    new_tid, history = reset_session()
    assert len(new_tid) == 8
    assert history == []


def test_respond_empty_message():
    msg, hist = respond("   ", [{"role": "user", "content": "olá"}], "t123")
    assert msg == ""
    assert len(hist) == 1  # Não altera


@patch("emporio_da_musica.app.web.agent.invoke")
def test_respond_with_mock_agent(mock_invoke):
    from langchain_core.messages import AIMessage
    mock_invoke.return_value = AIMessage(content="Resposta simulada do atendente.")

    history = []
    msg_out, hist_out = respond("Vocês vendem violão?", history, "thread_teste")

    assert msg_out == ""
    assert len(hist_out) == 2
    assert hist_out[0] == {"role": "user", "content": "Vocês vendem violão?"}
    assert hist_out[1] == {"role": "assistant", "content": "Resposta simulada do atendente."}

