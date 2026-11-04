"""Mapeamento e registro de tools do agente."""

from emporio_da_musica.tools.catalog import (
    buscar_produto,
    consultar_cliente,
    verificar_status_pedido,
)
from emporio_da_musica.tools.rag_tool import consultar_politicas_da_loja

ALL_TOOLS = [
    buscar_produto,
    consultar_cliente,
    verificar_status_pedido,
    consultar_politicas_da_loja,
]

__all__ = [
    "buscar_produto",
    "consultar_cliente",
    "verificar_status_pedido",
    "consultar_politicas_da_loja",
    "ALL_TOOLS",
]

