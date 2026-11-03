import traceback, sys
from pathlib import Path
from streamlit.testing.v1 import AppTest

script_path = (Path(__file__).parent / 'ui' / 'app.py').as_posix()
try:
    AppTest.from_file(script_path).run()
except Exception as e:
    print('Exception type:', type(e).__name__)
    print('Exception message:', e)
    traceback.print_exc()
