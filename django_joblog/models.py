# encoding=utf-8
from __future__ import unicode_literals

import warnings
import enum

from django.db import models, transaction
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.conf import settings
from django.db import DEFAULT_DB_ALIAS

from . import Config


class JobLogStates(enum.Enum):
    """
    Enum for all possible states of JobLogModel.state field
    """
    running = _("▶ running")
    finished = _("✔ finished")
    error = _("❌ error")
    blocked = _("🖐 blocked")
    vanished = _("⊙ vanished")


def db_alias():
    """
    Returns the db name to use for JobLogModel.
    Return "joblog" if such a database is configured else defaults to django.db.DEFAULT_DB_ALIAS
    :return: str
    """
    alias = Config().db_alias
    if alias not in settings.DATABASES:
        warnings.warn("Configured job-logger db alias '%s' is not in settings.DATABASES" % alias)
        return DEFAULT_DB_ALIAS
    return alias


class JobLogModel(models.Model):
    class Meta:
        verbose_name = _("Job log")
        verbose_name_plural = _("Job logs")

    name = models.CharField(verbose_name=_("name"), max_length=128, editable=False, default="", db_index=True)
    count = models.BigIntegerField(verbose_name=_("count"), editable=False, default=0)
    date_started = models.DateTimeField(verbose_name=_("started"), default=timezone.now, editable=False, db_index=True)
    date_ended = models.DateTimeField(verbose_name=_("ended"), default=None, editable=False, null=True, blank=True, db_index=True)
    duration = models.DurationField(verbose_name=_("duration"), default=None, null=True, blank=True, db_index=True)
    state = models.CharField(verbose_name=_("state"), max_length=64, editable=False, db_index=True,
                             choices=[(e.name, e.value) for e in JobLogStates], default=JobLogStates.running.name)
    log_text = models.TextField(verbose_name=_("log"), default=None, null=True, blank=True, editable=False)
    error_text = models.TextField(verbose_name=_("error log"), default=None, null=True, blank=True, editable=False)

    @classmethod
    def is_job_running(cls, name, time_delta=None, ping=None):
        """
        Return True if a job with the given name is currently running.
        :param name: str
        :param time_delta: datetime.timedelta, optional,
                           if not None, return True only if the running job is started within now - time_delta
        :param ping: bool, overrides the "ping" setting in django.conf.settings.JOBLOG_CONFIG
                When true, jobs will be considered "vanished" when their "duration" field is significantly
                smaller than their true duration
        :return: bool
        """
        if ping is None:
            ping = Config().ping

        if time_delta is None:
            qset = cls.objects.using(db_alias()).filter(
                name=name,
                state=JobLogStates.running.name,
            )
        else:
            date_started = timezone.now() - time_delta
            qset = cls.objects.using(db_alias()).filter(
                name=name,
                state=JobLogStates.running.name,
                date_started__gte=date_started,
            )

        if not qset.exists():
            return False

        if not ping:
            return qset.exists()

        leeway = Config().ping_interval
        now = timezone.now()
        for date_started, duration in qset.values_list("date_started", "duration"):
            true_duration = now - date_started

            if not duration:
                if true_duration.total_seconds() < leeway + 1:
                    # a probably still running job which has not updated it's "duration" field yet
                    return True
                continue

            if true_duration.total_seconds() <= duration.total_seconds() + leeway:
                # a running job who's "duration" has been updated recently
                return True

        return False

    @classmethod
    def cleanup(cls, joblog=None):
        """
        Set all jobs that are running but who's update is older than JOBLOG_CONFIG["ping_interval"] to 'vanished'.
        Careful! JOBLOG_CONFIG["ping"] must be enabled for this to work reliably.
        :param joblog: optional JobLogger instance to log the result
        """
        from django_joblog import DummyJobLogger
        now = timezone.now()
        leeway = Config().ping_interval
        joblog = joblog or DummyJobLogger()

        with transaction.atomic():
            qset = cls.objects.using(db_alias()).filter(state=JobLogStates.running.name)
            num_running = qset.count()
            to_delete = []

            for pk, date_started, duration in qset.values_list("pk", "date_started", "duration"):
                true_duration = now - date_started

                if not duration:
                    if true_duration.total_seconds() < leeway:
                        # a probably still running job which has not updated it's "duration" field yet
                        continue
                else:
                    if true_duration.total_seconds() <= duration.total_seconds() + leeway:
                        # a running job who's "duration" has been updated recently
                        continue

                to_delete.append(pk)

            if not to_delete:
                joblog.log("%s job(s) running, all valid" % num_running)
            else:
                joblog.log("%s job(s) running, %s vanished" % (num_running, len(to_delete)))
                for pk in to_delete:
                    try:
                        job = cls.objects.using(db_alias()).get(pk=pk)
                        job.state = JobLogStates.vanished.name
                        if not job.date_ended:
                            if job.duration:
                                job.date_ended = job.date_started + job.duration
                            else:
                                job.date_ended = now
                        job.save(using=db_alias())
                    except cls.DoesNotExist:
                        pass
