from pathlib import Path
from streamlit.testing.v1 import AppTest

def send_messages(app_path, msgs, idioma='pt-BR'):
    script_path = (Path(__file__).resolve().parents[1] / app_path).as_posix()
    at = AppTest.from_file(script_path).run()
    at.sidebar.selectbox('Idioma / Language').set_value(idioma)
    for m in msgs:
        at.chat_input.set_value(m)
        at.chat_input.post()
    return at.session_state.get('history', [])

if __name__ == '__main__':
    msgs = ['Oi', 'Quanto custa o Takamine GD20?', 'Qual o status do pedido 5?']
    hist = send_messages('ui/app.py', msgs)
    print('len', len(hist))
    print('hist', hist)
