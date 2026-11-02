"""Carregamento e tratamento mínimo dos dados operacionais da Empório da Música."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
CSV_FILES = {
    "products": "desafio_tecnico_ai_eng - products.csv",
    "categories": "desafio_tecnico_ai_eng - categories.csv",
    "customers": "desafio_tecnico_ai_eng - customers.csv",
    "orders": "desafio_tecnico_ai_eng - orders.csv",
    "order_items": "desafio_tecnico_ai_eng - order_items.csv",
    "promotions": "desafio_tecnico_ai_eng - promotions.csv",
}


@dataclass(frozen=True)
class StoreData:
    """Tabelas prontas para uso pelas ferramentas do agente."""

    products: pd.DataFrame
    categories: pd.DataFrame
    customers: pd.DataFrame
    orders: pd.DataFrame
    order_items: pd.DataFrame
    promotions: pd.DataFrame


def _read_csv(filename: str) -> pd.DataFrame:
    """Lê um CSV da pasta de dados e remove espaços acidentais em textos."""
    path = DATA_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Arquivo de dados não encontrado: {path}")

    frame = pd.read_csv(path)
    text_columns = frame.select_dtypes(include=["object", "string"]).columns
    for column in text_columns:
        frame[column] = frame[column].astype("string").str.strip()
    return frame


def _validate_unique_ids(frame: pd.DataFrame, table_name: str, id_column: str) -> None:
    if frame[id_column].isna().any() or frame[id_column].duplicated().any():
        raise ValueError(f"{table_name}.{id_column} deve ser preenchido e único.")


def _validate_foreign_key(
    child: pd.DataFrame,
    child_table: str,
    child_column: str,
    parent: pd.DataFrame,
    parent_table: str,
    parent_column: str,
) -> None:
    orphan_values = child.loc[
        child[child_column].notna() & ~child[child_column].isin(parent[parent_column]),
        child_column,
    ]
    if not orphan_values.empty:
        examples = orphan_values.head(5).tolist()
        raise ValueError(
            f"Referências inválidas em {child_table}.{child_column} para "
            f"{parent_table}.{parent_column}: {examples}"
        )


def load_data() -> StoreData:
    """Carrega, padroniza o mínimo necessário e valida os CSVs da loja.

    Não altera descrições ou tenta corrigir divergências semânticas do catálogo.
    A disponibilidade é derivada de status ``active`` e estoque estritamente positivo.
    """
    products = _read_csv(CSV_FILES["products"])
    categories = _read_csv(CSV_FILES["categories"])
    customers = _read_csv(CSV_FILES["customers"])
    orders = _read_csv(CSV_FILES["orders"])
    order_items = _read_csv(CSV_FILES["order_items"])
    promotions = _read_csv(CSV_FILES["promotions"])

    for frame, date_columns in (
        (products, ["created_at"]),
        (orders, ["order_date", "estimated_delivery"]),
    ):
        for column in date_columns:
            frame[column] = pd.to_datetime(frame[column], errors="raise")

    promotions["is_active"] = promotions["is_active"].astype(bool)
    products["is_available"] = (
        products["status"].eq("active") & products["stock_quantity"].gt(0)
    )

    for frame, table_name, id_column in (
        (products, "products", "product_id"),
        (categories, "categories", "category_id"),
        (customers, "customers", "customer_id"),
        (orders, "orders", "order_id"),
        (promotions, "promotions", "promotion_id"),
    ):
        _validate_unique_ids(frame, table_name, id_column)

    _validate_foreign_key(products, "products", "category_id", categories, "categories", "category_id")
    _validate_foreign_key(orders, "orders", "customer_id", customers, "customers", "customer_id")
    _validate_foreign_key(order_items, "order_items", "order_id", orders, "orders", "order_id")
    _validate_foreign_key(order_items, "order_items", "product_id", products, "products", "product_id")
    _validate_foreign_key(promotions, "promotions", "product_id", products, "products", "product_id")

    if (products["price_brl"] < 0).any() or (products["stock_quantity"] < 0).any():
        raise ValueError("Products não pode conter preço ou estoque negativos.")
    if (order_items["quantity"] <= 0).any():
        raise ValueError("Order items deve conter quantidades positivas.")

    return StoreData(
        products=products,
        categories=categories,
        customers=customers,
        orders=orders,
        order_items=order_items,
        promotions=promotions,
    )
