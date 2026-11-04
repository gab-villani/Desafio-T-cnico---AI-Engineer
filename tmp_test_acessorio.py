import sys
sys.path.append('.')
from src.agent import responder
for i in range(5):
    resp = responder('Voc\u00ea vendem amplificador?', [], idioma='en')
    print(f'--- Run {i+1} ---')
    print(resp)
    print()
