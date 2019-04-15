import time
from threading import Thread

from django.test import TestCase

from django_joblog.models import JobLogModel
from django_joblog import *


class JobLogParallelTestCase(TestCase):
    def setUp(self):
        pass

    def test_parallel(self):
        def _task():
            with JobLogger("test-parallel", parallel=True) as log:
                time.sleep(1)
                log.log("Great!")

        threads = []
        for i in range(3):
            threads.append(Thread(target=_task))
            threads[-1].start()

        for t in threads:
            t.join()

        self.assertEqual(3, JobLogModel.objects.filter(name="test-parallel").count())

    def test_no_parallel(self):
        def _task():
            with JobLogger("test-no-parallel") as log:
                time.sleep(1)
                log.log("Great!")

        thread = Thread(target=_task)
        thread.start()
        time.sleep(0.1)

        try:
            with self.assertRaises(JobIsAlreadyRunningError):
                with JobLogger("test-no-parallel") as log:
                    log.log("try to run in parallel")

            self.assertEqual(1, JobLogModel.objects.filter(name="test-no-parallel").count())

        finally:
            thread.join()
