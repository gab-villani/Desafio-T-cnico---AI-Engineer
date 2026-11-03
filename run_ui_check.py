import json
from pathlib import Path
from streamlit.testing.v1 import AppTest

script_path = (Path(__file__).resolve().parent / 'ui' / 'app.py').as_posix()
app = AppTest.from_file(script_path).run()
# set language
lang_sel = app.sidebar.selectbox('Idioma / Language')
lang_sel.set_value('pt-BR')
msgs = ['Oi', 'Quanto custa o Takamine GD20?', 'Qual o status do pedido 5?']
for m in msgs:
    app.chat_input.set_value(m)
    app.chat_input.post()
# retrieve history
hist = app.session_state.get('history', [])
print('History length:', len(hist))
print('User msgs count:', len([h for h in hist if h['role']=='user']))
print('Assistant msgs count:', len([h for h in hist if h['role']=='assistant']))
print('User msgs:', [h['content'] for h in hist if h['role']=='user'])
