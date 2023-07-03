import unittest

import trytond.tests.test_tryton
from trytond.tests.test_tryton import ModuleTestCase


class ModuleTestCase(ModuleTestCase):
    'Module Test Case'

    module = 'note_authorizations'


def suite():
    suite = trytond.tests.test_tryton.suite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(
        ModuleTestCase))
    return suite
