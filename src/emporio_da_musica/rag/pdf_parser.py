"""Módulo de extração e segmentação de texto do PDF de políticas da loja."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import List

import pypdf

from emporio_da_musica import config


@dataclass
class DocumentChunk:
    chunk_id: str
    section_title: str
    content: str


def extract_raw_pages(pdf_path: Path | None = None) -> List[str]:
    """Extrai o texto bruto de cada página do PDF, colapsando quebras de linhas espúrias."""
    path = pdf_path or config.POLICIES_PDF
    reader = pypdf.PdfReader(str(path))
    pages = []
    for page in reader.pages:
        text = page.extract_text() or ""
        # Normalização de quebras de linha e espaços artificiais gerados pelo Skia/PDF
        text_clean = re.sub(r"\s+", " ", text).strip()
        pages.append(text_clean)
    return pages


def clean_pdf_text(pages: List[str]) -> str:
    """Junta as páginas removendo cabeçalhos/rodapés repetitivos."""
    full_text = "\n".join(pages)
    
    # Remover padrões de rodapé como 'Página X', 'Versão 2.1...', 'Documento interno...'
    full_text = re.sub(r"Página\s+\d+", "", full_text, flags=re.IGNORECASE)
    
    # Colapsar espaços e quebras excessivas preservando parágrafos
    lines = [l.strip() for l in full_text.splitlines() if l.strip()]
    unified = " ".join(lines)
    unified = re.sub(r"\s+", " ", unified)
    return unified


SECTION_TITLES = [
    (1, "Sobre a Empório da Música"),
    (2, "Horário de Funcionamento"),
    (3, "Formas de Pagamento"),
    (4, "Política de Trocas e Devoluções"),
    (5, "Política de Frete e Entregas"),
    (6, "Promoções e Descontos"),
    (7, "Atendimento via WhatsApp"),
    (8, "Garantia"),
    (9, "Privacidade e Proteção de Dados"),
    (10, "Disposições Finais"),
]


def chunk_policies(pdf_path: Path | None = None) -> List[DocumentChunk]:
    """Segmenta o manual de políticas com base nas seções numeradas principais (1 a 10)."""
    pages = extract_raw_pages(pdf_path)
    text = clean_pdf_text(pages)

    # Localizar os índices de cada seção
    positions: List[tuple[int, str, int]] = []
    for num, title in SECTION_TITLES:
        # Procurar por 'X. Título' ignorando eventuais diferenças sutis de acento/espaço
        pattern = re.compile(rf"{num}\.\s+{re.escape(title[:10])}", re.IGNORECASE)
        m = pattern.search(text)
        if m:
            positions.append((num, title, m.start()))

    # Ordenar pelas posições encontradas
    positions.sort(key=lambda x: x[2])

    chunks: List[DocumentChunk] = []

    # Cabeçalho inicial antes da seção 1 (Endereço, Telefones, CNPJ)
    if positions and positions[0][2] > 0:
        header_text = text[: positions[0][2]].strip()
        if header_text:
            chunks.append(
                DocumentChunk(
                    chunk_id="sec_0_cabecalho",
                    section_title="Identificação e Contato da Loja",
                    content=header_text,
                )
            )

    for i, (num, title, start_idx) in enumerate(positions):
        end_idx = positions[i + 1][2] if i + 1 < len(positions) else len(text)
        sec_content = text[start_idx:end_idx].strip()
        chunks.append(
            DocumentChunk(
                chunk_id=f"sec_{num}",
                section_title=f"{num}. {title}",
                content=sec_content,
            )
        )

    return chunks
