"""Fase W2/W3 — Testes de integração da interface Web própria (HTML5/CSS/JS + FastAPI)."""

from fastapi.testclient import TestClient
import pytest

from emporio_da_musica.app.server import app


@pytest.fixture
def client():
    return TestClient(app)


def test_serve_index_html(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Empório da Música" in response.text
    assert "id=\"chatWindow\"" in response.text
    assert "id=\"messageInput\"" in response.text
    # Garantir ausência de emojis nas tags e textos do HTML
    assert "🎸" not in response.text
    assert "🔄" not in response.text
    assert "🎵" not in response.text


def test_serve_static_assets(client):
    css_res = client.get("/static/styles.css")
    assert css_res.status_code == 200
    assert "var(--bg-primary)" in css_res.text

    js_res = client.get("/static/app.js")
    assert js_res.status_code == 200
    assert "emporio_thread_id" in js_res.text
