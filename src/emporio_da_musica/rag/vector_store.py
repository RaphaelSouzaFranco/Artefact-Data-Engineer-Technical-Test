"""Motor de busca vetorial leve e persistente baseado em embeddings + numpy."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, List, Optional

import numpy as np

from emporio_da_musica import config
from emporio_da_musica.rag.pdf_parser import DocumentChunk, chunk_policies


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Calcula a similaridade de cosseno entre um vetor query e uma matriz de vetores."""
    dot_products = np.dot(b, a)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b, axis=1)
    # Evitar divisão por zero
    denominador = np.maximum(norm_b * norm_a, 1e-10)
    return dot_products / denominador


class LocalVectorStore:
    """Gerencia indexação de chunks, armazenamento e busca vetorial."""

    def __init__(self, index_dir: Optional[Path] = None):
        self.index_dir = index_dir or config.VECTOR_INDEX_DIR
        self.chunks_file = self.index_dir / "chunks.json"
        self.embeddings_file = self.index_dir / "embeddings.npy"

        self.chunks: List[dict[str, Any]] = []
        self.embeddings: Optional[np.ndarray] = None

    def is_indexed(self) -> bool:
        """Verifica se o índice já foi gerado e salvo em disco."""
        return self.chunks_file.is_file() and self.embeddings_file.is_file()

    def save(self, chunks: List[DocumentChunk], embeddings: np.ndarray) -> None:
        """Salva os chunks e matriz de embeddings no diretório de armazenamento."""
        self.index_dir.mkdir(parents=True, exist_ok=True)
        
        chunks_data = [
            {"chunk_id": c.chunk_id, "section_title": c.section_title, "content": c.content}
            for c in chunks
        ]
        with open(self.chunks_file, "w", encoding="utf-8") as f:
            json.dump(chunks_data, f, ensure_ascii=False, indent=2)

        np.save(str(self.embeddings_file), embeddings)
        self.chunks = chunks_data
        self.embeddings = embeddings

    def load(self) -> None:
        """Carrega os chunks e a matriz de embeddings do disco."""
        if not self.is_indexed():
            raise FileNotFoundError(f"Índice vetorial não encontrado em {self.index_dir}")

        with open(self.chunks_file, "r", encoding="utf-8") as f:
            self.chunks = json.load(f)

        self.embeddings = np.load(str(self.embeddings_file))

    def build_index(self, embedder_func=None) -> None:
        """Constrói o índice a partir do PDF usando uma função geradora de embeddings."""
        chunks = chunk_policies()
        texts = [f"{c.section_title}\n{c.content}" for c in chunks]

        if embedder_func is None:
            # Import dinâmico para não falhar se GOOGLE_API_KEY ainda não estiver configurada
            from langchain_google_genai import GoogleGenerativeAIEmbeddings

            embedder = GoogleGenerativeAIEmbeddings(
                model=config.EMBEDDING_MODEL,
                google_api_key=config.GOOGLE_API_KEY,
            )
            embeddings_list = embedder.embed_documents(texts)
            embeddings_arr = np.array(embeddings_list, dtype=np.float32)
        else:
            embeddings_arr = embedder_func(texts)

        self.save(chunks, embeddings_arr)

    def search(self, query_vector: np.ndarray, top_k: int = 3) -> List[dict[str, Any]]:
        """Busca os top_k chunks mais similares ao vetor de consulta."""
        if self.embeddings is None:
            self.load()

        scores = cosine_similarity(query_vector, self.embeddings)
        top_indices = np.argsort(scores)[::-1][:top_k]

        results = []
        for idx in top_indices:
            chunk = self.chunks[idx].copy()
            chunk["score"] = float(scores[idx])
            results.append(chunk)

        return results

