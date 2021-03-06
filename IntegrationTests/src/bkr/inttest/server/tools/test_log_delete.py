import unittest, datetime, os, errno, shutil
from nose.plugins.skip import SkipTest
import tempfile
import subprocess
import sys
from sqlalchemy.orm.exc import NoResultFound
from bkr.server.model import LogRecipe, TaskBase, Job, Recipe, RenderedKickstart
from bkr.inttest import data_setup, with_transaction, Process
from bkr.server.tools import log_delete
from turbogears.database import session

def setUpModule():
    try:
        import kerberos
    except ImportError:
        raise SkipTest('kerberos module not available, but log-delete requires it')

    try:
        import requests_kerberos
    except ImportError:
        raise SkipTest('requests_kerberos module not available, but log-delete requires it')

    # It makes our tests simpler here if they only need to worry about deleting 
    # logs which they themselves have created, rather than ones which might have 
    # been left behind from earlier tests in the run.
    for job, _ in Job.expired_logs():
        job.delete()

class LogDelete(unittest.TestCase):

    @with_transaction
    def setUp(self):
        self.password=u'p'
        self.user = data_setup.create_user(password=self.password)
        self.job_to_delete = data_setup.create_completed_job() #default tag, scratch
        self.job_to_delete.owner = self.user

    def check_dir_not_there(self, dir):
        if os.path.exists(dir):
            raise AssertionError('%s should have been deleted' % dir)

    def make_dir(self, dir):
        try:
            os.makedirs(dir)
        except OSError, e:
            if e.errno == errno.EEXIST:
                pass
            else:
                raise

    def _assert_logs_not_in_db(self, job):
        for rs in job.recipesets:
            for r in rs.recipes:
                self.assert_(r.logs == [])
                for rt in r.tasks:
                    self.assert_(rt.logs == [])
                    for rtr in rt.results:
                        self.assert_(rtr.logs == [])

    def test_limit(self):
        limit = 10

        def _create_jobs():
            with session.begin():
                for i in range(limit + 1):
                    job_to_delete = data_setup.create_completed_job(
                            start_time=datetime.datetime.utcnow() - datetime.timedelta(days=60),
                            finish_time=datetime.datetime.utcnow() - datetime.timedelta(days=31))
                    job_to_delete.recipesets[0].recipes[0].logs.append(LogRecipe(filename=u'test.log'))

        def _get_output(f):
            tmp_file =  tempfile.TemporaryFile()
            sys_std_out = sys.stdout
            sys.stdout = tmp_file
            f()
            tmp_file.seek(0)
            log_delete_output = tmp_file.read()
            tmp_file.close()
            sys.stdout = sys_std_out
            return log_delete_output

        # Test with limit
        _create_jobs()
        with_limit = _get_output(lambda:
            log_delete.log_delete(dry=True, print_logs=True, limit=10))
        self.assert_(len(with_limit.splitlines()) == limit)

        # Test no limit set
        _create_jobs()
        no_limit = _get_output(lambda:
            log_delete.log_delete(dry=True, print_logs=True))
        self.assert_(len(no_limit.splitlines()) > limit)

    def test_log_not_delete(self):
        # Job that is not within it's expiry time
        with session.begin():
            job_not_delete = data_setup.create_completed_job(
                    start_time=datetime.datetime.utcnow() - datetime.timedelta(days=60),
                    finish_time=datetime.datetime.utcnow() - datetime.timedelta(days=29))
        job_not_delete.recipesets[0].recipes[0].logs.append(LogRecipe(filename=u'test.log'))
        r_not_delete = job_not_delete.recipesets[0].recipes[0]
        dir_not_delete = os.path.join(r_not_delete.logspath ,r_not_delete.filepath)
        self.make_dir(dir_not_delete)
        ft = open(os.path.join(dir_not_delete,'test.log'), 'w')
        ft.close()
        session.flush()
        log_delete.log_delete()
        self.assertRaises(AssertionError, self._assert_logs_not_in_db, self.job_to_delete)
        try:
            self.check_dir_not_there(dir_not_delete)
            raise Exception('%s was deleted when it shold not have been' % dir_not_delete)
        except AssertionError:
            pass

    def test_log_delete_expired(self):
        with session.begin():
            job_to_delete = data_setup.create_completed_job(
                    start_time=datetime.datetime.utcnow() - datetime.timedelta(days=60),
                    finish_time=datetime.datetime.utcnow() - datetime.timedelta(days=31))
            self.job_to_delete.owner = self.user
            job_to_delete.recipesets[0].recipes[0].logs.append(LogRecipe(filename=u'test.log'))
            r_delete = job_to_delete.recipesets[0].recipes[0]
            dir_delete = os.path.join(r_delete.logspath ,r_delete.filepath)

        self.make_dir(dir_delete)
        fd = open(os.path.join(dir_delete,'test.log'), 'w')
        fd.close()
        log_delete.log_delete()
        self._assert_logs_not_in_db(Job.by_id(job_to_delete.id))
        self.check_dir_not_there(dir_delete)

    def test_log_delete_to_delete(self):
        with session.begin():
            self.job_to_delete.to_delete = datetime.datetime.utcnow()
            self.job_to_delete.recipesets[0].recipes[0].logs.append(LogRecipe(filename=u'test.log'))
        r_ = self.job_to_delete.recipesets[0].recipes[0]
        dir = os.path.join(r_.logspath ,r_.filepath)
        self.make_dir(dir)
        f = open(os.path.join(dir,'test.log'), 'w')
        f.close()
        log_delete.log_delete()
        self._assert_logs_not_in_db(Job.by_id(self.job_to_delete.id))
        self.check_dir_not_there(dir)

    def test_rendered_kickstart_is_deleted(self):
        with session.begin():
            self.job_to_delete.to_delete = datetime.datetime.utcnow()
            recipe = self.job_to_delete.recipesets[0].recipes[0]
            ks = RenderedKickstart(kickstart=u'This is not a real kickstart.')
            recipe.rendered_kickstart = ks
        log_delete.log_delete()
        with session.begin():
            self.assertEqual(Recipe.by_id(recipe.id).rendered_kickstart, None)
            self.assertRaises(NoResultFound, RenderedKickstart.by_id, ks.id)

