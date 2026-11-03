import sys, os, pathlib
from streamlit.testing.v1 import AppTest

def run_test(cwd):
    # Change cwd
    os.chdir(cwd)
    # Clean sys.path: keep only empty string (current dir) and remove project root if present
    sys.path = [p for p in sys.path if p]
    # Insert only the ui directory (relative to cwd)
    ui_path = pathlib.Path('ui').resolve()
    sys.path.insert(0, str(ui_path))
    print(f'--- Running from cwd="{cwd}" ---')
    try:
        script_abs = pathlib.Path('ui/app.py').resolve().as_posix()
        AppTest.from_file(script_abs).run()
        print('Result: OK')
    except Exception as e:
        print('Result: EXCEPTION')
        print(type(e), e)

# Run from project root
run_test('.')
# Run from ui directory
run_test('ui')
