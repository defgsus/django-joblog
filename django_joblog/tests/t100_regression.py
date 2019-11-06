import time
from threading import Thread
from functools import partial

from django.test import TestCase
from django.db import transaction, connections

from django_joblog.models import JobLogModel
from django_joblog import *


class JobLogRegressionTests(TestCase):

    databases = ("default", "joblog")

    def setUp(self):
        pass

    def test_bug_hanging_jobs(self):
        """
        Make sure that a job always writes 'finished' to database
        """
        JOB_NAME = "test-hanging"
        NUM_THREADS = 10
        NUM_JOBS = 5

        def _task(job_name):
            for i in range(NUM_JOBS):
                with JobLogger(job_name) as log:
                    log.log("starting transaction")
                    with transaction.atomic():
                        log.log("sleeping")
                        time.sleep(1.1)
                        log.log("finished")
                    log.log("ended transaction")
                time.sleep(.5)
            connections.close_all()

        threads = [
            Thread(target=partial(_task, "%s-%s" % (JOB_NAME, i)))
            for i in range(NUM_THREADS)
        ]
        for t in threads:
            t.start()

        for t in threads:
            t.join()

        for i in range(NUM_THREADS):
            job_name = "%s-%s" % (JOB_NAME, i)
            self.assertEqual(
                NUM_JOBS,
                JobLogModel.objects.filter(name=job_name).count()
            )
            self.assertEqual(
                NUM_JOBS,
                JobLogModel.objects.filter(name=job_name).exclude(date_ended=None).count()
            )
