"""Fase 3 — Testes do motor RAG: parser, chunking e busca vetorial local."""

import numpy as np
import pytest

from emporio_da_musica.rag.pdf_parser import (
    DocumentChunk,
    SECTION_TITLES,
    chunk_policies,
    clean_pdf_text,
    extract_raw_pages,
)
from emporio_da_musica.rag.vector_store import LocalVectorStore, cosine_similarity


def test_extracao_paginas_pdf():
    pages = extract_raw_pages()
    assert len(pages) == 8
    # Verificar que contém termos cruciais da loja
    assert "EMPÓRIO DA MÚSICA" in pages[0].upper()


def test_chunking_secoes_principais():
    chunks = chunk_policies()
    # 1 cabeçalho + 10 seções = 11 chunks
    assert len(chunks) == 11
    
    chunk_map = {c.chunk_id: c for c in chunks}
    
    # Validar se as seções vitais foram capturadas com conteúdo adequado
    assert "sec_2" in chunk_map
    assert "Horário de Funcionamento" in chunk_map["sec_2"].section_title
    assert "09:00 às 18:00" in chunk_map["sec_2"].content

    assert "sec_4" in chunk_map
    assert "Trocas e Devoluções" in chunk_map["sec_4"].section_title
    assert "7 (sete) dias" in chunk_map["sec_4"].content

    assert "sec_5" in chunk_map
    assert "Frete e Entregas" in chunk_map["sec_5"].section_title
    assert "Campo Grande" in chunk_map["sec_5"].content


def test_cosine_similarity():
    v1 = np.array([1.0, 0.0, 0.0])
    v2 = np.array([1.0, 0.0, 0.0])
    v3 = np.array([0.0, 1.0, 0.0])

    matrix = np.array([v2, v3])
    sims = cosine_similarity(v1, matrix)
    
    assert sims[0] == pytest.approx(1.0)
    assert sims[1] == pytest.approx(0.0)


def test_local_vector_store_save_load_and_search(tmp_path):
    store = LocalVectorStore(index_dir=tmp_path)
    assert not store.is_indexed()

    chunks = [
        DocumentChunk("c1", "Horário", "A loja abre de segunda a sexta das 9h às 18h."),
        DocumentChunk("c2", "Frete", "Frete grátis para pedidos acima de R$ 500."),
        DocumentChunk("c3", "Troca", "Devoluções em até 7 dias corridos."),
    ]
    # Mock de embeddings sintéticos 3D
    mock_embeddings = np.array([
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0],
    ], dtype=np.float32)

    store.save(chunks, mock_embeddings)
    assert store.is_indexed()

    # Recarregar em nova instância
    loaded_store = LocalVectorStore(index_dir=tmp_path)
    loaded_store.load()
    assert len(loaded_store.chunks) == 3

    # Query alinhada com o chunk 2 (Frete)
    query_vec = np.array([0.1, 0.99, 0.0], dtype=np.float32)
    results = loaded_store.search(query_vec, top_k=2)

    assert len(results) == 2
    assert results[0]["chunk_id"] == "c2"
    assert results[0]["section_title"] == "Frete"
    assert results[0]["score"] > 0.9

