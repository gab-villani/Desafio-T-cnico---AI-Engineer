import unittest
from pathlib import Path
from streamlit.testing.v1 import AppTest

class TestUIDuplicate(unittest.TestCase):
    def test_no_duplicate_messages(self):
        # Resolve absolute path to UI script
        script_path = (Path(__file__).resolve().parents[2] / 'ui' / 'app.py').as_posix()
        at = AppTest.from_file(script_path).run()
        # Set language to pt-BR
        at.sidebar.selectbox('Idioma / Language').set_value('pt-BR')
        msgs = ["Oi", "Quanto custa o Takamine GD20?", "Qual o status do pedido 5?"]
        for m in msgs:
            at.chat_input.set_value(m)
            at.chat_input.post()
            at.run()
        # Get the history from session_state
        history = at.session_state.get('history', [])
        # Expect 6 entries: 3 user, 3 assistant
        self.assertEqual(len(history), 6, f"Histórico tem {len(history)} mensagens, esperado 6")
        user_msgs = [h for h in history if h['role'] == 'user']
        self.assertEqual(len(user_msgs), 3, f"Mensagens de usuário duplicadas: {len(user_msgs)}")
        for sent, recorded in zip(msgs, user_msgs):
            self.assertEqual(sent, recorded['content'])

if __name__ == '__main__':
    unittest.main()
