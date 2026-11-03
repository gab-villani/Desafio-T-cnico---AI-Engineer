import os
import pathlib
from streamlit.testing.v1 import AppTest

def run_test(cwd, script_path):
    os.chdir(cwd)
    print(f'Running from {cwd}')
    try:
        app = AppTest.from_file(script_path).run()
        print('Result: OK')
    except Exception as e:
        print('Result: EXCEPTION')
        print(type(e), e)

# From project root
run_test('.', pathlib.Path('ui/app.py').as_posix())
# From ui folder
run_test('ui', 'app.py')
