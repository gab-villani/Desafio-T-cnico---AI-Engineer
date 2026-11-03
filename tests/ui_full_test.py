import os
import json
import unittest
from pathlib import Path
from unittest.mock import patch
from streamlit.testing.v1 import AppTest

class TestUIFull(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Ensure a clean chat_history directory for each run
        cls.chat_dir = Path('chat_history')
        cls.chat_dir.mkdir(exist_ok=True)
        # Remove any existing JSON files
        for f in cls.chat_dir.glob('*.json'):
            f.unlink()
        # Path to UI script
        cls.script_path = (Path(__file__).resolve().parents[1] / 'ui' / 'app.py').as_posix()

    def setUp(self):
        # Start a fresh AppTest instance for each test
        self.app = AppTest.from_file(self.script_path).run()

    def test_initial_ui_elements(self):
        # Verify chat_input and Nova conversa button exist
        self.assertTrue(hasattr(self.app, 'chat_input'))
        # Buttons are accessed via get('button')
        btns = self.app.get('button')
        labels = [b.label for b in btns]
        self.assertIn('Nova conversa', labels)

    def test_one_message_creates_single_pair(self):
        self.app.chat_input.set_value('Oi')
        self.app.chat_input.post()
        self.app.run()
        # History should have exactly 2 entries (user + assistant)
        hist = self.app.session_state.get('history', [])
        self.assertEqual(len(hist), 2)
        self.assertEqual(hist[0]['role'], 'user')
        self.assertEqual(hist[1]['role'], 'assistant')
        # JSON file should exist and contain same two messages
        files = list(self.chat_dir.glob('*.json'))
        self.assertEqual(len(files), 1)
        data = json.loads(files[0].read_text(encoding='utf-8'))
        self.assertEqual(data['messages'], hist)

    def test_three_messages_alternated(self):
        msgs = ['Oi', 'Quanto custa o Takamine GD20?', 'Qual o status do pedido 5?']
        for m in msgs:
            self.app.chat_input.set_value(m)
            self.app.chat_input.post()
            self.app.run()
        hist = self.app.session_state.get('history', [])
        self.assertEqual(len(hist), 6)
        # Verify alternating roles
        for i, entry in enumerate(hist):
            expected_role = 'user' if i % 2 == 0 else 'assistant'
            self.assertEqual(entry['role'], expected_role)

    def test_responder_receives_correct_history(self):
        # Use patch to capture the history argument passed to responder
        with patch('src.agent.responder') as mock_responder:
            mock_responder.side_effect = lambda msg, hist, idioma='pt-BR': f'Resposta a {msg}'
            # Send two messages first
            for m in ['Oi', "Qual é o preço do violão?"]:
                self.app.chat_input.set_value(m)
                self.app.chat_input.post()
                self.app.run()
            # On third message, capture call args
            self.app.chat_input.set_value('Qual o status do pedido 5?')
            self.app.chat_input.post()
            self.app.run()
            # Ensure responder called three times
            self.assertEqual(mock_responder.call_count, 3)
            # Third call args
            args, kwargs = mock_responder.call_args_list[2]
            # History passed should contain previous 2 pairs (4 entries)
            self.assertEqual(len(args[1]), 4)
            # Verify order: user, assistant, user, assistant
            self.assertEqual(args[1][0]['role'], 'user')
            self.assertEqual(args[1][1]['role'], 'assistant')
            self.assertEqual(args[1][2]['role'], 'user')
            self.assertEqual(args[1][3]['role'], 'assistant')

    def test_new_conversation_without_messages_creates_no_file(self):
        # Click Nova conversa without sending any message
        self.app.button('Nova conversa').click()
        self.app.run()
        files = list(self.chat_dir.glob('*.json'))
        self.assertEqual(len(files), 0)

if __name__ == '__main__':
    unittest.main()
