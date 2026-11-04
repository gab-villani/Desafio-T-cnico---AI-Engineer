import os, json, pathlib, tempfile, shutil, uuid, datetime
from streamlit.testing.v1 import AppTest

# create temporary chat dir
temp_dir = pathlib.Path(tempfile.mkdtemp())
chat_dir = temp_dir / 'chat_history'
chat_dir.mkdir()
# create two dummy chats
for i in range(2):
    cid = uuid.uuid4().hex
    data = {
        'id': cid,
        'created_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'messages': [
            {'role': 'user', 'content': f'Hello {i}'},
            {'role': 'assistant', 'content': f'Hi {i}'},
        ]
    }
    (chat_dir / f'{cid}.json').write_text(json.dumps(data), encoding='utf-8')

os.environ['CHAT_HISTORY_DIR'] = str(chat_dir)
app = AppTest.from_file('ui/app.py').run()
# send a message
app.chat_input[0].set_value('Test message')
app.run()
print('exception:', app.exception)
print('chat_id after generation:', app.session_state['chat_id'])
shutil.rmtree(temp_dir)
