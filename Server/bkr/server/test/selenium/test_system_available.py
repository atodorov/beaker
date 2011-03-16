import bkr.server.test.selenium
from bkr.server.test import data_setup
import unittest, time, re, os
from turbogears.database import session

class SystemAvailable(bkr.server.test.selenium.SeleniumTestCase):
    
    @classmethod
    def setupClass(cls):
        cls.selenium = cls.get_selenium()
        cls.password = 'password'
        cls.user_1 = data_setup.create_user(password=cls.password)
        cls.user_2 = data_setup.create_user(password=cls.password)
        cls.system = data_setup.create_system(shared=True)
        lc = data_setup.create_labcontroller()
        cls.system.lab_controller = lc
        session.flush()
        cls.selenium.start()
        try:
            cls.login(user=cls.user_1,password=cls.password)
        except Exception:
            pass

    def test_avilable_with_no_loan(self):
        sel = self.selenium
        sel.open('available')
        sel.wait_for_page_to_load('3000')
        sel.select("systemsearch_0_table", "label=System/Name")
        sel.select("systemsearch_0_operation", "label=is")
        sel.type("systemsearch_0_value", "%s" % self.system.fqdn)
        sel.click("Search")
        sel.wait_for_page_to_load('3000')
        self.failUnless(sel.is_text_present("%s" % self.system.fqdn))
        sel.open("view/%s" % self.system.fqdn)
        sel.click("link=Provision")
        self.failUnless(sel.is_text_present("Schedule provision"))

    def test_avilable_with_loan(self):
        sel = self.selenium
        self.system.loaned=self.user_2
        session.flush()
        sel.open('available')
        sel.wait_for_page_to_load('3000')
        sel.select("systemsearch_0_table", "label=System/Name")
        sel.select("systemsearch_0_operation", "label=is")
        sel.type("systemsearch_0_value", "%s" % self.system.fqdn)
        sel.click("Search")
        sel.wait_for_page_to_load('3000')
        self.failUnless(sel.is_text_present("%s" % self.system.fqdn))
        sel.open("view/%s" % self.system.fqdn)
        sel.click("link=Provision")
        self.failUnless(sel.is_text_present("Schedule provision"))

    @classmethod
    def teardownClass(cls):
        cls.selenium.stop()

