"""Mapeamento e registro de tools do agente."""

from emporio.tools.catalog import (
    buscar_produto,
    consultar_cliente,
    verificar_status_pedido,
)

ALL_TOOLS = [
    buscar_produto,
    consultar_cliente,
    verificar_status_pedido,
]

__all__ = [
    "buscar_produto",
    "consultar_cliente",
    "verificar_status_pedido",
    "ALL_TOOLS",
]

