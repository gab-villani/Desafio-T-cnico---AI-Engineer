"""Inspeciona os CSVs brutos do desafio antes de qualquer limpeza.

Execute a partir da raiz do projeto:
    py scripts/inspect_data.py
"""

from __future__ import annotations

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


def print_section(title: str) -> None:
    print(f"\n{'=' * 80}\n{title}\n{'=' * 80}")


def find_column(frame: pd.DataFrame, *candidates: str) -> str | None:
    """Localiza uma coluna sem depender de maiúsculas, espaços ou hífens."""
    normalized = {
        column.lower().strip().replace(" ", "_").replace("-", "_"): column
        for column in frame.columns
    }
    for candidate in candidates:
        if candidate in normalized:
            return normalized[candidate]
    return None


def report_frame(name: str, frame: pd.DataFrame) -> None:
    print_section(f"CSV: {name}")
    print(f"Shape: {frame.shape}")
    print("\nColunas e dtypes:")
    print(frame.dtypes.to_string())
    print("\nNulos por coluna:")
    print(frame.isna().sum().to_string())
    print(f"\nLinhas duplicadas: {frame.duplicated().sum()}")
    print("\nAmostra (primeiras 3 linhas):")
    print(frame.head(3).to_string(index=False))

    status_columns = [column for column in frame.columns if "status" in column.lower()]
    if status_columns:
        print("\nValores únicos de status:")
        for column in status_columns:
            print(f"- {column}: {frame[column].value_counts(dropna=False).to_dict()}")


def report_data_quality(tables: dict[str, pd.DataFrame]) -> None:
    print_section("VERIFICAÇÕES ESPECÍFICAS DE QUALIDADE")

    products = tables["products"]
    promotions = tables["promotions"]
    orders = tables["orders"]

    price_columns = [column for column in products.columns if "price" in column.lower() or "preco" in column.lower()]
    print("Possíveis colunas de preço e exemplos brutos:")
    for column in price_columns:
        print(f"- products.{column} ({products[column].dtype}): {products[column].dropna().head(5).tolist()}")

    string_columns = [column for column in products.columns if products[column].dtype == "object"]
    print("\nValores com espaços nas extremidades (produtos):")
    found_spaces = False
    for column in string_columns:
        values = products[column].dropna().astype(str)
        count = (values != values.str.strip()).sum()
        if count:
            found_spaces = True
            print(f"- {column}: {count}")
    if not found_spaces:
        print("- Nenhum encontrado.")

    stock_column = find_column(products, "stock", "estoque", "stock_quantity", "quantity_in_stock")
    if stock_column:
        numeric_stock = pd.to_numeric(products[stock_column], errors="coerce")
        print(f"\nEstoque zerado em products.{stock_column}: {(numeric_stock == 0).sum()}")
        print(f"Estoque negativo em products.{stock_column}: {(numeric_stock < 0).sum()}")
    else:
        print("\nColuna de estoque não identificada automaticamente.")

    active_column = find_column(promotions, "active", "is_active", "ativo", "ativa", "status")
    end_date_column = find_column(promotions, "end_date", "ends_at", "valid_until", "data_fim", "fim")
    if active_column:
        print(f"\nPossível campo de promoção ativa ({active_column}):")
        print(promotions[active_column].value_counts(dropna=False).to_dict())
    if end_date_column:
        parsed_end_dates = pd.to_datetime(promotions[end_date_column], errors="coerce")
        print(f"Promoções com data final anterior a hoje ({end_date_column}): {(parsed_end_dates < pd.Timestamp.today().normalize()).sum()}")

    tracking_column = find_column(orders, "tracking_code", "tracking", "codigo_rastreio")
    if tracking_column:
        blank_tracking = orders[tracking_column].isna() | orders[tracking_column].astype(str).str.strip().eq("")
        print(f"\nPedidos sem tracking_code ({tracking_column}): {blank_tracking.sum()}")
    else:
        print("\nColuna de tracking_code não identificada automaticamente.")


def report_foreign_keys(tables: dict[str, pd.DataFrame]) -> None:
    print_section("INTEGRIDADE REFERENCIAL")
    checks = [
        ("promotions", ("product_id",), "products", ("product_id",)),
        ("products", ("category_id",), "categories", ("category_id",)),
        ("orders", ("customer_id",), "customers", ("customer_id",)),
        ("order_items", ("order_id",), "orders", ("order_id",)),
        ("order_items", ("product_id",), "products", ("product_id",)),
    ]

    for source_name, source_candidates, target_name, target_candidates in checks:
        source = tables[source_name]
        target = tables[target_name]
        source_column = find_column(source, *source_candidates)
        target_column = find_column(target, *target_candidates)
        label = f"{source_name}.{source_column or source_candidates[0]} -> {target_name}.{target_column or target_candidates[0]}"
        if not source_column or not target_column:
            print(f"- {label}: NÃO FOI POSSÍVEL VERIFICAR (coluna não encontrada)")
            continue

        values = source[source_column].dropna()
        missing = values[~values.isin(target[target_column].dropna())]
        print(f"- {label}: {len(missing)} referência(s) órfã(s)")
        if not missing.empty:
            print(f"  Exemplos: {missing.head(5).tolist()}")


def main() -> None:
    tables = {}
    for name, filename in CSV_FILES.items():
        path = DATA_DIR / filename
        if not path.exists():
            raise FileNotFoundError(f"Arquivo esperado não encontrado: {path}")
        tables[name] = pd.read_csv(path)
        report_frame(name, tables[name])

    report_data_quality(tables)
    report_foreign_keys(tables)


if __name__ == "__main__":
    main()
