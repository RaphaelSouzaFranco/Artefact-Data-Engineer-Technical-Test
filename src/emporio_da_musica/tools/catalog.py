"""Ferramentas operacionais do agente Empório da Música (LangChain tools).

Todas as tools retornam dicionários serializáveis em JSON para que o agente
possa interpretar e sintetizar a resposta com facilidade, sem quebrar o fluxo.
"""

from __future__ import annotations

import re
from typing import Any, Optional

from langchain_core.tools import tool

from emporio_da_musica.data import loader
from emporio_da_musica.data.text import normalize_email, normalize_phone, normalize_text


@tool
def buscar_produto(
    termo_busca: str,
    categoria: Optional[str] = None,
    preco_maximo: Optional[float] = None,
) -> dict[str, Any]:
    """Busca instrumentos musicais no catálogo da loja por nome, descrição ou categoria.
    
    Args:
        termo_busca: Palavra-chave ou nome do instrumento (ex: 'violao', 'takamine', 'yamaha').
        categoria: Nome opcional da categoria (ex: 'Violões', 'Guitarras', 'Ukuleles').
        preco_maximo: Valor máximo opcional em reais para filtrar os produtos.
    """
    df = loader.load_products()

    # Normalização do termo de busca
    termo_norm = normalize_text(termo_busca)
    
    # Se termo vazio e sem categoria, retorna aviso
    if not termo_norm and not categoria:
        return {
            "status": "erro",
            "mensagem": "Por favor, informe ao menos um termo de busca ou uma categoria.",
            "total_encontrados": 0,
            "produtos": [],
        }

    # Filtro base
    mask = pd_series_true = df["product_id"].notna()

    if termo_norm:
        # Busca todas as palavras do termo no search_text
        palavras = termo_norm.split()
        for p in palavras:
            mask = mask & df["search_text"].str.contains(re.escape(p), case=False, na=False)

    if categoria:
        cat_norm = normalize_text(categoria)
        mask = mask & df["category_name"].map(normalize_text).str.contains(re.escape(cat_norm), case=False, na=False)

    if preco_maximo is not None and preco_maximo > 0:
        mask = mask & (df["final_price_brl"] <= preco_maximo)

    filtrados = df[mask].copy()

    if filtrados.empty:
        return {
            "status": "vazio",
            "mensagem": "Nenhum produto encontrado com os critérios fornecidos.",
            "total_encontrados": 0,
            "produtos": [],
        }

    # Ordenar por relevância simples (produtos em estoque primeiro, depois menor preço)
    filtrados["em_estoque"] = filtrados["stock_quantity"] > 0
    filtrados = filtrados.sort_values(by=["em_estoque", "final_price_brl"], ascending=[False, True])

    resultados = []
    # Limita aos top 5 para manter o contexto enxuto conforme restrições de concisão
    for _, row in filtrados.head(5).iterrows():
        item = {
            "id": int(row["product_id"]),
            "nome": row["name"],
            "categoria": row["category_name"],
            "preco_original_brl": float(row["price_brl"]),
            "desconto_percent": float(row["promo_discount_percent"]),
            "preco_final_brl": float(row["final_price_brl"]),
            "tem_promocao": bool(row["promo_discount_percent"] > 0),
            "nome_promocao": row["promo_description"],
            "estoque": int(row["stock_quantity"]),
            "status": row["status"],
            "descricao": row["description"],
            "especificacoes": row["specs"],
        }
        resultados.append(item)

    return {
        "status": "sucesso",
        "total_encontrados": len(filtrados),
        "exibindo": len(resultados),
        "produtos": resultados,
    }


