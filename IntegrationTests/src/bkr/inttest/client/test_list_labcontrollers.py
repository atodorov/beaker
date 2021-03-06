
import unittest
from turbogears.database import session
from bkr.inttest import data_setup, with_transaction
from bkr.inttest.client import run_client

class ListLabcontrollersTest(unittest.TestCase):

    @with_transaction
    def setUp(self):
        self.lc = data_setup.create_labcontroller()

    def test_list_lab_controller(self):
        out = run_client(['bkr', 'list-labcontrollers'])
        self.assert_(self.lc.fqdn in out, out)
