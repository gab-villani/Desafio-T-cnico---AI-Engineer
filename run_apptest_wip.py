import os, json, uuid, shutil, tempfile
from pathlib import Path
import streamlit as st
from streamlit.testing.v1 import AppTest

# create temporary chat_history folder with 3 files
temp_dir = Path(tempfile.mkdtemp())
chat_dir = temp_dir / 'chat_history'
chat_dir.mkdir()
for i in range(3):
    cid = uuid.uuid4().hex
    data = {
        'id': cid,
        'created_at': '2026-01-01T00:00:00+00:00',
        'messages': [
            {'role': 'user', 'content': f'Hello {i}'},
            {'role': 'assistant', 'content': 'Hi'}
        ]
    }
    (chat_dir / f"{cid}.json").write_text(json.dumps(data), encoding='utf-8')

# set env var for app to use this folder (will be read if code uses CHAT_HISTORY_DIR env var, but current code uses CHAT_DIR constant; we need to monkeypatch? For now just run to see error line.)
os.environ['CHAT_HISTORY_DIR'] = str(chat_dir)

script_path = Path('ui/app.py').as_posix()
app = AppTest.from_file(script_path, default_timeout=60)
try:
    app.run()
    print('AppTest run finished')
except Exception as e:
    print('Exception:', e)
    import traceback, sys
    tb = traceback.format_exc()
    print(tb)
finally:
    shutil.rmtree(temp_dir)
