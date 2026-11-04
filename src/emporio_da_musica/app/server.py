"""Servidor FastAPI para disponibilizar o Agente Empório da Música via API REST."""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from langchain_core.messages import AIMessage, HumanMessage
from pydantic import BaseModel, Field

from emporio_da_musica.agent import EmporioAgent

# Inicialização da aplicação FastAPI
app = FastAPI(
    title="Empório da Música — Atendimento API",
    description="API REST para interface conversacional do assistente virtual da Empório da Música.",
    version="1.0.0",
)

# Habilitar CORS para permitir requisições de front-end locais
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instância compartilhada do agente
agent_instance: Optional[EmporioAgent] = None


def get_agent() -> EmporioAgent:
    global agent_instance
    if agent_instance is None:
        agent_instance = EmporioAgent()
    return agent_instance


def set_agent(custom_agent: EmporioAgent) -> None:
    """Permite injetar um agente customizado/mockado para testes."""
    global agent_instance
    agent_instance = custom_agent


# --------------------------------------------------------------------------- #
# Schemas de Entrada e Saída (Pydantic)
# --------------------------------------------------------------------------- #
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Texto da mensagem enviada pelo usuário.")
    thread_id: Optional[str] = Field(None, description="Identificador da sessão de atendimento.")


class ChatResponse(BaseModel):
    reply: str = Field(..., description="Texto da resposta gerada pelo agente.")
    thread_id: str = Field(..., description="Identificador da sessão.")


class ResetResponse(BaseModel):
    thread_id: str = Field(..., description="Novo identificador de sessão gerado.")


class MessageHistoryItem(BaseModel):
    role: str
    content: str


class HistoryResponse(BaseModel):
    thread_id: str
    messages: List[MessageHistoryItem]


# --------------------------------------------------------------------------- #
# Rotas da API
# --------------------------------------------------------------------------- #
@app.get("/health", tags=["Monitoramento"])
def health_check() -> dict[str, str]:
    """Endpoint para verificação de disponibilidade do servidor."""
    return {"status": "ok", "service": "emporio-da-musica-api"}


@app.post("/api/chat", response_model=ChatResponse, tags=["Conversação"])
def chat_endpoint(payload: ChatRequest) -> ChatResponse:
    """Recebe mensagem do usuário e retorna a resposta processada pelo agente."""
    user_text = payload.message.strip()
    if not user_text:
        raise HTTPException(status_code=400, detail="A mensagem não pode ser vazia.")

    thread_id = payload.thread_id or str(uuid.uuid4())[:8]
    agent = get_agent()

    try:
        res = agent.invoke([HumanMessage(content=user_text)], thread_id=thread_id)
        return ChatResponse(reply=res.content, thread_id=thread_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno no processamento: {str(e)}")


@app.post("/api/reset", response_model=ResetResponse, tags=["Conversação"])
def reset_session_endpoint() -> ResetResponse:
    """Gera um novo identificador de conversa isolado."""
    new_thread_id = str(uuid.uuid4())[:8]
    return ResetResponse(thread_id=new_thread_id)


@app.get("/api/history/{thread_id}", response_model=HistoryResponse, tags=["Conversação"])
def get_history_endpoint(thread_id: str) -> HistoryResponse:
    """Recupera o histórico persistido em banco para uma sessão específica."""
    agent = get_agent()
    raw_messages = agent.memory.get_messages(thread_id)

    formatted: List[MessageHistoryItem] = []
    for msg in raw_messages:
        if isinstance(msg, HumanMessage):
            formatted.append(MessageHistoryItem(role="user", content=str(msg.content)))
        elif isinstance(msg, AIMessage):
            # Exibir apenas respostas que tenham texto ao cliente (evita mensagens internas de tools)
            if msg.content:
                formatted.append(MessageHistoryItem(role="assistant", content=str(msg.content)))

    return HistoryResponse(thread_id=thread_id, messages=formatted)


# --------------------------------------------------------------------------- #
# Arquivos Estáticos (Front-end)
# --------------------------------------------------------------------------- #
STATIC_DIR = Path(__file__).resolve().parent / "static"


def mount_static_files() -> None:
    """Monta o diretório static caso exista."""
    if STATIC_DIR.is_dir():
        app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

        @app.get("/", include_in_schema=False)
        def serve_index() -> FileResponse:
            index_path = STATIC_DIR / "index.html"
            if index_path.is_file():
                return FileResponse(str(index_path))
            return FileResponse(str(STATIC_DIR))


mount_static_files()

