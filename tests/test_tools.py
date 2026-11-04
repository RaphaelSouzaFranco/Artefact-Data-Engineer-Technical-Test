"""Fase 2 — Testes unitários das Tools do agente."""

import pytest
from emporio_da_musica.tools.catalog import (
    buscar_produto,
    consultar_cliente,
    verificar_status_pedido,
)


# --------------------------------------------------------------------------- #
# Tool: buscar_produto
# --------------------------------------------------------------------------- #
def test_buscar_produto_por_nome_sem_acento():
    res = buscar_produto.invoke({"termo_busca": "violao takamine"})
    assert res["status"] == "sucesso"
    assert res["total_encontrados"] > 0
    # Deve conter GD20, GC5CE ou GC1CE
    nomes = [p["nome"] for p in res["produtos"]]
    assert any("Takamine" in n for n in nomes)


def test_buscar_produto_com_promocao_ativa():
    # Produto 94: Taylor 110e tem 8% de desconto ativo
    res = buscar_produto.invoke({"termo_busca": "Taylor 110e"})
    assert res["status"] == "sucesso"
    assert len(res["produtos"]) >= 1
    p = res["produtos"][0]
    assert p["id"] == 94
    assert p["tem_promocao"] is True
    assert p["desconto_percent"] == 8.0
    assert p["preco_final_brl"] < p["preco_original_brl"]
    assert p["nome_promocao"] == "Desconto Exclusivo"


def test_buscar_produto_filtro_preco_e_categoria():
    res = buscar_produto.invoke({
        "termo_busca": "nylon",
        "categoria": "Violões",
        "preco_maximo": 600.0,
    })
    assert res["status"] == "sucesso"
    for p in res["produtos"]:
        assert p["preco_final_brl"] <= 600.0
        assert p["categoria"] == "Violões"


def test_buscar_produto_inexistente():
    res = buscar_produto.invoke({"termo_busca": "Saxofone Dourado Inexistente 999"})
    assert res["status"] == "vazio"
    assert res["total_encontrados"] == 0
    assert len(res["produtos"]) == 0


def test_buscar_produto_parametro_vazio():
    res = buscar_produto.invoke({"termo_busca": ""})
    assert res["status"] == "erro"
    assert "ao menos um termo" in res["mensagem"]


# --------------------------------------------------------------------------- #
# Tool: consultar_cliente
# --------------------------------------------------------------------------- #
def test_consultar_cliente_sucesso():
    # Lucas Mendes: (67) 99812-3456 / lucas.mendes@jmail.com
    res = consultar_cliente.invoke({
        "email": "Lucas.Mendes@jmail.com",
        "telefone": "+55 67 99812-3456",
    })
    assert res["status"] == "sucesso"
    assert res["cliente"]["id"] == 1
    assert res["cliente"]["nome"] == "Lucas Mendes da Silva"


def test_consultar_cliente_email_duplicado_desambiguado_por_telefone():
    # Bruno Carvalho Martins (id 11): (67) 98543-2109, bruno.martins@jmail.com
    # Bruno Martins (id 43): (67) 99456-3456, bruno.martins@jmail.com
    res11 = consultar_cliente.invoke({
        "email": "bruno.martins@jmail.com",
        "telefone": "67985432109",
    })
    assert res11["status"] == "sucesso"
    assert res11["cliente"]["id"] == 11

    res43 = consultar_cliente.invoke({
        "email": "bruno.martins@jmail.com",
        "telefone": "67994563456",
    })
    assert res43["status"] == "sucesso"
    assert res43["cliente"]["id"] == 43


def test_consultar_cliente_invalido():
    res = consultar_cliente.invoke({
        "email": "naoexiste@jmail.com",
        "telefone": "67999999999",
    })
    assert res["status"] == "nao_encontrado"
    assert res["cliente"] is None


# --------------------------------------------------------------------------- #
# Tool: verificar_status_pedido (Opção A - Segurança e Validação)
# --------------------------------------------------------------------------- #
def test_verificar_status_pedido_sucesso_completo():
    # Pedido 8: Ana Carolina Ferreira (id 2), status shipped, rastreio BRJL5544332BR
    res = verificar_status_pedido.invoke({
        "numero_pedido": "8",
        "email": "anacarol.ferreira@coldmail.com",
        "telefone": "(67) 99654-7821",
    })
    assert res["status"] == "sucesso"
    ped = res["pedido"]
    assert ped["id"] == 8
    assert ped["status"] == "shipped"
    assert ped["codigo_rastreio"] == "BRJL5544332BR"
    assert ped["titular"] == "Ana Carolina Ferreira"
    assert len(ped["itens"]) == 1
    assert ped["itens"][0]["produto_id"] == 120  # Kala KA-C Concert Mogno


def test_verificar_status_pedido_com_hashtag_no_numero():
    res = verificar_status_pedido.invoke({
        "numero_pedido": "#8",
        "email": "anacarol.ferreira@coldmail.com",
        "telefone": "67 99654-7821",
    })
    assert res["status"] == "sucesso"
    assert res["pedido"]["id"] == 8


def test_verificar_status_pedido_dados_incorretos_opção_a():
    msg_esperada = "Não foi possível validar esses dados"

    # Caso 1: Telefone errado
    res1 = verificar_status_pedido.invoke({
        "numero_pedido": "8",
        "email": "anacarol.ferreira@coldmail.com",
        "telefone": "67900000000",
    })
    assert res1["status"] == "nao_encontrado"
    assert msg_esperada in res1["mensagem"]
    assert res1["pedido"] is None

    # Caso 2: Titular trocado (Lucas tentando ver pedido da Ana)
    res2 = verificar_status_pedido.invoke({
        "numero_pedido": "8",
        "email": "lucas.mendes@jmail.com",
        "telefone": "(67) 99812-3456",
    })
    assert res2["status"] == "nao_encontrado"
    assert msg_esperada in res2["mensagem"]
    assert res2["pedido"] is None

    # Caso 3: Pedido inexistente (id 999)
    res3 = verificar_status_pedido.invoke({
        "numero_pedido": "999",
        "email": "anacarol.ferreira@coldmail.com",
        "telefone": "(67) 99654-7821",
    })
    assert res3["status"] == "nao_encontrado"
    assert msg_esperada in res3["mensagem"]
    assert res3["pedido"] is None

