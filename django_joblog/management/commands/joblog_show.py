# encoding=utf-8
from __future__ import unicode_literals


from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.translation import ugettext_lazy as _

from django_joblog.models import JobLogModel, JobLogStates, db_alias


class Command(BaseCommand):
    help = "Show a single job"

    def add_arguments(self, parser):
        parser.add_argument("pk", type=int,
                            help="Primary key of job to display")

    def handle(self, *args, **options):
        try:
            job = JobLogModel.objects.using(db_alias()).get(pk=options["pk"])

            for n in (
                    "name", "count", "date_started", "date_ended", "duration", "state",
            ):
                print("%12s: %s" % (n, getattr(job, n)))

            if job.log_text:
                print("log:")
                print(job.log_text)
            if job.error_text:
                print("error:")
                print(job.error_text)

        except JobLogModel.DoesNotExist:
            print("Unknown pk '%s'" % options["pk"])
