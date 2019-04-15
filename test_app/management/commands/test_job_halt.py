# encoding=utf-8
from __future__ import unicode_literals

import os
import signal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.translation import ugettext_lazy as _

from django_joblog import JobLogger, DummyJobLogger, JobLoggerContext


class Command(BaseCommand):
    help = "Run a job and exit - test for 'ping' mode"

    def add_arguments(self, parser):
        parser.add_argument("-c", nargs="?", const=True, type=bool,
                            help="Also print to console")

    def handle(self, *args, **options):
        with JobLogger("test_job", print_to_console=options.get("c")) as log:
            log.log("starting test job")
            with JobLoggerContext(log, "subtask_1"):
                log.log("now 'unexpectedly' exiting to os")
                os.kill(os.getpid(), signal.SIGKILL)
