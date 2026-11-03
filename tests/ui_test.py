import os
import sys
from pathlib import Path
# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from streamlit.testing.v1 import AppTest

# Test from root directory
at_root = AppTest.from_file(os.path.abspath('ui/app.py')).run()
print('Root test history length:', len(at_root.session_state.get('history', [])))

# Change working dir to ui and test again
import os
import sys
os.chdir('ui')
# Ensure path includes parent
sys.path.insert(0, str(Path('..').resolve()))
at_ui = AppTest.from_file('app.py').run()
print('UI dir test history length:', len(at_ui.session_state.get('history', [])))
