import sys
sys.path.append('.')
from src.agent import responder
for i in range(5):
    resp = responder("Vocês vendem amplificador?", [], idioma="en")
    print(f"---Response {i+1}---")
    print(resp)
    print("---END---")
