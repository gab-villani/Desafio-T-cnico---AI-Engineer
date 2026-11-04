import json
from pathlib import Path
from streamlit.testing.v1 import AppTest

script_path = (Path('ui') / 'app.py').as_posix()
app = AppTest.from_file(script_path).run()
msg = 'Price: R$ 100, was R$ 150?'
app.chat_input[0].set_value(msg)
app.run()
# get the rendered assistant message text (after markdown processing)
# In AppTest, rendered markdown is in app.find('st.markdown')
msgs = [w.text for w in app.find('st.markdown') if w.text]
print('Rendered assistant messages:')
for m in msgs:
    print(m)
