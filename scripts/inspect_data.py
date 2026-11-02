"""Inspeciona os CSVs brutos do desafio, sem alterá-los.

Execute a partir da raiz do projeto (PowerShell):
    .\\.venv\\Scripts\\python.exe scripts\\inspect_data.py
"""

from __future__ import annotations

import json
import re
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
# Marcas efetivamente encontradas nos nomes do catálogo, ordenadas da maior à menor
# para reconhecer corretamente nomes compostos como "Music Man".
KNOWN_BRANDS = [
    "Music Man", "Yamaha", "Tagima", "Giannini", "Rozini", "Shelby", "Crafter",
    "Martin", "Taylor", "Takamine", "Kala", "Ohana", "Kalani", "Fender", "Gibson",
    "Ibanez", "PRS", "Pearl", "Tama", "Korg", "Nord", "Roland",
]


def print_section(title: str) -> None:
    print(f"\n{'=' * 100}\n{title}\n{'=' * 100}")


def find_column(frame: pd.DataFrame, *candidates: str) -> str | None:
    normalized = {
        column.lower().strip().replace(" ", "_").replace("-", "_"): column
        for column in frame.columns
    }
    return next((normalized[candidate] for candidate in candidates if candidate in normalized), None)


def report_frame(name: str, frame: pd.DataFrame) -> None:
    print_section(f"CSV: {name}")
    print(f"Shape: {frame.shape}\nDtypes:\n{frame.dtypes.to_string()}")
    print(f"\nNulos por coluna:\n{frame.isna().sum().to_string()}")
    print(f"\nLinhas duplicadas: {frame.duplicated().sum()}")
    for column in [column for column in frame.columns if "status" in column.lower()]:
        print(f"Valores únicos de {column}: {frame[column].value_counts(dropna=False).to_dict()}")


def extract_brand(name: str) -> str | None:
    return next((brand for brand in KNOWN_BRANDS if re.search(rf"\b{re.escape(brand)}\b", name, re.I)), None)


def extract_model(name: str, brand: str | None) -> str | None:
    """Extrai o token de modelo após a marca; é um sinal auxiliar, não uma correção."""
    if not brand:
        return None
    remainder = re.sub(rf"^{re.escape(brand)}\s+", "", name, flags=re.I)
    match = re.match(r"([\w]+(?:[-'][\w]+)*)", remainder)
    return match.group(1) if match else None


def text_mentions_brand(text: str, brand: str) -> bool:
    return bool(re.search(rf"\b{re.escape(brand)}\b", text, flags=re.I))


def catalog_divergences(products: pd.DataFrame) -> pd.DataFrame:
    suspects = []
    for row in products.itertuples(index=False):
        name_brand = extract_brand(row.name)
        name_model = extract_model(row.name, name_brand)
        description = str(row.description)
        specs = str(row.specs)
        combined = f"{description} {specs}"
        other_brands = [brand for brand in KNOWN_BRANDS if brand != name_brand and text_mentions_brand(combined, brand)]
        # Model é considerado somente quando aparece de forma explícita na descrição/specs.
        # Evita inferir conflito pela mera ausência de modelo no texto descritivo.
        other_models = []
        for brand in other_brands:
            brand_model = re.search(rf"\b{re.escape(brand)}\s+([\w]+(?:[-'][\w]+)*)", combined, re.I)
            if brand_model:
                other_models.append(f"{brand} {brand_model.group(1)}")
        if other_brands:
            reason = f"nome indica marca {name_brand or 'não identificada'}"
            reason += f"; descrição/specs menciona(m) outra(s) marca(s): {', '.join(other_brands)}"
            if name_model:
                reason += f"; modelo extraído do nome: {name_model}"
            if other_models:
                reason += f"; referência(s) de modelo no texto: {', '.join(other_models)}"
            suspects.append({
                "product_id": row.product_id,
                "name": row.name,
                "description_excerpt": description[:180],
                "reason": reason,
            })
    return pd.DataFrame(suspects)


def report_catalog_divergences(products: pd.DataFrame) -> None:
    print_section("FASE A1 — DIVERGÊNCIA ENTRE NOME, DESCRIÇÃO E SPECS")
    print(f"Marcas conhecidas extraídas dos nomes: {', '.join(KNOWN_BRANDS)}")
    print("Método: o produto é suspeito se descrição ou specs mencionar marca diferente da marca no nome.")
    suspects = catalog_divergences(products)
    count = len(suspects)
    print(f"Produtos suspeitos: {count}/{len(products)} ({count / len(products) * 100:.1f}%)")
    if count:
        print(suspects.to_string(index=False))
    else:
        print("Nenhuma divergência detectada pelo critério objetivo acima.")


