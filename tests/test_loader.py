"""Fase 1 — Camada de dados: contagens, tipos, joins e qualidade conhecida dos dados."""

import pandas as pd
import pytest

from emporio_da_musica.data import loader


# --------------------------------------------------------------------------- #
# Contagens e chaves
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    ("fn", "linhas"),
    [
        (loader.load_categories, 9),
        (loader.load_customers, 50),
        (loader.load_orders, 20),
        (loader.load_order_items, 22),
        (loader.load_products, 65),
        (loader.load_promotions, 25),
    ],
)
def test_contagem_de_linhas(fn, linhas):
    assert len(fn()) == linhas


@pytest.mark.parametrize(
    ("fn", "chave"),
    [
        (loader.load_categories, "category_id"),
        (loader.load_customers, "customer_id"),
        (loader.load_orders, "order_id"),
        (loader.load_products, "product_id"),
        (loader.load_promotions, "promotion_id"),
    ],
)
def test_chaves_primarias_unicas(fn, chave):
    assert fn()[chave].is_unique


def test_loader_e_cacheado():
    assert loader.load_products() is loader.load_products()


# --------------------------------------------------------------------------- #
# Tipos
# --------------------------------------------------------------------------- #
def test_tipos_de_produtos():
    df = loader.load_products()
    assert df["product_id"].dtype == "int64"
    assert df["price_brl"].dtype == "float64"
    assert df["stock_quantity"].dtype == "int64"
    assert pd.api.types.is_datetime64_any_dtype(df["created_at"])
    assert set(df["status"]) <= set(loader.PRODUCT_STATUSES)


def test_specs_viram_dict():
    df = loader.load_products()
    assert df["specs"].map(lambda s: isinstance(s, dict)).all()
    assert df["specs"].map(len).gt(0).all(), "Nenhum produto deveria ficar com specs vazio"
    yamaha_c40 = df.set_index("product_id").loc[81, "specs"]
    assert yamaha_c40["strings"] == "nylon"
    assert yamaha_c40["top"] == "Spruce"


def test_acentos_preservados_utf8():
    df = loader.load_products().set_index("product_id")
    assert df.loc[81, "description"].startswith("Violão clássico")


def test_tipos_de_pedidos():
    df = loader.load_orders().set_index("order_id")
    assert pd.api.types.is_datetime64_any_dtype(df["order_date"])
    assert pd.api.types.is_datetime64_any_dtype(df["estimated_delivery"])
    assert set(df["status"]) <= set(loader.ORDER_STATUSES)
    # Pedido enviado: tem rastreio e previsão.
    assert df.loc[8, "tracking_code"] == "BRJL5544332BR"
    assert df.loc[8, "estimated_delivery"] == pd.Timestamp("2026-02-28")
    # Pedido confirmado: campos opcionais vazios viram None / NaT.
    assert df.loc[9, "tracking_code"] is None
    assert df.loc[9, "notes"] is None
    assert pd.isna(df.loc[9, "estimated_delivery"])
    # Pedido cancelado: motivo em notes.
    assert df.loc[17, "notes"] == "Pedido cancelado pelo cliente antes do processamento"


def test_contatos_normalizados():
    df = loader.load_customers().set_index("customer_id")
    assert df.loc[1, "phone_digits"] == "67998123456"
    assert df.loc[1, "email_norm"] == "lucas.mendes@jmail.com"


def test_promocoes_is_active_booleano():
    assert loader.load_promotions()["is_active"].dtype == bool


# --------------------------------------------------------------------------- #
# Enriquecimento de produtos (categoria + promoção)
# --------------------------------------------------------------------------- #
def test_todos_os_produtos_tem_categoria():
    df = loader.load_products()
    assert df["category_name"].notna().all()
    assert df.set_index("product_id").loc[81, "category_name"] == "Violões"


def test_promocoes_ativas():
    assert set(loader.active_promotions()["product_id"]) == {90, 94, 121, 127}


@pytest.mark.parametrize(
    ("product_id", "desconto", "preco_final"),
    [
        (90, 18.0, 1967.18),  # 2399 * 0.82
        (94, 8.0, 5519.08),  # 5999 * 0.92
        (121, 20.0, 439.20),  # 549 * 0.80
        (127, 10.0, 323.10),  # 359 * 0.90
    ],
)
def test_preco_final_com_promocao(product_id, desconto, preco_final):
    row = loader.load_products().set_index("product_id").loc[product_id]
    assert row["promo_discount_percent"] == desconto
    assert row["final_price_brl"] == pytest.approx(preco_final)
    assert row["promo_description"]


def test_promocao_inativa_nao_altera_preco():
    # Produto 93 tem 2 promoções, ambas inativas.
    row = loader.load_products().set_index("product_id").loc[93]
    assert row["promo_discount_percent"] == 0.0
    assert row["promo_description"] is None
    assert row["final_price_brl"] == row["price_brl"] == 11499.0


def test_texto_de_busca_sem_acentos():
    row = loader.load_products().set_index("product_id").loc[81]
    assert row["name_norm"] == "yamaha c40 nylon natural"
    assert "violoes" in row["search_text"]  # vem da categoria
    assert "violao classico" in row["search_text"]  # vem da descrição


# --------------------------------------------------------------------------- #
# Integridade referencial
# --------------------------------------------------------------------------- #
def test_itens_referenciam_pedidos_e_produtos_existentes():
    items = loader.load_order_items()
    assert items["order_id"].isin(loader.load_orders()["order_id"]).all()
    assert items["product_id"].isin(loader.load_products()["product_id"]).all()


def test_pedidos_referenciam_clientes_existentes():
    assert loader.load_orders()["customer_id"].isin(loader.load_customers()["customer_id"]).all()


def test_promocoes_referenciam_produtos_existentes():
    assert loader.load_promotions()["product_id"].isin(loader.load_products()["product_id"]).all()


# --------------------------------------------------------------------------- #
# Problemas conhecidos nos dados (documentados; as tools precisam lidar com eles)
# --------------------------------------------------------------------------- #
def test_casos_de_borda_de_status_de_produto():
    df = loader.load_products().set_index("product_id")
    assert (df.loc[96, "status"], df.loc[96, "stock_quantity"]) == ("active", 0)
    assert df.loc[113, "status"] == "discontinued"
    assert (df.loc[136, "status"], df.loc[136, "stock_quantity"]) == ("discontinued", 13)
    assert df.loc[130, "status"] == "coming_soon"


def test_email_duplicado_entre_clientes():
    df = loader.load_customers()
    dup = df[df["email_norm"] == "bruno.martins@jmail.com"]
    assert sorted(dup["customer_id"]) == [11, 43]
    # Telefones diferentes: e-mail + telefone juntos desambiguam o titular.
    assert dup["phone_digits"].is_unique