@tool
def consultar_cliente(email: str, telefone: str) -> dict[str, Any]:
    """Consulta os dados de um cliente a partir de seu e-mail e telefone.
    
    Args:
        email: E-mail do cliente (ex: 'lucas.mendes@jmail.com').
        telefone: Telefone do cliente (ex: '(67) 99812-3456' ou '67998123456').
    """
    df = loader.load_customers()
    
    email_norm = normalize_email(email)
    phone_norm = normalize_phone(telefone)

    if not email_norm or not phone_norm:
        return {
            "status": "nao_encontrado",
            "mensagem": "Não foi possível validar as informações do cliente. Verifique o e-mail e telefone fornecidos.",
            "cliente": None,
        }

    match = df[(df["email_norm"] == email_norm) & (df["phone_digits"] == phone_norm)]

    if match.empty:
        return {
            "status": "nao_encontrado",
            "mensagem": "Não foi possível validar as informações do cliente. Verifique o e-mail e telefone fornecidos.",
            "cliente": None,
        }

    cliente_row = match.iloc[0]
    return {
        "status": "sucesso",
        "mensagem": "Cliente autenticado com sucesso.",
        "cliente": {
            "id": int(cliente_row["customer_id"]),
            "nome": cliente_row["name"],
            "email": cliente_row["email"],
            "telefone": cliente_row["phone"],
            "cidade": cliente_row["city"],
        },
    }


@tool
def verificar_status_pedido(numero_pedido: str, email: str, telefone: str) -> dict[str, Any]:
    """Verifica os detalhes e status de um pedido existente após validação do titular.
    
    Args:
        numero_pedido: Número ou ID do pedido (ex: '8', '#8').
        email: E-mail do titular do pedido.
        telefone: Telefone do titular do pedido.
    """
    # Mensagem padronizada conforme Opção A decidida
    msg_invalido = (
        "Não foi possível validar esses dados. Por favor, confira o número do pedido, "
        "o e-mail e o telefone do titular."
    )

    # Limpar numero do pedido para dígitos
    digits_order = re.sub(r"\D", "", str(numero_pedido))
    if not digits_order:
        return {
            "status": "nao_encontrado",
            "mensagem": msg_invalido,
            "pedido": None,
        }

    order_id = int(digits_order)

    # 1. Carregar tabelas necessárias
    orders_df = loader.load_orders()
    customers_df = loader.load_customers()

    order_match = orders_df[orders_df["order_id"] == order_id]
    if order_match.empty:
        return {
            "status": "nao_encontrado",
            "mensagem": msg_invalido,
            "pedido": None,
        }

    order_row = order_match.iloc[0]
    cust_id = int(order_row["customer_id"])

    # 2. Validar se o titular corresponde ao e-mail e telefone fornecidos
    email_norm = normalize_email(email)
    phone_norm = normalize_phone(telefone)

    customer_match = customers_df[
        (customers_df["customer_id"] == cust_id)
        & (customers_df["email_norm"] == email_norm)
        & (customers_df["phone_digits"] == phone_norm)
    ]

    if customer_match.empty:
        return {
            "status": "nao_encontrado",
            "mensagem": msg_invalido,
            "pedido": None,
        }

    # 3. Se autenticado, enriquecer com itens do pedido
    items_df = loader.load_order_items()
    products_df = loader.load_products().set_index("product_id")

    order_items = items_df[items_df["order_id"] == order_id]
    itens_formatados = []

    for _, item_row in order_items.iterrows():
        pid = int(item_row["product_id"])
        qtd = int(item_row["quantity"])
        nome_prod = "Produto não identificado"
        preco_unit = None

        if pid in products_df.index:
            p_data = products_df.loc[pid]
            nome_prod = p_data["name"]
            preco_unit = float(p_data["final_price_brl"])

        itens_formatados.append({
            "produto_id": pid,
            "nome": nome_prod,
            "quantidade": qtd,
            "preco_unitario_brl": preco_unit,
        })

    # Tratamento de datas
    data_pedido = order_row["order_date"].strftime("%d/%m/%Y") if hasattr(order_row["order_date"], "strftime") else str(order_row["order_date"])
    previsao_entrega = None
    if order_row["estimated_delivery"] is not None and not str(order_row["estimated_delivery"]).lower().startswith("nat"):
        previsao_entrega = order_row["estimated_delivery"].strftime("%d/%m/%Y")

    return {
        "status": "sucesso",
        "mensagem": "Pedido encontrado com sucesso.",
        "pedido": {
            "id": order_id,
            "titular": customer_match.iloc[0]["name"],
            "data_pedido": data_pedido,
            "status": order_row["status"],
            "valor_total_brl": float(order_row["total_brl"]),
            "metodo_pagamento": order_row["payment_method"],
            "codigo_rastreio": order_row["tracking_code"],
            "previsao_entrega": previsao_entrega,
            "observacoes": order_row["notes"],
            "itens": itens_formatados,
        },
    }

