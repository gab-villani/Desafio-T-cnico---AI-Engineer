"""Smoke tests reais com API Gemini - evidências completas."""

import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from src.agent import responder

# Cenários do passo 8
SCENARIOS = [
    "Quais violões disponíveis até R$ 1000?",
    "Quanto custa o Takamine GD20?",
    "Qual o endereço e o horário da loja?",
    "Me arrependi da minha compra, posso devolver?",
    "Vocês vendem corda de violão?",
    "Quero consultar o pedido 5, meu e-mail é cliente.errado@example.com",
]


def run_smoke_tests():
    """Executa os 6 cenários e mostra evidências completas."""
    print("=" * 100)
    print("SMOKE TESTS REAIS - API GEMINI")
    print("=" * 100)
    print()

    for i, scenario in enumerate(SCENARIOS, 1):
        print(f"\n{'=' * 100}")
        print(f"CENÁRIO {i}/6")
        print(f"{'=' * 100}")
        print(f"PERGUNTA: {scenario}")
        print()

        historico = []
        start = time.time()

        try:
            resposta = responder(scenario, historico)
            elapsed = time.time() - start

            print(f"LATÊNCIA: {elapsed:.2f}s")
            print()
            print("RESPOSTA:")
            print("-" * 100)
            print(resposta)
            print("-" * 100)
            print()

            # Mostrar histórico para ver tool calls
            if len(historico) > 2:
                print("HISTÓRICO (tool calls intermediárias):")
                for idx, msg in enumerate(historico):
                    if idx == 0 or idx == len(historico) - 1:
                        continue  # Skip user message and final response
                    print(f"  {idx}. role={msg.get('role', 'unknown')}, "
                          f"content={str(msg.get('content', ''))[:100]}")
                print()

            print(f"✅ CENÁRIO {i} PASSOU")

        except Exception as e:
            elapsed = time.time() - start
            print(f"LATÊNCIA ATÉ FALHA: {elapsed:.2f}s")
            print(f"❌ CENÁRIO {i} FALHOU")
            print(f"ERRO: {type(e).__name__}: {e}")
            
            # Show full traceback for debugging
            import traceback
            print("\nTRACEBACK COMPLETO:")
            traceback.print_exc()
            print()

        print()

    print("=" * 100)
    print("SMOKE TESTS CONCLUÍDOS")
    print("=" * 100)


if __name__ == "__main__":
    run_smoke_tests()