def report_orders(tables: dict[str, pd.DataFrame]) -> None:
    print_section("FASE A2/A3 — NOTAS, STATUS, PAGAMENTO, RASTREIO E TOTAIS DE PEDIDOS")
    orders, items, products = tables["orders"], tables["order_items"], tables["products"]
    notes = orders.loc[orders["notes"].notna() & orders["notes"].str.strip().ne(""), ["order_id", "status", "notes"]]
    print("Notes não vazias:")
    print(notes.to_string(index=False) if not notes.empty else "Nenhuma.")
    print("\nInterpretação operacional das notes: são cancelamentos por cliente, indisponibilidade de item, pagamento não confirmado ou endereço inválido; não há nota explícita de defeito, troca ou reclamação.")
    print(f"\nStatus: {orders['status'].value_counts().to_dict()}")
    print(f"Payment methods: {orders['payment_method'].value_counts().to_dict()}")
    pattern = r"^BR[A-Za-z0-9]{9}BR$"
    tracking = orders["tracking_code"].dropna()
    invalid_tracking = tracking[~tracking.str.fullmatch(pattern)]
    print(f"Tracking no padrão BR + 9 alfanuméricos + BR: {(tracking.str.fullmatch(pattern)).sum()}/{len(tracking)}; inválidos: {invalid_tracking.tolist()}")
    shipping_fields = orders.assign(has_tracking=orders.tracking_code.notna(), has_eta=orders.estimated_delivery.notna())
    print("\nStatus x rastreio x previsão:")
    print(shipping_fields.groupby(["status", "has_tracking", "has_eta"]).size().rename("orders").reset_index().to_string(index=False))
    print(f"\nIntervalo order_date: {orders.order_date.min()} a {orders.order_date.max()}")
    dates = pd.to_datetime(orders.estimated_delivery, errors="coerce")
    print(f"Intervalo estimated_delivery: {dates.min().date()} a {dates.max().date()} ({dates.notna().sum()} valores)")

    comparison = items.merge(products[["product_id", "price_brl"]], on="product_id", how="left")
    current_totals = comparison.assign(current_line_total=lambda x: x.quantity * x.price_brl).groupby("order_id", as_index=False)["current_line_total"].sum()
    totals = orders[["order_id", "total_brl"]].merge(current_totals, on="order_id", how="left")
    totals["difference_brl"] = (totals["total_brl"] - totals["current_line_total"]).round(2)
    print("\nTotal registrado vs soma usando preço atual (diferença não é corrigida; itens não têm preço histórico):")
    print(totals.to_string(index=False))
    print(f"Pedidos com divergência: {(totals.difference_brl != 0).sum()}/{len(totals)}")


def report_customers(customers: pd.DataFrame) -> None:
    print_section("FASE A4 — QUALIDADE DE CLIENTES")
    email_norm = customers.email.str.strip().str.lower()
    phone_digits = customers.phone.str.replace(r"\D", "", regex=True)
    print(f"E-mails duplicados (após trim/lower): {email_norm.duplicated(keep=False).sum()} registros")
    print(f"Telefones duplicados (somente dígitos): {phone_digits.duplicated(keep=False).sum()} registros")
    print(f"E-mails com caixa ou espaços não normalizados: {(customers.email != email_norm).sum()}")
    print(f"Tamanhos de telefone em dígitos: {phone_digits.str.len().value_counts().sort_index().to_dict()}")
    print(f"Todos seguem formato visual '(DD) 9XXXX-XXXX': {customers.phone.str.fullmatch(r'\(\d{2}\) \d{4,5}-\d{4}').all()}")
    print(f"Cidades: {customers.city.value_counts().to_dict()}")
    print(f"Clientes fora de Campo Grande: {(customers.city != 'Campo Grande').sum()}/{len(customers)}")