class RemoteLogDeletionTest(unittest.TestCase):

    def setUp(self):
        self.logs_dir = tempfile.mkdtemp(prefix='beaker-test-log-delete')
        self.archive_server = Process('archive_server.py',
                args=['python', os.path.join(os.path.dirname(__file__), '..', '..', 'archive_server.py'),
                      '--base', self.logs_dir],
                listen_port=19998)
        self.archive_server.start()

    def tearDown(self):
        self.archive_server.stop()
        shutil.rmtree(self.logs_dir, ignore_errors=True)

    def create_deleted_job_with_log(self, path, filename):
        with session.begin():
            job = data_setup.create_completed_job()
            job.to_delete = datetime.datetime.utcnow()
            session.flush()
            job.recipesets[0].recipes[0].log_server = u'localhost:19998'
            job.recipesets[0].recipes[0].logs[:] = [
                    LogRecipe(server=u'http://localhost:19998/%s' % path, filename=filename)]
            for rt in job.recipesets[0].recipes[0].tasks:
                rt.logs[:] = []

    def test_deletion(self):
        os.mkdir(os.path.join(self.logs_dir, 'recipe'))
        open(os.path.join(self.logs_dir, 'recipe', 'dummy.txt'), 'w').write('dummy')
        os.mkdir(os.path.join(self.logs_dir, 'dont_tase_me_bro'))
        self.create_deleted_job_with_log(u'recipe/', u'dummy.txt')
        self.assertEquals(log_delete.log_delete(), 0) # exit status
        self.assert_(not os.path.exists(os.path.join(self.logs_dir, 'recipe')))
        self.assert_(os.path.exists(os.path.join(self.logs_dir, 'dont_tase_me_bro')))

    def test_301_redirect(self):
        os.mkdir(os.path.join(self.logs_dir, 'recipe'))
        open(os.path.join(self.logs_dir, 'recipe', 'dummy.txt'), 'w').write('dummy')
        self.create_deleted_job_with_log(u'redirect/301/recipe/', u'dummy.txt')
        self.assertEquals(log_delete.log_delete(), 0) # exit status
        self.assert_(not os.path.exists(os.path.join(self.logs_dir, 'recipe')))

    def test_302_redirect(self):
        os.mkdir(os.path.join(self.logs_dir, 'recipe'))
        open(os.path.join(self.logs_dir, 'recipe', 'dummy.txt'), 'w').write('dummy')
        self.create_deleted_job_with_log(u'redirect/302/recipe/', u'dummy.txt')
        self.assertEquals(log_delete.log_delete(), 0) # exit status
        self.assert_(not os.path.exists(os.path.join(self.logs_dir, 'recipe')))

    def test_404(self):
        self.create_deleted_job_with_log(u'notexist/', u'dummy.txt')
        self.assertEquals(log_delete.log_delete(), 0) # exit status
