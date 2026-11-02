import unittest
from src.agent import responder
from src.prompts import build_system_prompt

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
        import re
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
        self.assertIn("amplifier", resp.lower())
        # expect refusal phrase in English
        self.assertTrue("not" in resp.lower() or "do not" in resp.lower())

if __name__ == '__main__':
    unittest.main()
