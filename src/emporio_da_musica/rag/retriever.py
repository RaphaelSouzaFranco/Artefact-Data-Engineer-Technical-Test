"""Mecanismo de consulta e recuperação semântica (RAG)."""

from __future__ import annotations

from typing import Any, List, Optional

import numpy as np

from emporio_da_musica import config
from emporio_da_musica.rag.vector_store import LocalVectorStore


class PolicyRetriever:
    """Interface de alto nível para consultar as políticas da loja."""

    def __init__(self, vector_store: Optional[LocalVectorStore] = None):
        self.store = vector_store or LocalVectorStore()

    def get_relevant_policy(self, query: str, top_k: int = 2) -> List[dict[str, Any]]:
        """Recupera as seções mais relevantes do manual de políticas para a dúvida."""
        if not self.store.is_indexed():
            # Constrói o índice na primeira execução
            self.store.build_index()

        from langchain_google_genai import GoogleGenerativeAIEmbeddings

        embedder = GoogleGenerativeAIEmbeddings(
            model=config.EMBEDDING_MODEL,
            google_api_key=config.GOOGLE_API_KEY,
        )
        query_vec = np.array(embedder.embed_query(query), dtype=np.float32)
        return self.store.search(query_vec, top_k=top_k)

