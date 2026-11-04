import time, os
from pathlib import Path
from streamlit.testing.v1 import AppTest

script_path = Path('ui/app.py').as_posix()

def run_test(timeout):
    start = time.time()
    app = AppTest.from_file(script_path).run(timeout=timeout)
    # send message
    app.chat_input[0].set_value('Oi')
    app.run(timeout=timeout)
    # change language
    app.sidebar.radio[0].set_value(('English (en)', 'en'))
    app.run(timeout=timeout)
    elapsed = time.time() - start
    return elapsed

for branch, to in [('green', 60), ('wip', 60)]:
    print(f'Running on branch {branch} with timeout {to}')
    elapsed = run_test(to)
    print(f'Elapsed: {elapsed:.2f}s')
