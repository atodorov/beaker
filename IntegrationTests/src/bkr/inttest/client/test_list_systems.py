
import unittest
from turbogears.database import session
from bkr.inttest import data_setup
from bkr.inttest.client import run_client, ClientError
from bkr.server.model import System, Key, Key_Value_String
import datetime

class ListSystemsTest(unittest.TestCase):

    def check_systems(self, present=None, absent=None):
        for system in present:
            self.assert_(system.fqdn in self.returned_systems)

        for system in absent:
            self.assert_(system.fqdn not in self.returned_systems)

    def test_list_all_systems(self):
        with session.begin():
            data_setup.create_system() # so that we have at least one
        out = run_client(['bkr', 'list-systems'])
        self.assertEqual(len(out.splitlines()), System.query.count())

    # https://bugzilla.redhat.com/show_bug.cgi?id=690063
    def test_xml_filter(self):
        with session.begin():
            module_key = Key.by_name(u'MODULE')
            with_module = data_setup.create_system()
            with_module.key_values_string.extend([
                    Key_Value_String(module_key, u'cciss'),
                    Key_Value_String(module_key, u'kvm')])
            without_module = data_setup.create_system()
        out = run_client(['bkr', 'list-systems',
                '--xml-filter', '<key_value key="MODULE" />'])
        returned_systems = out.splitlines()
        self.assert_(with_module.fqdn in returned_systems, returned_systems)
        self.assert_(without_module.fqdn not in returned_systems,
                returned_systems)

    #https://bugzilla.redhat.com/show_bug.cgi?id=949777
    def test_inventory_date_search(self):

        # date times
        today = datetime.date.today()
        time_now = datetime.datetime.combine(today, datetime.time(0, 0))
        time_delta1 = datetime.datetime.combine(today, datetime.time(0, 30))
        time_tomorrow = time_now + datetime.timedelta(days=1)

        # today date
        date_today = time_now.date().isoformat()
        date_tomorrow = time_tomorrow.date().isoformat()

        with session.begin():
            not_inv = data_setup.create_system()

            inv1 = data_setup.create_system()
            inv1.date_lastcheckin = time_now

            inv2 = data_setup.create_system()
            inv2.date_lastcheckin = time_delta1

            inv3 = data_setup.create_system()
            inv3.date_lastcheckin = time_tomorrow

        # uninventoried
        out = run_client(['bkr', 'list-systems',
                          '--xml-filter',
                          '<system>'
                          '<last_inventoried op="=" value="" />'
                          '</system>'])

        self.returned_systems = out.splitlines()
        self.check_systems(present=[not_inv], absent=[inv1, inv2, inv3])

        # Return all inventoried systems
        out = run_client(['bkr', 'list-systems',
                          '--xml-filter',
                          '<system>'
                          '<last_inventoried op="!=" value="" />'
                          '</system>'])

        self.returned_systems = out.splitlines()
        self.check_systems(present=[inv1, inv2, inv2], absent=[not_inv])

        # inventoried on a certain date
        out = run_client(['bkr', 'list-systems',
                          '--xml-filter',
                          '<system>'
                          '<last_inventoried op="=" value="%s" />'
                          '</system>'% date_today])

        self.returned_systems = out.splitlines()
        self.check_systems(present=[inv1, inv2], absent=[not_inv, inv3])

        # not inventoried on a certain date
        out = run_client(['bkr', 'list-systems',
                          '--xml-filter',
                          '<system>'
                          '<last_inventoried op="!=" value="%s" />'
                          '</system>' % date_today])

        self.returned_systems = out.splitlines()
        self.check_systems(present=[inv3], absent=[not_inv, inv1, inv2])


        # Before a certain date
        out = run_client(['bkr', 'list-systems',
                          '--xml-filter',
                          '<system>'
                          '<last_inventoried op="&lt;" value="%s" />'
                          '</system>' % date_tomorrow])

        self.returned_systems = out.splitlines()
        self.check_systems(present=[inv1, inv2], absent=[not_inv, inv3])

        # On or before a certain date
        out = run_client(['bkr', 'list-systems',
                          '--xml-filter',
                          '<system>'
                          '<last_inventoried op="&lt;=" value="%s" />'
                          '</system>' % date_tomorrow])

        self.returned_systems = out.splitlines()
        self.check_systems(present=[inv1, inv2, inv3], absent=[not_inv])

        # Only date is valid, not date time
        try:
            out = run_client(['bkr', 'list-systems',
                              '--xml-filter',
                              '<system>'
                              '<last_inventoried op="&gt;" value="%s 00:00:00" />'
                              '</system>' % today])
            self.fail('Must Fail or Die')
        except ClientError, e:
            self.assertEqual(e.status, 1)
            self.assert_('Invalid date format' in e.stderr_output,
                    e.stderr_output)

    #https://bugzilla.redhat.com/show_bug.cgi?id=955868
    def test_added_date_search(self):

        # date times
        today = datetime.date.today()
        time_now = datetime.datetime.combine(today, datetime.time(0, 0))
        time_delta1 = datetime.datetime.combine(today, datetime.time(0, 30))
        time_tomorrow = time_now + datetime.timedelta(days=1)
        time_tomorrow = time_now + datetime.timedelta(days=2)

        # dates
        date_today = time_now.date().isoformat()
        date_tomorrow = time_tomorrow.date().isoformat()


        with session.begin():
            sys_today1 = data_setup.create_system(arch=u'i386', shared=True,
                                          date_added=time_now)
            sys_today2 = data_setup.create_system(arch=u'i386', shared=True,
                                          date_added=time_delta1)
            sys_tomorrow = data_setup.create_system(arch=u'i386', shared=True,
                                            date_added=time_tomorrow)

        # on a date
        out = run_client(['bkr', 'list-systems',
                          '--xml-filter',
                          '<system>'
                          '<added op="=" value="%s" />'
                          '</system>' % date_today])

        returned_systems = out.splitlines()
        self.assert_(sys_today1.fqdn in returned_systems)
        self.assert_(sys_today2.fqdn in returned_systems)
        self.assert_(sys_tomorrow.fqdn not in returned_systems)

        # on a datetime
        try:
            out = run_client(['bkr', 'list-systems',
                              '--xml-filter',
                              '<system>'
                              '<added op="=" value="%s" />'
                              '</system>' % time_now])
            self.fail('Must Fail or Die')
        except ClientError,e:
            self.assertEquals(e.status, 1)
            self.assert_('Invalid date format' in e.stderr_output, e.stderr_output)

        # date as  " "
        try:
            out = run_client(['bkr', 'list-systems',
                              '--xml-filter',
                              '<system>'
                              '<added op="=" value=" " />'
                              '</system>'])
            self.fail('Must Fail or die')
        except ClientError,e:
            self.assertEquals(e.status, 1)
            self.assert_('Invalid date format' in e.stderr_output, e.stderr_output)
