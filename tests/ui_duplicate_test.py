import json
import os
from pathlib import Path
from streamlit.testing.v1 import AppTest
import unittest

def send_messages(app_path, msgs, idioma="pt-BR"):
    # Resolve absolute path for the UI script relative to this test file
    script_path = (Path(__file__).resolve().parents[1] / app_path).as_posix()
    at = AppTest.from_file(script_path).run()
    # Set language selector if needed
    lang_select = at.sidebar.selectbox("Idioma / Language")
    lang_select.set_value(idioma)
    for m in msgs:
        at.chat_input.set_value(m)
        at.chat_input.post()
    # Return final session_state history
    return at.session_state.get('history', [])

class TestUIDuplicate(unittest.TestCase):
    def test_no_duplicate_messages(self):
        msgs = ["Oi", "Quanto custa o Takamine GD20?", "Qual o status do pedido 5?"]
        history = send_messages('ui/app.py', msgs)
        # Expect 6 entries (3 user, 3 assistant)
        self.assertEqual(len(history), 6, f"Histórico tem {len(history)} mensagens, esperado 6")
        user_msgs = [h for h in history if h['role'] == 'user']
        self.assertEqual(len(user_msgs), 3, f"Mensagens de usuário duplicadas: {len(user_msgs)}")
        for sent, recorded in zip(msgs, user_msgs):
            self.assertEqual(sent, recorded['content'])

if __name__ == '__main__':
    unittest.main()
