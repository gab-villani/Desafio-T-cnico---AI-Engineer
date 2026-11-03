import json
import pathlib
import shutil
import unittest
from pathlib import Path
from streamlit.testing.v1 import AppTest
from streamlit.errors import StreamlitDuplicateElementId

class TestDuplicateChatButtons(unittest.TestCase):
    def setUp(self):
        # Ensure chat_history is clean
        self.chat_dir = Path('chat_history')
        self.chat_dir.mkdir(exist_ok=True)
        # remove any existing files
        for f in self.chat_dir.glob('*.json'):
            f.unlink()
        # create two files with same id and same first message
        dup_id = 'dup-id-1234'
        msg = 'Mensagem teste'
        date = '2026-11-02T12:00:00+00:00'
        for i in range(2):
            data = {
                'id': dup_id,
                'created_at': date,
                'messages': [{'role': 'user', 'content': msg}]
            }
            (self.chat_dir / f'dup_{i}.json').write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
        self.script_path = (Path(__file__).parent.parent / 'ui' / 'app.py').as_posix()

    def test_no_duplicate_element_error(self):
        try:
            AppTest.from_file(self.script_path).run()
        except StreamlitDuplicateElementId as e:
            self.fail(f'StreamlitDuplicateElementId raised: {e}')
        except Exception as e:
            # any other exception also fails the test
            self.fail(f'Unexpected exception: {e}')
        # if no exception, test passes

if __name__ == '__main__':
    unittest.main()
