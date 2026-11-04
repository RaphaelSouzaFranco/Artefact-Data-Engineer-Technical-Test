"""Camada de dados: carga, tipagem e enriquecimento dos CSVs.

Regras:
* Todos os CSVs são lidos em UTF-8 e recebem tipos explícitos.
* Cada loader é cacheado (``lru_cache``): os arquivos são lidos uma única vez.
  Os DataFrames retornados são compartilhados — **não os modifique in-place**.
* ``load_products`` já entrega a visão enriquecida usada pelas tools
  (categoria, promoção ativa, preço final e texto normalizado para busca).
"""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

import pandas as pd

from emporio_da_musica import config
from emporio_da_musica.data.text import normalize_email, normalize_phone, normalize_text

# Status válidos de produto e pedido, conforme os dados de origem.
PRODUCT_STATUSES = ("active", "discontinued", "coming_soon")
ORDER_STATUSES = ("pending", "confirmed", "shipped", "delivered", "cancelled")


def _read_csv(name: str, **kwargs: Any) -> pd.DataFrame:
    return pd.read_csv(config.CSV_FILES[name], encoding="utf-8", **kwargs)


def _parse_specs(raw: object) -> dict[str, Any]:
    """Converte a coluna JSON ``specs`` em dict; valores inválidos viram {}."""
    if not isinstance(raw, str) or not raw.strip():
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _optional_str(series: pd.Series) -> pd.Series:
    """Coluna de texto opcional: vazio/NaN vira ``None`` (dtype object).

    O dtype ``object`` é forçado explicitamente: no pandas 3, ``Series.map``
    infere o dtype ``str`` e converteria ``None`` de volta para ``NaN``.
    """
    values = [(v.strip() or None) if isinstance(v, str) else None for v in series]
    return pd.Series(values, index=series.index, dtype="object")


# --------------------------------------------------------------------------- #
# Tabelas base
# --------------------------------------------------------------------------- #
@lru_cache(maxsize=1)
def load_categories() -> pd.DataFrame:
    df = _read_csv("categories", dtype={"category_id": "int64"})
    return df


@lru_cache(maxsize=1)
def load_customers() -> pd.DataFrame:
    df = _read_csv("customers", dtype={"customer_id": "int64"})
    df["email_norm"] = df["email"].map(normalize_email)
    df["phone_digits"] = df["phone"].map(normalize_phone)
    return df


@lru_cache(maxsize=1)
def load_orders() -> pd.DataFrame:
    df = _read_csv(
        "orders",
        dtype={"order_id": "int64", "customer_id": "int64", "total_brl": "float64"},
    )
    df["order_date"] = pd.to_datetime(df["order_date"], format="%Y-%m-%d")
    df["estimated_delivery"] = pd.to_datetime(df["estimated_delivery"], format="%Y-%m-%d")
    for col in ("tracking_code", "notes"):
        df[col] = _optional_str(df[col])
    return df


@lru_cache(maxsize=1)
def load_order_items() -> pd.DataFrame:
    return _read_csv(
        "order_items",
        dtype={"order_id": "int64", "quantity": "int64", "product_id": "int64"},
    )


@lru_cache(maxsize=1)
def load_promotions() -> pd.DataFrame:
    df = _read_csv(
        "promotions",
        dtype={"promotion_id": "int64", "product_id": "int64", "discount_percent": "float64"},
    )
    df["is_active"] = df["is_active"].astype(int).astype(bool)
    return df


def active_promotions() -> pd.DataFrame:
    """Uma linha por produto com a promoção ativa de maior desconto.

    Promoções não são cumulativas (políticas, seção 6.2), por isso só a melhor
    promoção ativa de cada produto é considerada.
    """
    promos = load_promotions()
    active = promos[promos["is_active"]]
    return (
        active.sort_values("discount_percent", ascending=False)
        .drop_duplicates("product_id")
        .reset_index(drop=True)
    )


# --------------------------------------------------------------------------- #
# Visão enriquecida de produtos
# --------------------------------------------------------------------------- #
@lru_cache(maxsize=1)
def load_products() -> pd.DataFrame:
    """Produtos + categoria + promoção ativa + preço final + texto de busca.

    Colunas adicionadas:
        category_name, promo_discount_percent (0.0 se não houver),
        promo_description (None se não houver), final_price_brl,
        name_norm, search_text.
    """
    df = _read_csv(
        "products",
        dtype={
            "product_id": "int64",
            "price_brl": "float64",
            "category_id": "int64",
            "stock_quantity": "int64",
        },
    )
    df["specs"] = df["specs"].map(_parse_specs)
    df["created_at"] = pd.to_datetime(df["created_at"], format="%Y-%m-%d")

    categories = load_categories()[["category_id", "name"]].rename(columns={"name": "category_name"})
    df = df.merge(categories, on="category_id", how="left", validate="many_to_one")

    promos = active_promotions()[["product_id", "discount_percent", "description"]].rename(
        columns={"discount_percent": "promo_discount_percent", "description": "promo_description"}
    )
    df = df.merge(promos, on="product_id", how="left", validate="one_to_one")
    df["promo_discount_percent"] = df["promo_discount_percent"].fillna(0.0)
    df["promo_description"] = _optional_str(df["promo_description"])
    df["final_price_brl"] = (df["price_brl"] * (1 - df["promo_discount_percent"] / 100)).round(2)

    df["name_norm"] = df["name"].map(normalize_text)
    df["search_text"] = (
        df["name"] + " " + df["category_name"].fillna("") + " " + df["description"].fillna("")
    ).map(normalize_text)
    return df


def clear_cache() -> None:
    """Força a releitura dos CSVs na próxima chamada (útil em testes)."""
    for fn in (
        load_categories,
        load_customers,
        load_orders,
        load_order_items,
        load_promotions,
        load_products,
    ):
        fn.cache_clear()