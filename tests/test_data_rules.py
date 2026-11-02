"""Testes das regras de dados aplicadas em memória."""

import unittest

import pandas as pd

from src.data_loader import calculate_payment_price, load_data, phone_matches


class DataRulesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data = load_data()

    def product(self, product_id: int):
        return self.data.products.loc[self.data.products.product_id.eq(product_id)].iloc[0]

    def test_active_product_with_zero_stock_is_not_available(self) -> None:
        self.assertFalse(self.product(96).is_available)

    def test_discontinued_product_is_not_available(self) -> None:
        product = self.product(113)
        self.assertEqual(product.status, "discontinued")
        self.assertFalse(product.is_available)

    def test_inactive_promotion_is_ignored(self) -> None:
        # Produto 95 possui promoção inativa de 12%; o preço final permanece o de tabela.
        product = self.product(95)
        self.assertTrue(pd.isna(product.active_promo_percent))
        self.assertEqual(product.final_price, product.price_brl)

    def test_pix_does_not_accumulate_with_active_promotion(self) -> None:
        product = self.product(90)  # promoção ativa de 18%
        expected_promotional_price = round(product.price_brl * 0.82, 2)
        self.assertEqual(
            calculate_payment_price(product.price_brl, product.active_promo_percent, "pix"),
            expected_promotional_price,
        )

    def test_phone_identity_accepts_different_formatting(self) -> None:
        customer = self.data.customers.loc[self.data.customers.customer_id.eq(1)].iloc[0]
        self.assertTrue(phone_matches("67998123456", customer.phone))
        self.assertTrue(phone_matches("(67) 99812-3456", customer.phone))

    def test_missing_tracking_code_remains_missing(self) -> None:
        confirmed_order = self.data.orders.loc[self.data.orders.order_id.eq(9)].iloc[0]
        self.assertEqual(confirmed_order.status, "confirmed")
        self.assertTrue(pd.isna(confirmed_order.tracking_code))
        self.assertTrue(pd.isna(confirmed_order.estimated_delivery))


if __name__ == "__main__":
    unittest.main()
