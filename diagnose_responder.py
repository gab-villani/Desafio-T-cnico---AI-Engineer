from src.agent import responder
for i in range(5):
    resp = responder("Vocês vendem amplificador?", [], idioma="en")
    print(f'Run {i+1}: {resp}')
