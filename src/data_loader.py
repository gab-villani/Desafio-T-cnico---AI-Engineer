"""Carregamento e regras de dados da Empório da Música, sem alterar os CSVs."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

PROJECT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_DIR / "data"
load_dotenv(PROJECT_DIR / ".env")

CSV_FILES = {
    "products": "desafio_tecnico_ai_eng - products.csv",
    "categories": "desafio_tecnico_ai_eng - categories.csv",
    "customers": "desafio_tecnico_ai_eng - customers.csv",
    "orders": "desafio_tecnico_ai_eng - orders.csv",
    "order_items": "desafio_tecnico_ai_eng - order_items.csv",
    "promotions": "desafio_tecnico_ai_eng - promotions.csv",
}
KNOWN_BRANDS = (
    "Music Man", "Yamaha", "Tagima", "Giannini", "Rozini", "Shelby", "Crafter",
    "Martin", "Taylor", "Takamine", "Kala", "Ohana", "Kalani", "Fender", "Gibson",
    "Ibanez", "PRS", "Pearl", "Tama", "Korg", "Nord", "Roland",
)
DEFAULT_REFERENCE_DATE = date(2026, 3, 1)


@dataclass(frozen=True)
class StoreData:
    """Tabelas tratadas e prontas para uso pelas ferramentas do agente."""

    products: pd.DataFrame
    categories: pd.DataFrame
    customers: pd.DataFrame
    orders: pd.DataFrame
    order_items: pd.DataFrame
    promotions: pd.DataFrame
    reference_date: date


def normalize_email(value: str) -> str:
    """Normaliza e-mail para conferência de identidade, sem alterar o valor original."""
    return str(value).strip().lower()


def normalize_phone(value: str) -> str:
    """Retém somente dígitos do telefone para conferência de identidade."""
    return re.sub(r"\D", "", str(value))


def phone_matches(provided_phone: str, stored_phone: str) -> bool:
    """Compara telefones pelos últimos 10 ou 11 dígitos, aceitando formatações usuais."""
    provided = normalize_phone(provided_phone)
    stored = normalize_phone(stored_phone)
    if not provided or not stored:
        return False
    return provided[-11:] == stored[-11:] or provided[-10:] == stored[-10:]


def calculate_payment_price(
    list_price: float,
    active_promo_percent: int | float | None,
    payment_method: str,
) -> float:
    """Calcula preço atual: PIX dá 5% somente quando não existe promoção ativa."""
    if active_promo_percent is not None and active_promo_percent > 0:
        return round(float(list_price) * (1 - float(active_promo_percent) / 100), 2)
    if payment_method.strip().lower() == "pix":
        return round(float(list_price) * 0.95, 2)
    return round(float(list_price), 2)


def _reference_date() -> date:
    raw_value = os.getenv("REFERENCE_DATE", DEFAULT_REFERENCE_DATE.isoformat())
    try:
        return date.fromisoformat(raw_value)
    except ValueError as error:
        raise ValueError("REFERENCE_DATE deve usar o formato YYYY-MM-DD.") from error


def _read_csv(filename: str) -> pd.DataFrame:
    path = DATA_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Arquivo de dados não encontrado: {path}")
    frame = pd.read_csv(path)
    for column in frame.select_dtypes(include=["object", "string"]).columns:
        frame[column] = frame[column].astype("string").str.strip()
    return frame


def _validate_unique_ids(frame: pd.DataFrame, table_name: str, id_column: str) -> None:
    if frame[id_column].isna().any() or frame[id_column].duplicated().any():
        raise ValueError(f"{table_name}.{id_column} deve ser preenchido e único.")


def _validate_foreign_key(child: pd.DataFrame, child_table: str, child_column: str, parent: pd.DataFrame, parent_table: str, parent_column: str) -> None:
    orphan_values = child.loc[child[child_column].notna() & ~child[child_column].isin(parent[parent_column]), child_column]
    if not orphan_values.empty:
        raise ValueError(f"Referências inválidas em {child_table}.{child_column} para {parent_table}.{parent_column}: {orphan_values.head(5).tolist()}")


def _brand_in_text(text: str, brand: str) -> bool:
    return bool(re.search(rf"\b{re.escape(brand)}\b", text, flags=re.IGNORECASE))


def _catalog_inconsistent(row: pd.Series) -> bool:
    name_brand = next((brand for brand in KNOWN_BRANDS if _brand_in_text(row["name"], brand)), None)
    if name_brand is None:
        return False
    product_text = f"{row['description']} {row['specs']}"
    return any(brand != name_brand and _brand_in_text(product_text, brand) for brand in KNOWN_BRANDS)


def load_data() -> StoreData:
    """Carrega, deriva regras comerciais e valida as tabelas da loja.

    Os arquivos de origem permanecem intactos. Para produtos com divergência de catálogo,
    ``catalog_inconsistent`` sinaliza que a descrição não deve ser exibida pelas tools;
    as specs continuam disponíveis conforme decisão documentada.
    """
    products = _read_csv(CSV_FILES["products"])
    categories = _read_csv(CSV_FILES["categories"])
    customers = _read_csv(CSV_FILES["customers"])
    orders = _read_csv(CSV_FILES["orders"])
    order_items = _read_csv(CSV_FILES["order_items"])
    promotions = _read_csv(CSV_FILES["promotions"])

    for frame, date_columns in ((products, ["created_at"]), (orders, ["order_date", "estimated_delivery"])):
        for column in date_columns:
            frame[column] = pd.to_datetime(frame[column], errors="raise")

    promotions["is_active"] = promotions["is_active"].astype(bool)
    active_promotions = promotions.loc[promotions["is_active"], ["product_id", "discount_percent"]].rename(columns={"discount_percent": "active_promo_percent"})
    products = products.merge(active_promotions, on="product_id", how="left", validate="one_to_one")
    products["active_promo_percent"] = products["active_promo_percent"].astype("Int64")
    products["final_price"] = products.apply(lambda row: calculate_payment_price(row.price_brl, row.active_promo_percent, "other"), axis=1)
    products["is_available"] = products["status"].eq("active") & products["stock_quantity"].gt(0)
    products["catalog_inconsistent"] = products.apply(_catalog_inconsistent, axis=1)
    customers["email_norm"] = customers["email"].map(normalize_email)
    customers["phone_norm"] = customers["phone"].map(normalize_phone)

    for frame, table_name, id_column in ((products, "products", "product_id"), (categories, "categories", "category_id"), (customers, "customers", "customer_id"), (orders, "orders", "order_id"), (promotions, "promotions", "promotion_id")):
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

    return StoreData(products, categories, customers, orders, order_items, promotions, _reference_date())
