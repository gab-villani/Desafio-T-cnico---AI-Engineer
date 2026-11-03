import unittest
import uuid
import json
from datetime import datetime, timezone
from pathlib import Path
from streamlit.testing.v1 import AppTest

class TestUIPersistence(unittest.TestCase):
    def setUp(self):
        # create a temporary chat file in chat_history
        self.chat_dir = Path(__file__).resolve().parents[2] / 'chat_history'
        self.chat_dir.mkdir(exist_ok=True)
        self.chat_id = str(uuid.uuid4())
        self.chat_path = self.chat_dir / f"{self.chat_id}.json"
        data = {
            "id": self.chat_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "messages": []
        }
        self.chat_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
        # path to UI script
        self.script_path = (Path(__file__).resolve().parents[2] / 'ui' / 'app.py').as_posix()
        self.app = AppTest.from_file(self.script_path).run()
        # set language to pt-BR
        self.app.sidebar.selectbox('Idioma / Language').set_value('pt-BR')

    def test_load_chat_and_identity_prompt(self):
        # Load the saved chat via sidebar selectbox
        load_sel = self.app.sidebar.selectbox('Carregar conversa')
        # select the first (and only) option
        load_sel.set_value(load_sel.options[0])
        # after selection, run the app (rerun called internally)
        self.app.run()
        # verify history is empty (no messages)
        self.assertEqual(self.app.session_state.get('history'), [])
        # send a status request
        self.app.chat_input.set_value('Qual o status do pedido 5?')
        self.app.chat_input.post()
        self.app.run()
        # get history and check last assistant message contains request for email/phone
        hist = self.app.session_state.get('history', [])
        self.assertTrue(any('email' in msg['content'].lower() or 'telefone' in msg['content'].lower() for msg in hist if msg['role']=='assistant'))

    def test_new_conversation_clears(self):
        # send a first message
        self.app.chat_input.set_value('Oi')
        self.app.chat_input.post()
        self.app.run()
        # click new conversation button
        self.app.button('Nova conversa').click()
        self.app.run()
        # history should be empty after reset
        self.assertEqual(self.app.session_state.get('history'), [])

    def test_three_messages_no_duplicates(self):
        msgs = ['Oi', 'Quanto custa o Takamine GD20?', 'Qual o status do pedido 5?']
        for m in msgs:
            self.app.chat_input.set_value(m)
            self.app.chat_input.post()
            self.app.run()
        hist = self.app.session_state.get('history', [])
        self.assertEqual(len(hist), 6)  # 3 user + 3 assistant
        user_msgs = [h for h in hist if h['role']=='user']
        self.assertEqual(len(user_msgs), 3)
        for sent, recorded in zip(msgs, user_msgs):
            self.assertEqual(sent, recorded['content'])

if __name__ == '__main__':
    unittest.main()
