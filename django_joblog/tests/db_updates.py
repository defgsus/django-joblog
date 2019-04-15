import time
from threading import Thread

from django.test import TestCase
from django.db import transaction

from django_joblog.models import JobLogModel
from django_joblog import *


class JobLogDbUpdatesTestCase(TestCase):

    databases = ("default", "joblog")

    def setUp(self):
        pass

    def test_log_update(self):
        JOB_NAME = "test-log-update"
        MESSAGES = ["one second", "two seconds", "three seconds"]

        def _task():
            with JobLogger(JOB_NAME) as log:
                for msg in MESSAGES:
                    time.sleep(.5)
                    log.log(msg)
                    log.error(msg)

        thread = Thread(target=_task)
        thread.start()
        time.sleep(0.1)

        try:
            self.assertEqual(1, JobLogModel.objects.filter(name=JOB_NAME).count())

            expected_log = []
            for i, msg in enumerate(MESSAGES):
                time.sleep(.5)
                model = JobLogModel.objects.get(name=JOB_NAME)

                expected_log.append(msg)
                self.assertEqual("\n".join(expected_log), model.log_text)
                self.assertEqual("\n".join(expected_log), model.error_text)

        finally:
            thread.join()

    def test_log_update_transaction(self):
        """
        Make sure that a transaction inside a job does not block live-updates of logs
        """
        JOB_NAME = "test-log-update-transaction"
        MESSAGES = ["one second", "two seconds", "three seconds"]

        def _task():
            with JobLogger(JOB_NAME) as log:
                with transaction.atomic():
                    for msg in MESSAGES:
                        time.sleep(.5)
                        log.log(msg)
                        log.error(msg)

        thread = Thread(target=_task)
        thread.start()
        time.sleep(0.1)
        try:
            self.assertEqual(1, JobLogModel.objects.filter(name=JOB_NAME).count())

            expected_log = []
            for i, msg in enumerate(MESSAGES):
                time.sleep(.5)
                model = JobLogModel.objects.get(name=JOB_NAME)

                expected_log.append(msg)
                self.assertEqual("\n".join(expected_log), model.log_text)
                self.assertEqual("\n".join(expected_log), model.error_text)
        finally:
            thread.join()
