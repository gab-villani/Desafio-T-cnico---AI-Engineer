import sys
from pathlib import Path
from streamlit.testing.v1 import AppTest

script_path = (Path(__file__).parent / 'ui' / 'app.py').as_posix()
try:
    app = AppTest.from_file(script_path).run()
    print('AppTest ran without exception')
except Exception as e:
    print('Exception:', e)
