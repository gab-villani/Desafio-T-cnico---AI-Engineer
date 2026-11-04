from streamlit.testing.v1 import AppTest
import os, json, pathlib, tempfile, shutil
# create temporary chat dir
temp_dir = pathlib.Path(tempfile.mkdtemp())
chat_dir = temp_dir / 'chat_history'
chat_dir.mkdir()
os.environ['CHAT_HISTORY_DIR'] = str(chat_dir)
app = AppTest.from_file('ui/app.py').run()
print('exception:', app.exception)
# cleanup
shutil.rmtree(temp_dir)
