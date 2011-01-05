import unittest
from time import sleep
from bkr.server.model import TaskStatus, Job
import sqlalchemy.orm
from turbogears.database import session
from bkr.server.test import data_setup
from bkr.server.tools import beakerd
from threading import Thread

class TestBeakerd(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        data_setup.create_test_env('min')
        session.flush()

    def setUp(self):
        self.jobs = list()
        for i in range(30):
            job = data_setup.create_job(whiteboard=u'job_%s' % i)
            self.jobs.append(job)
        session.flush()

    def _check_job_status(self,status):
        for j in self.jobs:
            job = Job.by_id(j.id)
            self.assertEqual(job.status,TaskStatus.by_name(status))

    def _create_cached_status(self):
        new_session = sqlalchemy.orm.sessionmaker()
        new_session()
        TaskStatus.by_name(u'Processed')
        TaskStatus.by_name(u'Queued')

    def test_cache_new_to_queued(self):
        my_thread = Thread(target=self._create_cached_status, name='my_thread')
        my_thread.start()

        new_success = beakerd.new_recipes()
        self.assertTrue(new_success, True)
        session.flush()
        self._check_job_status(u'Processed')

        processed_success = beakerd.processed_recipesets()
        self.assertTrue(processed_success,True)
        session.flush()
        self._check_job_status(u'Queued')
        my_thread.join(10)

    @classmethod
    def teardownClass(cls):
        pass
