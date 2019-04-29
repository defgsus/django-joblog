# encoding=utf-8
from __future__ import unicode_literals


from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone

from django_joblog.models import JobLogModel
from django_joblog import Config, JobLogger


class Command(BaseCommand):
    help = "Set running jobs that seem to be killed to 'vanished' state - for 'ping' mode only"

    def add_arguments(self, parser):
        parser.add_argument("-f", "--force", nargs="?", type=bool, const=True, default=False,
                            help="Update the database even though the JOBLOG_CONFIG has 'ping' not enabled")

    def handle(self, *args, **options):
        config = Config()
        if not config.ping:
            if not options.get("force"):
                print("'ping' mode is not enabled in JOBLOG_CONFIG - this may alter the state of running jobs\n"
                      "Use -f/--force to override this warning")
                exit(-1)

        with JobLogger("joblog_cleanup", parallel=True, print_to_console=True) as job:
            JobLogModel.cleanup(joblog=job)
