# encoding=utf-8
from __future__ import unicode_literals


from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.translation import ugettext_lazy as _

from django_joblog.models import JobLogModel, JobLogStates, db_alias


class Command(BaseCommand):
    help = "List jobs"

    def add_arguments(self, parser):
        parser.add_argument("-s", "--state", nargs="+", type=str, default=[],
                            help="Specify states of jobs to list (running, finished, error, vanished)")

    def handle(self, *args, **options):
        if not options["state"]:
            qset = JobLogModel.objects.using(db_alias()).all()
        else:
            qset = None
            for state in options["state"]:
                state_qset = JobLogModel.objects.using(db_alias()).filter(state=state)
                if qset is None:
                    qset = state_qset
                else:
                    qset |= state_qset

        qset = qset.order_by("-date_started")
        qset = qset[:20]

        format_str = "%4s | %34s | %34s | %30s | %20s"
        print(format_str % ("pk", "date_started", "date_ended", "name", "state"))
        for job in qset:
            print(format_str % (job.pk, job.date_started, job.date_ended, job.name, job.state))
