from src.agent import responder
for i in range(5):
    resp = responder("Qual o status do pedido 5?", [], idioma="en")
    print(i, resp)
