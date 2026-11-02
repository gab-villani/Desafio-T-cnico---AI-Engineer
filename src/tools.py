"""Ferramentas determinísticas consultadas pelo agente para dados e políticas."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from src.data_loader import StoreData, calculate_payment_price, normalize_email, phone_matches

POLICIES_PATH = Path(__file__).resolve().parents[1] / "políticas_da_loja.md"


def _records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    """Converte DataFrame para JSON seguro, preservando ausências como None."""
    clean = frame.astype(object).where(pd.notna(frame), None)
    return clean.to_dict(orient="records")


def _money(value: float) -> float:
    return round(float(value), 2)


class StoreTools:
    """Agrupa as consultas de dados sem permitir escrita nos CSVs."""

    def __init__(self, data: StoreData) -> None:
        self.data = data

    def _product_payload(self, product: pd.Series, include_description: bool = True) -> dict[str, Any]:
        """Monta uma resposta segura de catálogo para um único produto."""
        category = self.data.categories.loc[
            self.data.categories.category_id.eq(product.category_id), "name"
        ].iloc[0]
        promo_percent = None if pd.isna(product.active_promo_percent) else int(product.active_promo_percent)
        payload: dict[str, Any] = {
            "product_id": int(product.product_id),
            "name": product["name"],
            "category": category,
            "list_price_brl": _money(product.price_brl),
            "active_promotion": (
                {"discount_percent": promo_percent, "final_price_brl": _money(product.final_price)}
                if promo_percent else None
            ),
            "final_price_brl": _money(product.final_price),
            "stock_quantity": int(product.stock_quantity),
            "status": product.status,
            "is_available": bool(product.is_available),
            "specs": product.specs,
        }
        if bool(product.catalog_inconsistent):
            payload["catalog_notice"] = (
                "Há uma divergência de catálogo neste item. Não cite detalhes da descrição; "
                "confirme informações adicionais com a equipe."
            )
        elif include_description:
            payload["description"] = product.description
        return payload

    def buscar_produtos(
        self,
        nome: str | None = None,
        categoria: str | None = None,
        preco_max: float | None = None,
        preco_min: float | None = None,
        somente_disponiveis: bool = True,
    ) -> dict[str, Any]:
        """Busca instrumentos por nome, categoria e faixa de preço.

        Usa o preço final atual (promoção ativa, se houver) para filtros de preço. Por padrão,
        traz somente itens disponíveis: ativos e com estoque positivo. Nunca use este resultado
        para supor dados de produtos que não foram retornados.
        """
        products = self.data.products.copy()
        if nome:
            products = products[products.name.str.contains(nome.strip(), case=False, regex=False, na=False)]
        if categoria:
            category_ids = self.data.categories.loc[
                self.data.categories.name.str.contains(categoria.strip(), case=False, regex=False, na=False),
                "category_id",
            ]
            products = products[products.category_id.isin(category_ids)]
        if preco_min is not None:
            products = products[products.final_price.ge(float(preco_min))]
        if preco_max is not None:
            products = products[products.final_price.le(float(preco_max))]
        if somente_disponiveis:
            products = products[products.is_available]

        results = [self._product_payload(row, include_description=False) for _, row in products.sort_values("final_price").iterrows()]
        return {"ok": True, "count": len(results), "products": results}

    def detalhar_produto(self, nome_ou_id: str | int) -> dict[str, Any]:
        """Retorna preço, estoque, status, promoção e ficha de um instrumento por nome ou ID.

        Para item esgotado, futuro ou descontinuado, consulte o status retornado antes de responder.
        Itens com divergência de catálogo não retornam descrição e exigem cautela sobre detalhes.
        """
        query = str(nome_ou_id).strip()
        products = self.data.products
        matches = products[products.product_id.astype(str).eq(query)]
        if matches.empty:
            matches = products[products.name.str.contains(query, case=False, regex=False, na=False)]
        if matches.empty:
            return {"ok": False, "error": "Produto não encontrado. Peça o nome ou código do instrumento."}
        if len(matches) > 1:
            return {"ok": False, "error": "Encontrei mais de um produto. Peça um nome mais específico.", "matches": _records(matches[["product_id", "name"]])}
        return {"ok": True, "product": self._product_payload(matches.iloc[0])}

    def listar_promocoes_ativas(self) -> dict[str, Any]:
        """Lista somente promoções ativas de instrumentos que ainda estão disponíveis."""
        products = self.data.products
        promoted = products[products.active_promo_percent.notna() & products.is_available]
        results = [self._product_payload(row, include_description=False) for _, row in promoted.sort_values("final_price").iterrows()]
        return {"ok": True, "count": len(results), "promotions": results}

    def consultar_pedido(self, order_id: int | str, email_ou_telefone: str) -> dict[str, Any]:
        """Consulta pedido somente após validar e-mail ou telefone do cliente vinculado.

        Em qualquer falha de validação, retorna a mesma mensagem genérica e não confirma se o
        pedido existe. Use o e-mail ou telefone usado na compra.
        """
        generic_error = "Não consegui validar os dados informados para consultar esse pedido. Confira o número do pedido e o e-mail ou telefone usado na compra."
        try:
            numeric_order_id = int(str(order_id).strip())
        except (TypeError, ValueError):
            return {"ok": False, "error": generic_error}
        order_match = self.data.orders[self.data.orders.order_id.eq(numeric_order_id)]
        if order_match.empty:
            return {"ok": False, "error": generic_error}
        order = order_match.iloc[0]
        customer = self.data.customers.loc[self.data.customers.customer_id.eq(order.customer_id)].iloc[0]
        identity = str(email_ou_telefone)
        valid = normalize_email(identity) == customer.email_norm or phone_matches(identity, customer.phone_norm)
        if not valid:
            return {"ok": False, "error": generic_error}

        items = self.data.order_items[self.data.order_items.order_id.eq(order.order_id)].merge(
            self.data.products[["product_id", "name"]], on="product_id", how="left"
        )
        payload: dict[str, Any] = {
            "order_id": int(order.order_id),
            "status": order.status,
            "order_date": order.order_date.date().isoformat(),
            "total_brl": _money(order.total_brl),
            "payment_method": order.payment_method,
            "items": _records(items[["product_id", "name", "quantity"]]),
        }
        if pd.notna(order.tracking_code):
            payload["tracking_code"] = order.tracking_code
        if pd.notna(order.estimated_delivery):
            payload["estimated_delivery"] = order.estimated_delivery.date().isoformat()
        if pd.notna(order.notes):
            payload["note"] = order.notes
        if order.status in {"pending", "confirmed"}:
            payload["tracking_message"] = "O pedido ainda não foi despachado; por isso não há rastreio disponível."
        elif order.status == "cancelled":
            payload["tracking_message"] = "O pedido foi cancelado e não possui rastreio."
        return {"ok": True, "order": payload}

    def calcular_preco(self, product_id: int, forma_pagamento: str, parcelas: int = 1) -> dict[str, Any]:
        """Calcula o preço atual e parcelamento de um produto usando regras da loja.

        PIX tem 5% sobre preço de tabela apenas sem promoção ativa. Com promoção ativa, o preço
        promocional já é o menor e não recebe PIX adicional. Crédito aceita 1 a 12 parcelas sem
        juros: 1-3x requer parcela de pelo menos R$50; 4-6x, R$80; 7-12x, R$100.
        """
        product = self.data.products.loc[self.data.products.product_id.eq(product_id)]
        if product.empty:
            return {"ok": False, "error": "Produto não encontrado."}
        product = product.iloc[0]
        method = forma_pagamento.strip().lower()
        aliases = {"cartao_credito": "credito", "credit_card": "credito", "cartão de crédito": "credito", "cartao de credito": "credito", "cartão": "credito", "debit": "debito", "cartão de débito": "debito", "cartao de debito": "debito"}
        method = aliases.get(method, method)
        if method not in {"pix", "credito", "debito", "boleto"}:
            return {"ok": False, "error": "Forma de pagamento inválida. Use PIX, crédito, débito ou boleto."}
        if not isinstance(parcelas, int) or isinstance(parcelas, bool) or parcelas < 1:
            return {"ok": False, "error": "Parcelas deve ser um número inteiro maior ou igual a 1."}
        if method != "credito" and parcelas != 1:
            return {"ok": False, "error": "Somente cartão de crédito permite parcelamento."}
        if method == "credito" and parcelas > 12:
            return {"ok": False, "error": "O cartão de crédito permite até 12 parcelas sem juros."}

        promo = None if pd.isna(product.active_promo_percent) else int(product.active_promo_percent)
        price = calculate_payment_price(product.price_brl, promo, method)
        result: dict[str, Any] = {
            "ok": True,
            "product_id": int(product.product_id),
            "product_name": product["name"],
            "payment_method": method,
            "list_price_brl": _money(product.price_brl),
            "active_promo_percent": promo,
            "total_brl": price,
        }
        if parcelas > 1:
            installment = round(price / parcelas, 2)
            minimum = 50 if parcelas <= 3 else 80 if parcelas <= 6 else 100
            if installment < minimum:
                return {"ok": False, "error": f"Em {parcelas}x, a parcela seria R$ {installment:.2f}, abaixo do mínimo de R$ {minimum:.2f}.", "total_brl": price}
            result.update({"installments": parcelas, "installment_value_brl": installment, "interest": "0%"})
        return result

    def consultar_politica(self, topico: str) -> dict[str, Any]:
        """Retorna a seção aplicável do manual: trocas, frete, pagamento, garantia ou horários."""
        topic = topico.strip().lower().replace("á", "a").replace("ã", "a").replace("ç", "c").replace("é", "e").replace("ê", "e").replace("í", "i").replace("ó", "o").replace("ô", "o").replace("ú", "u")
        sections = {
            "trocas": ("Trocas e devoluções", "## **4. Política de Trocas e Devoluções**", "## **5. Política de Frete e Entregas**"),
            "frete": ("Frete e entregas", "## **5. Política de Frete e Entregas**", "## **6. Promoções e Descontos**"),
            "pagamento": ("Formas de pagamento", "## **3. Formas de Pagamento**", "## **4. Política de Trocas e Devoluções**"),
            "garantia": ("Garantia", "## **8. Garantia**", "## **9. Privacidade e Proteção de Dados**"),
            "horarios": ("Horários", "## **2. Horário de Funcionamento**", "## **3. Formas de Pagamento**"),
        }
        aliases = {"troca": "trocas", "devolucao": "trocas", "devolução": "trocas", "entrega": "frete", "horario": "horarios", "horário": "horarios", "pagamentos": "pagamento"}
        key = aliases.get(topic, topic)
        if key not in sections:
            return {"ok": False, "error": "Tópico não reconhecido. Use trocas, frete, pagamento, garantia ou horários."}
        title, start, end = sections[key]
        manual = POLICIES_PATH.read_text(encoding="utf-8")
        content = manual.split(start, 1)[1].split(end, 1)[0].strip()
        return {"ok": True, "topic": title, "policy": content}


TOOL_SCHEMAS = [
    {"name": "buscar_produtos", "description": "Busca instrumentos por nome, categoria, preço e disponibilidade atual.", "parameters": {"type": "object", "properties": {"nome": {"type": "string"}, "categoria": {"type": "string"}, "preco_max": {"type": "number"}, "preco_min": {"type": "number"}, "somente_disponiveis": {"type": "boolean", "default": True}}}},
    {"name": "detalhar_produto", "description": "Consulta dados atuais de um produto pelo nome ou ID.", "parameters": {"type": "object", "properties": {"nome_ou_id": {"type": "string"}}, "required": ["nome_ou_id"]}},
    {"name": "listar_promocoes_ativas", "description": "Lista promoções ativas de produtos disponíveis.", "parameters": {"type": "object", "properties": {}}},
    {"name": "consultar_pedido", "description": "Consulta um pedido após validar e-mail ou telefone do cliente vinculado.", "parameters": {"type": "object", "properties": {"order_id": {"type": "integer"}, "email_ou_telefone": {"type": "string"}}, "required": ["order_id", "email_ou_telefone"]}},
    {"name": "calcular_preco", "description": "Calcula preço por forma de pagamento e parcelamento conforme regras da loja.", "parameters": {"type": "object", "properties": {"product_id": {"type": "integer"}, "forma_pagamento": {"type": "string"}, "parcelas": {"type": "integer", "default": 1}}, "required": ["product_id", "forma_pagamento"]}},
    {"name": "consultar_politica", "description": "Consulta políticas de trocas, frete, pagamento, garantia ou horários.", "parameters": {"type": "object", "properties": {"topico": {"type": "string"}}, "required": ["topico"]}},
]
