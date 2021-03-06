from bkr.inttest.server.selenium import SeleniumTestCase
from bkr.inttest import data_setup, with_transaction
from turbogears.database import session

class SystemNoteTests(SeleniumTestCase):

    @with_transaction
    def setUp(self):
        self.system = data_setup.create_system()
        self.owner = data_setup.create_user(password='password')
        self.system.owner = self.owner
        self.admin_group = data_setup.create_group()
        self.user = data_setup.create_user(password='password')
        self.admin_group.users.append(self.user)
        data_setup.add_group_to_system(self.system, self.admin_group, admin=True)
        self.nobody = data_setup.create_user(password='password')
        self.selenium = self.get_selenium()
        self.selenium.start()

    def tearDown(self):
        self.selenium.stop()

    def _test_add_note(self):
        sel = self.selenium
        sel.open('view/%s' % self.system.fqdn)
        sel.wait_for_page_to_load(30000)
        sel.click("link=Notes")
        note = data_setup.unique_name('note%s')
        try:
            sel.type("notes_note", note)
        except Exception, e:
            raise AssertionError(str(e))
        sel.click("//form[@name='notes']/div/a[normalize-space(text())='Add ( + )']")
        sel.wait_for_page_to_load(30000)
        note_text = sel.get_text("//pre[following-sibling::"
            "a[normalize-space(text())='(Delete this note)']]")
        self.assert_(note in note_text)
        return note

    def _test_has_note_delete_power(self, note):
        sel = self.selenium
        sel.click("link=Notes")
        sel.click("//a[preceding-sibling::"
            "pre[normalize-space(text())='%s']]" % note)
        # Test confirmation dialogue
        self.wait_and_try(lambda:
            self.failUnless(sel.is_text_present("Are you sure")))
        sel.click("//button[@type='button' and text()='Yes']")
        # Test that it is hidden
        self.wait_and_try(lambda: self.assert_(note not in \
            sel.get_text("//table[preceding-sibling::"
            "form[@name='notes']]")), 10)
        # Test that we have acreated a new element to toggle the notes
        self.wait_and_try(lambda: self.assert_(
            sel.is_text_present("Toggle deleted notes")), 10)
        sel.click("link=Toggle deleted notes")
        # Test that it reappears when toggled
        self.wait_and_try(lambda: self.assert_(note in \
            sel.get_text("//table[preceding-sibling::"
            "form[@name='notes']]")), 10)

        sel.open('view/%s' % self.system.fqdn)
        sel.wait_for_page_to_load(30000)
        sel.click("link=Notes")
        # Test existing deleted notes are hidden
        self.assert_(note not in \
            sel.get_text("//table[preceding-sibling::form[@name='notes']]"))
        # Test that it recognises deleted notes and gives us a toggle option
        self.assert_(sel.is_text_present("Toggle deleted notes"))

        # Add another note, delete it, and then toggle to make sure
        # both of the deleted notes display together, and are hidden together
        note_2 = self._test_add_note()
        sel.click("//a[normalize-space(text())='(Delete this note)']")
        self.wait_and_try(lambda:
            self.failUnless(sel.is_text_present("Are you sure")))
        sel.click("//button[@type='button' and text()='Yes']")
        self.wait_and_try(lambda: self.assert_(note not in \
            sel.get_text("//table[preceding-sibling::"
            "form[@name='notes']]")), 10)
        self.wait_and_try(lambda: self.assert_(note_2 not in \
            sel.get_text("//table[preceding-sibling::"
            "form[@name='notes']]")), 10)
        sel.click("link=Toggle deleted notes")
        self.wait_and_try(lambda: self.assert_(note in \
            sel.get_text("//table[preceding-sibling::"
            "form[@name='notes']]")), 10)
        self.wait_and_try(lambda: self.assert_(note_2 in \
            sel.get_text("//table[preceding-sibling::"
            "form[@name='notes']]")), 10)

    def test_notes_as_admin(self):
        self.login()
        note = self._test_add_note()
        self._test_has_note_delete_power(note)

    def test_notes_as_owner(self):
        self.login(user=self.owner.user_name, password='password')
        note = self._test_add_note()
        self._test_has_note_delete_power(note)

    def test_notes_as_group_admin(self):
        self.login(user=self.user.user_name, password='password')
        note = self._test_add_note()
        self._test_has_note_delete_power(note)

    def test_notes_as_nobody(self):
        # Add a note by authorised user
        sel = self.selenium
        self.login()
        self._test_add_note()

        # Test that we cannot add another as unprivileged user
        self.logout()
        self.login(user=self.nobody.user_name, password='password')
        try:
            self._test_add_note()
        except AssertionError:
            pass
        else:
            raise AssertionError('Unprivileged user was able to add note')

        #Try to delete the first added note
        sel.open('view/%s' % self.system.fqdn)
        sel.wait_for_page_to_load(30000)
        sel.click("link=Notes")
        try:
            sel.click("//a[normalize-space(text())='(Delete this note)']")
        except Exception:
            pass
        else:
            raise AssertionError('Unprivileged user was able to delete a note')

    def test_notes_logged_out(self):
        # Add a note by authorised user
        sel = self.selenium
        self.login()
        self._test_add_note()

        # Test that we cannot add another note without logging in
        self.logout()
        try:
            self._test_add_note()
        except AssertionError:
            pass
        else:
            raise AssertionError('User without credentials was able to add note')

        #Try to delete the first added note
        sel.open('view/%s' % self.system.fqdn)
        sel.wait_for_page_to_load(30000)
        sel.click("link=Notes")
        try:
            sel.click("//a[normalize-space(text())='(Delete this note)']")
        except Exception:
            pass
        else:
            raise AssertionError('User without credentials was able to delete a note')
