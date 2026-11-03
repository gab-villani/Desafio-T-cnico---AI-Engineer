import os
import pathlib
import sys
import unittest
from streamlit.testing.v1 import AppTest


class TestUIPath(unittest.TestCase):
    def setUp(self):
        # Absolute path to the UI script
        self.script_abs = pathlib.Path('ui/app.py').resolve().as_posix()
        self.root_cwd = pathlib.Path('.').resolve()
        self.ui_cwd = self.root_cwd / 'ui'

    def _run_app_test(self, cwd):
        os.chdir(cwd)
        # Clean sys.path: keep only empty string and remove project root if present
        sys.path = [p for p in sys.path if p]
        # Insert only the ui directory (relative to cwd)
        ui_path = pathlib.Path('ui').resolve()
        sys.path.insert(0, str(ui_path))
        try:
            AppTest.from_file(self.script_abs).run()
            return True
        except Exception:
            return False

    def test_from_root_directory(self):
        ok = self._run_app_test(self.root_cwd)
        self.assertTrue(ok, "AppTest failed when run from project root")

    def test_from_ui_directory(self):
        ok = self._run_app_test(self.ui_cwd)
        self.assertTrue(ok, "AppTest failed when run from ui directory")


if __name__ == '__main__':
    unittest.main()