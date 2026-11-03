import unittest, importlib.util, pathlib, sys

file_path = pathlib.Path('tests') / 'ui_duplicate_test.py'
spec = importlib.util.spec_from_file_location('ui_duplicate_test', str(file_path))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
loader = unittest.TestLoader()
suite = loader.loadTestsFromModule(module)
runner = unittest.TextTestRunner(verbosity=2)
result = runner.run(suite)
sys.exit(0 if result.wasSuccessful() else 1)
