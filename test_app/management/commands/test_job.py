# encoding=utf-8
from __future__ import unicode_literals


from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.translation import ugettext_lazy as _

from django_joblog import JobLogger, DummyJobLogger, JobLoggerContext


class Command(BaseCommand):
    help = "Run a job and log it's output"

    def handle(self, *args, **options):
        with JobLogger("test_job") as log:
            log.log("starting test job")
            with JobLoggerContext(log, "subtask_1"):
                some_task_that_may_fail(log)
            with JobLoggerContext(log, "subtask_2"):
                some_task_that_may_fail(log)


def some_task_that_may_fail(log=None):
    import random, time
    log = log or DummyJobLogger()

    sec = random.uniform(2, 5)+50
    log.log("waiting {:.2f} seconds".format(sec))
    time.sleep(sec)

    if random.randrange(10) == 0:
        raise RuntimeError("There was a problem")

    log.log("finished")