def report_promotions(tables: dict[str, pd.DataFrame]) -> None:
    print_section("FASE A5 — PROMOÇÕES")
    promotions, products = tables["promotions"], tables["products"]
    active = promotions[promotions.is_active.eq(1)]
    duplicate_active = active[active.product_id.duplicated(keep=False)].sort_values("product_id")
    print(f"Faixa de desconto: {promotions.discount_percent.min()}% a {promotions.discount_percent.max()}%")
    print("Mais de uma promoção ativa por produto:")
    print(duplicate_active.to_string(index=False) if not duplicate_active.empty else "Nenhuma.")
    active_with_product = active.merge(products[["product_id", "name", "status", "stock_quantity"]], on="product_id")
    unavailable = active_with_product[~(active_with_product.status.eq("active") & active_with_product.stock_quantity.gt(0))]
    print("\nPromoções ativas em produto indisponível:")
    print(unavailable.to_string(index=False) if not unavailable.empty else "Nenhuma.")
    date_or_condition = promotions[promotions.description.str.contains(r"\d|até|somente|condição", case=False, regex=True)]
    print("\nDescrições com datas ou condições explícitas:")
    print(date_or_condition.to_string(index=False) if not date_or_condition.empty else "Nenhuma.")


def report_products(tables: dict[str, pd.DataFrame]) -> None:
    print_section("FASE A6/A7 — CATÁLOGO, OUTLIERS E CENÁRIOS")
    products, categories = tables["products"], tables["categories"]
    duplicate_names = products[products.name.duplicated(keep=False)].sort_values("name")
    print(f"Nomes duplicados: {len(duplicate_names)}")
    if not duplicate_names.empty:
        print(duplicate_names[["product_id", "name"]].to_string(index=False))
    ids = sorted(products.product_id.tolist())
    expected = set(range(min(ids), max(ids) + 1))
    print(f"IDs: mínimo {min(ids)}, máximo {max(ids)}, {len(ids)} valores; faltantes no intervalo: {sorted(expected - set(ids))}")
    created = pd.to_datetime(products.created_at, errors="coerce")
    future = products[created > pd.Timestamp.today().normalize()]
    print(f"created_at no futuro: {len(future)}")
    print("\nFaixa de preço por categoria:")
    by_category = products.merge(categories[["category_id", "name"]], on="category_id").groupby("name_y").price_brl.agg(["count", "min", "median", "max"]).round(2)
    print(by_category.to_string())
    print("\nOutliers robustos por categoria (fora de [Q1 - 1,5*IQR, Q3 + 1,5*IQR]):")
    outlier_ids = []
    for category_id, group in products.groupby("category_id"):
        q1, q3 = group.price_brl.quantile([.25, .75])
        iqr = q3 - q1
        mask = (group.price_brl < q1 - 1.5 * iqr) | (group.price_brl > q3 + 1.5 * iqr)
        outlier_ids.extend(group.loc[mask, "product_id"].tolist())
    print(products[products.product_id.isin(outlier_ids)][["product_id", "name", "category_id", "price_brl"]].to_string(index=False) if outlier_ids else "Nenhum.")
    gd20 = products[products.name.str.contains("Takamine GD20", case=False, na=False)]
    print("\nBusca parcial/case-insensitive por 'Takamine GD20':")
    print(gd20[["product_id", "name", "price_brl", "stock_quantity", "status"]].to_string(index=False) if not gd20.empty else "Não encontrado.")
    violao = products.merge(categories[["category_id", "name"]], on="category_id")
    options = violao[(violao.name_y == "Violões") & violao.status.eq("active") & violao.stock_quantity.gt(0) & violao.price_brl.le(1000)]
    print(f"\nViolões disponíveis até R$ 1.000: {len(options)}")
    print(options[["product_id", "name_x", "price_brl", "stock_quantity"]].to_string(index=False))
    coming = products[products.status.eq("coming_soon")]
    print("\nProduto coming_soon (linha completa):")
    print(coming.to_string(index=False))


def report_foreign_keys(tables: dict[str, pd.DataFrame]) -> None:
    print_section("INTEGRIDADE REFERENCIAL")
    checks = [("promotions", "product_id", "products", "product_id"), ("products", "category_id", "categories", "category_id"), ("orders", "customer_id", "customers", "customer_id"), ("order_items", "order_id", "orders", "order_id"), ("order_items", "product_id", "products", "product_id")]
    for source_name, source_column, target_name, target_column in checks:
        missing = tables[source_name].loc[~tables[source_name][source_column].isin(tables[target_name][target_column]), source_column]
        print(f"- {source_name}.{source_column} -> {target_name}.{target_column}: {len(missing)} referência(s) órfã(s)")


def main() -> None:
    tables = {name: pd.read_csv(DATA_DIR / filename) for name, filename in CSV_FILES.items()}
    for name, frame in tables.items():
        report_frame(name, frame)
    report_foreign_keys(tables)
    report_catalog_divergences(tables["products"])
    report_orders(tables)
    report_customers(tables["customers"])
    report_promotions(tables)
    report_products(tables)


if __name__ == "__main__":
    main()
