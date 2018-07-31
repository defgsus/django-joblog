import time, datetime
from threading import Thread

from django.test import TestCase
from django.utils import timezone

from .models import JobLogModel
from .joblogger import *


class JobLogTestCase(TestCase):
    def setUp(self):
        pass

    def test_db_creation(self):
        with JobLogger("test-db-creation"):
            pass

        qset = JobLogModel.objects.filter(name="test-db-creation")
        self.assertEqual(1, qset.count())
        self.assertEqual(1, qset[0].count)
        self.assertEqual("test-db-creation", qset[0].name)

    def test_count(self):
        with JobLogger("test-count"):
            pass
        with JobLogger("test-count"):
            pass

        qset = JobLogModel.objects.filter(name="test-count").order_by("-date_started")
        self.assertEqual(2, qset.count())
        self.assertEqual(2, qset[0].count)

    def test_time(self):
        now = timezone.now()
        with JobLogger("test-time"):
            time.sleep(1)

        model = JobLogModel.objects.get(name="test-time")

        self.assertLessEqual((model.date_started - now).total_seconds(), 0.01)
        self.assertGreaterEqual(model.duration.total_seconds(), 1.0)
        self.assertLessEqual(model.duration.total_seconds(), 1.1)

    def test_log(self):
        with JobLogger("test-log") as log:
            log.log("Hello!")
            log.log("World!")
            log.error("Hey!")
            log.error("Jude!")

        model = JobLogModel.objects.get(name="test-log")

        self.assertEqual("Hello!\nWorld!", model.log_text)
        self.assertEqual("Hey!\nJude!", model.error_text)

    def test_context(self):
        with JobLogger("test-context") as log:
            log.log("outside")
            log.error("eoutside")
            with JobLoggerContext(log, "context1"):
                log.log("inside")
                log.error("einside")
                with JobLoggerContext(log, "context2"):
                    log.log("nested")
                    log.error("enested")
            log.log("outside")
            log.error("eoutside")

        model = JobLogModel.objects.get(name="test-context")

        self.assertEqual("outside\ncontext1: inside\ncontext1:context2: nested\noutside", model.log_text)
        self.assertEqual("eoutside\ncontext1: einside\ncontext1:context2: enested\neoutside", model.error_text)

    def test_exception(self):
        with JobLogger("test-exception"):
            raise ValueError("This was bad")

        model = JobLogModel.objects.get(name="test-exception")

        self.assertEqual("ValueError - This was bad", model.error_text.split("\n")[0])

    def test_context_exception(self):
        with JobLogger("test-context-exception") as log:
            with JobLoggerContext(log, "context1"):
                with JobLoggerContext(log, "context2"):
                    raise ValueError("This was bad")

        model = JobLogModel.objects.get(name="test-context-exception")

        self.assertEqual("context1:context2: ValueError - This was bad", model.error_text.split("\n")[0])

    def test_is_running(self):
        def _task():
            with JobLogger("test-is-running"):
                time.sleep(5)

        thread = Thread(target=_task)
        thread.start()
        time.sleep(.1)

        self.assertEqual(False, JobLogModel.is_job_running("test-is-not-running"))
        self.assertEqual(True, JobLogModel.is_job_running("test-is-running"))
        self.assertEqual(True, JobLogModel.is_job_running("test-is-running", timezone.timedelta(seconds=5)))
        self.assertEqual(True, JobLogModel.is_job_running("test-is-running", datetime.timedelta(seconds=5)))
        time.sleep(1)
        self.assertEqual(False, JobLogModel.is_job_running("test-is-running", timezone.timedelta(seconds=1)))
        self.assertEqual(True, JobLogModel.is_job_running("test-is-running", timezone.timedelta(seconds=3)))

        thread.join()

        self.assertEqual(False, JobLogModel.is_job_running("test-is-running"))

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
        with self.assertRaises(JobIsAlreadyRunningError):
            with JobLogger("test-no-parallel") as log:
                log.log("try to run in parallel")

        self.assertEqual(1, JobLogModel.objects.filter(name="test-no-parallel").count())

        thread.join()