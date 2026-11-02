#!/usr/bin/env python
"""Gera conversas de exemplo reais usando o agente e salva em examples/."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
print('PATH ADDED:', Path(__file__).resolve().parents[1] / "src")
from src.agent import responder

def save_conversation(history, filename):
    """Salva histórico como markdown."""
    path = Path(__file__).resolve().parents[1] / "examples" / filename
    with path.open("w", encoding="utf-8") as f:
        f.write(f"# {filename}\n\n")
        for msg in history:
            role = "🧑 Cliente" if msg["role"] == "user" else "🤖 Atendente"
            f.write(f"## {role}\n\n{msg['content']}\n\n")
    print(f"Salvo: {path}")

def run_scenario(name, messages):
    """Executa uma sequência de mensagens mantendo histórico."""
    history = []
    for i, msg in enumerate(messages):
        print(f"\n--- {name} - turno {i+1} ---")
        print(f"Cliente: {msg}")
        resp = responder(msg, history)
        print(f"Atendente: {resp}")
        history.append({"role": "user", "content": msg})
        history.append({"role": "assistant", "content": resp})
    return history

# Cenário 1: violões até R$1000
hist1 = run_scenario("Violões até 1000", [
    "Quais violões disponíveis até R$ 1000?"
])
save_conversation(hist1, "exemplo_1_violões_ate_1000.md")

# Cenário 2: preço Takamine GD20 (inclui promoção se houver)
hist2 = run_scenario("Preço Takamine GD20", [
    "Quanto custa o Takamine GD20?",
    "Tem promoção ativa nele? Qual o preço original e percentual?"
])
save_conversation(hist2, "exemplo_2_preco_takamine.md")

# Cenário 3: arrependimento com pedido real (pedido 5, email correto)
hist3 = run_scenario("Arrependimento pedido 5", [
    "Quero devolver o pedido 5, como proceder?",
    "Meu e-mail é leonardo.costa@cmail.com"
])
save_conversation(hist3, "exemplo_3_arrependimento_pedido5.md")

# Cenário 4: status/rastreio de pedido
hist4 = run_scenario("Status pedido 5", [
    "Qual o status do pedido 5?",
    "Meu e-mail é leonardo.costa@cmail.com"
])
save_conversation(hist4, "exemplo_4_status_pedido5.md")

# Cenário 5: fora de escopo
hist5 = run_scenario("Fora de escopo", [
    "Vocês vendem amplificador?"
])
save_conversation(hist5, "exemplo_5_fora_de_escopo.md")

print("\n=== Todos os exemplos gerados ===")