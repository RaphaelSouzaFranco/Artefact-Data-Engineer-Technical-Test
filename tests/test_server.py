"""Fase W1 — Testes unitários dos endpoints da API FastAPI (Mocks 100% offline)."""

from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage

from emporio_da_musica.agent import EmporioAgent
from emporio_da_musica.app.server import app, set_agent
from emporio_da_musica.memory.sqlite_memory import SQLiteConversationMemory


@pytest.fixture(autouse=True)
def setup_mock_agent(tmp_path):
    """Configura um agente mockado para isolar a API de chamadas de LLM."""
    mock_llm = MagicMock()
    mock_bound = MagicMock()
    mock_llm.bind_tools.return_value = mock_bound
    mock_bound.invoke.return_value = AIMessage(content="Olá, sou o assistente virtual da Empório da Música.")

    test_db = tmp_path / "test_api_memory.sqlite3"
    memory = SQLiteConversationMemory(db_path=test_db)

    agent = EmporioAgent(llm=mock_llm, memory=memory)
    set_agent(agent)
    return agent


@pytest.fixture
def client():
    return TestClient(app)


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "emporio-da-musica-api"


def test_api_reset(client):
    response = client.post("/api/reset")
    assert response.status_code == 200
    data = response.json()
    assert "thread_id" in data
    assert len(data["thread_id"]) == 8


def test_api_chat_success(client):
    payload = {"message": "Vocês vendem violões?", "thread_id": "thread_test_1"}
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["thread_id"] == "thread_test_1"
    assert "Empório da Música" in data["reply"]


def test_api_chat_empty_message(client):
    payload = {"message": "   ", "thread_id": "thread_test_1"}
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 400
    assert "não pode ser vazia" in response.json()["detail"]


def test_api_history(client):
    # Enviar uma mensagem para popular o histórico
    client.post("/api/chat", json={"message": "Mensagem de teste", "thread_id": "thread_hist"})
    
    # Consultar histórico
    response = client.get("/api/history/thread_hist")
    assert response.status_code == 200
    data = response.json()
    assert data["thread_id"] == "thread_hist"
    assert len(data["messages"]) >= 2
    assert data["messages"][0]["role"] == "user"
    assert data["messages"][0]["content"] == "Mensagem de teste"
    assert data["messages"][1]["role"] == "assistant"

