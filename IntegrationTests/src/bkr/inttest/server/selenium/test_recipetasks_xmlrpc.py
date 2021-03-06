
import datetime
from turbogears.database import session
from bkr.server.model import TaskStatus, TaskResult
from bkr.inttest import data_setup
from bkr.inttest.assertions import assert_datetime_within
from bkr.inttest.server.selenium import XmlRpcTestCase

class RecipeTasksXmlRpcTest(XmlRpcTestCase):

    def setUp(self):
        with session.begin():
            self.lc = data_setup.create_labcontroller()
            self.lc.user.password = u'logmein'
        self.server = self.get_server()

    def test_peer_roles(self):
        with session.begin():
            dt = data_setup.create_distro_tree()
            lc = data_setup.create_labcontroller()
            systems = [
                data_setup.create_system(fqdn=u'server.peer_roles', lab_controller=lc),
                data_setup.create_system(fqdn=u'clientone.peer_roles', lab_controller=lc),
                data_setup.create_system(fqdn=u'clienttwo.peer_roles', lab_controller=lc),
            ]
            job = data_setup.create_job_for_recipes([
                data_setup.create_recipe(distro_tree=dt, role=u'SERVERS'),
                data_setup.create_recipe(distro_tree=dt, role=u'CLIENTS'),
                data_setup.create_recipe(distro_tree=dt, role=u'CLIENTS'),
            ])
            job.recipesets[0].recipes[0].tasks[0].role = None
            # Normally you wouldn't use the same role name with different 
            # meaning at the task level, because that would just get 
            # confusing... but it is possible
            job.recipesets[0].recipes[1].tasks[0].role = u'SERVERS'
            job.recipesets[0].recipes[2].tasks[0].role = u'CLIENTTWO'
            for i in range(3):
                data_setup.mark_recipe_running(job.recipesets[0].recipes[i], system=systems[i])
        self.server.auth.login_password(self.lc.user.user_name, u'logmein')
        expected = {
            'SERVERS': ['server.peer_roles', 'clientone.peer_roles'],
            'CLIENTS': ['clientone.peer_roles', 'clienttwo.peer_roles'],
            'None': ['server.peer_roles'],
            'CLIENTTWO': ['clienttwo.peer_roles'],
        }
        for i in range(3):
            self.assertEquals(self.server.recipes.tasks.peer_roles(
                    job.recipesets[0].recipes[i].tasks[0].id),
                    expected)

    # https://bugzilla.redhat.com/show_bug.cgi?id=951283
    def test_role_fqdns_not_duplicated(self):
        with session.begin():
            dt = data_setup.create_distro_tree()
            lc = data_setup.create_labcontroller()
            systems = [
                data_setup.create_system(fqdn=u'server.bz951283', lab_controller=lc),
                data_setup.create_system(fqdn=u'client.bz951283', lab_controller=lc),
            ]
            job = data_setup.create_job_for_recipes([
                data_setup.create_recipe(distro_tree=dt, role=u'SERVERS'),
                data_setup.create_recipe(distro_tree=dt, role=u'CLIENTS'),
            ])
            # same roles on the tasks as on the recipes
            job.recipesets[0].recipes[0].tasks[0].role = u'SERVERS'
            job.recipesets[0].recipes[1].tasks[0].role = u'CLIENTS'
            for i in range(2):
                data_setup.mark_recipe_running(job.recipesets[0].recipes[i], system=systems[i])
        self.server.auth.login_password(self.lc.user.user_name, u'logmein')
        expected = {
            'SERVERS': ['server.bz951283'],
            'CLIENTS': ['client.bz951283'],
        }
        for i in range(2):
            self.assertEquals(self.server.recipes.tasks.peer_roles(
                    job.recipesets[0].recipes[i].tasks[0].id),
                    expected)

    # https://bugzilla.redhat.com/show_bug.cgi?id=952948
    def test_unknown_fqdns_dont_appear(self):
        # If we have a recipe where the FQDN is not known (for example 
        # a guest that hasn't finished installing yet), previously it would 
        # appear as the string 'None'. Now it's just not included.
        with session.begin():
            hostrecipe = data_setup.create_recipe(role=u'SERVERS')
            guestrecipe = data_setup.create_guestrecipe(host=hostrecipe,
                    role=u'CLIENTS')
            data_setup.create_job_for_recipes([hostrecipe, guestrecipe])
            system = data_setup.create_system(fqdn=u'host.bz952948')
            data_setup.mark_recipe_running(hostrecipe, system=system)
            data_setup.mark_recipe_waiting(guestrecipe)
            self.assertEquals(guestrecipe.resource.fqdn, None)
        self.server.auth.login_password(self.lc.user.user_name, u'logmein')
        self.assertEquals(self.server.recipes.tasks.peer_roles(
                hostrecipe.tasks[0].id),
                {'SERVERS': ['host.bz952948'],
                 'STANDALONE': ['host.bz952948'],
                 'CLIENTS': []})
        self.assertEquals(self.server.recipes.tasks.peer_roles(
                guestrecipe.tasks[0].id),
                {'SERVERS': ['host.bz952948'],
                 'STANDALONE': [],
                 'CLIENTS': []})
