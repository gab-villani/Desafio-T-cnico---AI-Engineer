import os, json, uuid, tempfile, shutil
from pathlib import Path
import subprocess, sys, textwrap

# create temporary chat_history with 2 chats
temp_dir = Path(tempfile.mkdtemp())
chat_dir = temp_dir / 'chat_history'
chat_dir.mkdir()

# create two chat files
for i in range(2):
    cid = str(uuid.uuid4())
    data = {
        'id': cid,
        'created_at': '2026-11-03T00:00:00+00:00',
        'messages': [
            {'role': 'user', 'content': f'Hello {i}'},
            {'role': 'assistant', 'content': f'Hi {i}'}
        ]
    }
    (chat_dir / f'{cid}.json').write_text(json.dumps(data), encoding='utf-8')

# set environment variable to point to this dir (though code doesn't use it)
os.environ['CHAT_HISTORY_DIR'] = str(chat_dir)

# run AppTest via python - << script
script = textwrap.dedent('''
import os, json
from pathlib import Path
from streamlit.testing.v1 import AppTest

# point to our temporary chat_history by symlinking expected location
proj_root = Path(__file__).resolve().parents[0]
expected = proj_root / 'chat_history'
if expected.exists():
    # rename if exists
    backup = expected.with_name('chat_history_backup')
    expected.rename(backup)
expected.symlink_to(os.environ['CHAT_HISTORY_DIR'])

app = AppTest.from_file('ui/app.py').run()
# send first message
app.chat_input[0].set_value('How are you?')
app.run()
print('Files after 1st msg:', list(expected.iterdir()))
# list selector options
selector = app.sidebar.selectbox[0]
print('selector options:', selector.options)
# second run (simulate page reload)
app2 = AppTest.from_file('ui/app.py').run()
selector2 = app2.sidebar.selectbox[0]
print('selector options after reload:', selector2.options)
''')

# write script to temp file
script_path = temp_dir / 'run_app_test.py'
script_path.write_text(script)

# run using the venv python
exe = Path('C:/Users/gabim/Documents/Desafio Técnico - AI Engineer/.venv/Scripts/python.exe')
result = subprocess.run([str(exe), str(script_path)], capture_output=True, text=True, env=os.environ)
print('STDOUT:', result.stdout)
print('STDERR:', result.stderr)

# cleanup
shutil.rmtree(temp_dir)
''