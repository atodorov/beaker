from turbogears.database import session
from bkr.server.model import SystemStatus
from bkr.inttest.server.selenium import SeleniumTestCase, WebDriverTestCase
from bkr.inttest import data_setup, with_transaction, get_server_base
from bkr.inttest.server.webdriver_utils import login, is_text_present


class SystemReturnTestWD(WebDriverTestCase):

    def setUp(self):
        with session.begin():
            self.recipe = data_setup.create_recipe()
            data_setup.create_job_for_recipes([self.recipe])
            data_setup.mark_recipe_running(self.recipe)
        self.browser = self.get_browser()

    def tearDown(self):
        self.browser.quit()

    def test_cannot_return_running_recipe(self):
        b = self.browser
        system = self.recipe.resource.system
        login(b)
        b.get(get_server_base() + 'view/%s' % system.fqdn)
        b.find_element_by_link_text('(Return)').click()
        self.assertEquals(b.find_element_by_css_selector('.flash').text,
            "Failed to return %s: u'Currently running R:%s'" % (system.fqdn, self.recipe.id))


class SystemReturnTest(SeleniumTestCase):

    @with_transaction
    def setUp(self):
        self.user = data_setup.create_user(password='password')
        self.system = data_setup.create_system(shared=True,
                status=SystemStatus.manual)
        self.lc  = data_setup.create_labcontroller(fqdn='remove_me')
        self.system.lab_controller = self.lc
        self.selenium = self.get_selenium()
        self.selenium.start()

    def test_cant_return_sneakily(self):
        self.login() #login as admin
        sel = self.selenium
        sel.open('view/%s' % self.system.fqdn)
        sel.wait_for_page_to_load(30000)
        sel.click('link=(Take)')
        sel.wait_for_page_to_load(30000)

        self.logout()
        self.login(user=self.user.user_name, password='password')
        sel.open('view/%s' % self.system.fqdn)
        sel.wait_for_page_to_load(30000)

        # Test for https://bugzilla.redhat.com/show_bug.cgi?id=747328
        sel.open('user_change?id=%s' % self.system.id)
        sel.wait_for_page_to_load("30000")
        self.assert_('You were unable to change the user for %s' % self.system.fqdn in sel.get_text('//body'))


    def test_return_with_no_lc(self):
        sel = self.selenium
        self.login(user=self.user.user_name, password='password')
        sel.open('view/%s' % self.system.fqdn)
        sel.wait_for_page_to_load('30000')
        sel.click('link=(Take)')
        sel.wait_for_page_to_load('30000')

        # Let's remove the LC
        self.logout()
        self.login()
        sel.open("labcontrollers/")
        sel.wait_for_page_to_load('30000')
        sel.click("//a[@onclick=\"has_watchdog('%s')\"]" % self.lc.id)
        sel.wait_for_page_to_load("30000")

        self.logout()
        self.login(user=self.user.user_name, password='password')
        sel.open('view/%s' % self.system.fqdn)
        sel.wait_for_page_to_load('30000')
        sel.click('link=(Return)')
        sel.wait_for_page_to_load('30000')
        text = sel.get_text('//body')
        self.assert_('Returned %s' % self.system.fqdn in text)


