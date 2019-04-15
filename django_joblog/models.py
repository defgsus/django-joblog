# encoding=utf-8
from __future__ import unicode_literals

import warnings
import enum

from django.db import models
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
    halted = _("❎ halted")


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
                When true, jobs will be considered "halted" when their "duration" field is significantly
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

        leeway = Config().ping_delay
        now = timezone.now()
        for date_started, duration in qset.values_list("date_started", "duration"):
            true_duration = now - date_started

            if not duration:
                if true_duration.total_seconds() < leeway:
                    # a probably still running job which has not updated it's "duration" field yet
                    return True
                continue

            if true_duration.total_seconds() <= duration.total_seconds() + leeway:
                # a running job who's "duration" has been updated recently
                return True

        return False

