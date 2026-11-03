import unittest
import re
import pandas as pd
from src.agent import responder
from src.prompts import build_system_prompt

# Load product names for assertion
_PRODUCTS_DF = pd.read_csv('data/desafio_tecnico_ai_eng - products.csv')
_PRODUCT_NAMES = set(_PRODUCTS_DF['name'].str.lower())

class TestIdioma(unittest.TestCase):
    def test_prompt_pt_br_identical(self):
        # Build current prompt without idioma (defaults to pt-BR)
        prompt_default = build_system_prompt()
        prompt_pt = build_system_prompt("pt-BR")
        self.assertEqual(prompt_default, prompt_pt)

    def test_resposta_preco_en_preserva_valor(self):
        resp_pt = responder("Quanto custa o Takamine GD20?", [], idioma="pt-BR")
        resp_en = responder("Quanto custa o Takamine GD20?", [], idioma="en")
        # Both should contain the same price in R$
        price_pt = re.search(r"R\$\s*\d+[\.,]?\d*", resp_pt)
        price_en = re.search(r"R\$\s*\d+[\.,]?\d*", resp_en)
        self.assertIsNotNone(price_pt)
        self.assertIsNotNone(price_en)
        self.assertEqual(price_pt.group(), price_en.group())

    def test_status_pedido_sem_identificacao_en(self):
        resp = responder("Qual o status do pedido 5?", [], idioma="en")
        self.assertTrue("email" in resp.lower() or "phone" in resp.lower())

    def test_acessorio_recusado_en(self):
        resp = responder("Vocês vendem amplificador?", [], idioma="en")
        # Must contain the word "amplifier"
        self.assertIn("amplifier", resp.lower())
        # Must NOT contain any price (pattern R$) nor any product name from catalog
        self.assertIsNone(re.search(r"R\$", resp))
        lowered = resp.lower()
        for name in _PRODUCT_NAMES:
            if name in lowered:
                self.fail(f"Response contains product name '{name}' which should not be mentioned.")
        # Must mention instrument (case-insensitive)
        self.assertIn("instrument", lowered)

if __name__ == '__main__':
    unittest.main()
