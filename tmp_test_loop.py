import unittest
import sys

suite = unittest.TestSuite()
for i in range(5):
    suite.addTest(unittest.defaultTestLoader.loadTestsFromName("tests.test_idioma.TestIdioma.test_acessorio_recusado_en"))

runner = unittest.TextTestRunner(verbosity=2)
result = runner.run(suite)
if not result.wasSuccessful():
    sys.exit(1)
