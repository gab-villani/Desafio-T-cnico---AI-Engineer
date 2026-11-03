import unittest, traceback, sys
from tests import ui_persistence_test

suite = unittest.TestLoader().loadTestsFromTestCase(ui_persistence_test.TestUIPersistence)
runner = unittest.TextTestRunner(verbosity=2)
result = runner.run(suite)
if not result.wasSuccessful():
    print('FAILURES:')
    for case, tb in result.failures:
        print('FAIL:', case)
        traceback.print_exception(type(tb), tb, tb.__traceback__)
    for case, tb in result.errors:
        print('ERROR:', case)
        traceback.print_exception(type(tb), tb, tb.__traceback__)
    sys.exit(1)
else:
    print('All passed')
    sys.exit(0)
