"""Gerenciador de memória e histórico conversacional persistido em SQLite."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import List, Optional

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    ChatMessage,
    FunctionMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
    messages_from_dict,
    messages_to_dict,
)

from emporio_da_musica import config


class SQLiteConversationMemory:
    """Persiste o histórico de mensagens agrupado por thread_id em SQLite."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or config.MEMORY_DB_PATH
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        return sqlite3.connect(str(self.db_path))

    def _init_db(self) -> None:
        """Cria as tabelas necessárias de histórico caso não existam."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversation_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    thread_id TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    message_json TEXT NOT NULL
                );
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_thread_id 
                ON conversation_history (thread_id);
            """)
            conn.commit()

    def get_messages(self, thread_id: str) -> List[BaseMessage]:
        """Recupera a lista cronológica de mensagens de uma sessão (thread_id)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT message_json FROM conversation_history
                WHERE thread_id = ?
                ORDER BY id ASC
                """,
                (thread_id,),
            )
            rows = cursor.fetchall()

        if not rows:
            return []

        dicts = [json.loads(r[0]) for r in rows]
        return messages_from_dict(dicts)

    def append_messages(self, thread_id: str, messages: List[BaseMessage]) -> None:
        """Adiciona uma ou mais mensagens ao histórico da thread."""
        if not messages:
            return

        dicts = messages_to_dict(messages)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(
                """
                INSERT INTO conversation_history (thread_id, message_json)
                VALUES (?, ?)
                """,
                [(thread_id, json.dumps(d, ensure_ascii=False)) for d in dicts],
            )
            conn.commit()

    def clear_thread(self, thread_id: str) -> None:
        """Apaga o histórico de uma conversa específica."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM conversation_history WHERE thread_id = ?",
                (thread_id,),
            )
            conn.commit()

    def list_threads(self) -> List[str]:
        """Lista todos os identificadores de thread salvos no banco."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT DISTINCT thread_id FROM conversation_history ORDER BY thread_id ASC"
            )
            rows = cursor.fetchall()
            return [r[0] for r in rows]

