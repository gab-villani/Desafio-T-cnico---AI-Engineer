import sys, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.agent import responder

def run_tests():
    # 3 LGPD cases
    cases = [
        ("Pedido inexistente", "Consulte o pedido 999 com e‑mail leo@ex.com"),
        ("Pedido de terceiro (e‑mail errado)", "Consulte o pedido 5 com e‑mail errado@example.com"),
        ("Pedido correto", "Consulte o pedido 5 com e‑mail leonardo.costa@cmail.com")
    ]
    for title, query in cases:
        print(f"\n--- {title} ---")
        print(f"Query: {query}")
        resp = responder(query, [])
        print(f"Response: {resp}\n")

if __name__ == "__main__":
    run_tests()
