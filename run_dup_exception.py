import traceback, sys
from pathlib import Path
from streamlit.testing.v1 import AppTest
from streamlit.errors import StreamlitDuplicateElementId

script_path = (Path(__file__).parent / 'ui' / 'app.py').as_posix()
try:
    AppTest.from_file(script_path).run()
except StreamlitDuplicateElementId as e:
    print('StreamlitDuplicateElementId caught:')
    print(e)
    traceback.print_exc()
except Exception as e:
    print('Other exception type:', type(e).__name__)
    print(e)
    traceback.print_exc()
