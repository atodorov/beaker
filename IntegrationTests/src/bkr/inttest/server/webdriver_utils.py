
from __future__ import absolute_import

import json
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium import webdriver
from bkr.inttest import data_setup, get_server_base

def delete_and_confirm(browser, ancestor_xpath, delete_text='Delete'):
    browser.find_element_by_xpath("%s//a[normalize-space(text())='%s']" % (ancestor_xpath, delete_text)).click()
    browser.find_element_by_xpath("//button[@type='button' and text()='Yes']").click()

def logout(browser):
    browser.get(get_server_base())
    browser.find_element_by_link_text('Logout').click()

def login(browser, user=None, password=None):
    if user is None and password is None:
        user = data_setup.ADMIN_USER
        password = data_setup.ADMIN_PASSWORD
    browser.get(get_server_base())
    browser.find_element_by_link_text('Login').click()
    browser.find_element_by_name('user_name').click()
    browser.find_element_by_name('user_name').send_keys(user)
    browser.find_element_by_name('password').click()
    browser.find_element_by_name('password').send_keys(password)
    browser.find_element_by_name('login').click()

def logout(browser):
    browser.get(get_server_base())
    browser.find_element_by_link_text('Logout').click()

def is_text_present(browser, text):
    return bool(browser.find_elements_by_xpath(
            '//*[contains(text(), "%s")]' % text.replace('"', r'\"')))

def is_activity_row_present(b, via=u'testdata', object_=None, property_=None,
        action=None, old_value=None, new_value=None):
    row_count = len(b.find_elements_by_xpath('//table[@id="widget"]/tbody/tr'))
    for row in range(1, row_count + 1):
        if via and via != b.find_element_by_xpath('//table[@id="widget"]/tbody/tr[%d]/td[2]' % row).text:
            continue
        if object_ and object_ != b.find_element_by_xpath('//table[@id="widget"]/tbody/tr[%d]/td[4]' % row).text:
            continue
        if property_ and property_ != b.find_element_by_xpath('//table[@id="widget"]/tbody/tr[%d]/td[5]' % row).text:
            continue
        if action and action != b.find_element_by_xpath('//table[@id="widget"]/tbody/tr[%d]/td[6]' % row).text:
            continue
        if old_value and old_value != b.find_element_by_xpath('//table[@id="widget"]/tbody/tr[%d]/td[7]' % row).text:
            continue
        if new_value and new_value != b.find_element_by_xpath('//table[@id="widget"]/tbody/tr[%d]/td[8]' % row).text:
            continue
        return True
    return False

def search_for_system(browser, system):
    browser.find_element_by_link_text('Toggle Search').click()
    Select(browser.find_element_by_name('systemsearch-0.table'))\
            .select_by_visible_text('System/Name')
    Select(browser.find_element_by_name('systemsearch-0.operation'))\
            .select_by_visible_text('is')
    browser.find_element_by_name('systemsearch-0.value').send_keys(system.fqdn)
    browser.find_element_by_name('systemsearch').submit()

def wait_for_animation(browser, selector):
    """
    Waits until jQuery animations have finished for the given jQuery selector.
    """
    WebDriverWait(browser, 10).until(lambda browser: browser.execute_script(
            'return jQuery(%s).is(":animated")' % json.dumps(selector))
            == False)
