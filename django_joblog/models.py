# encoding=utf-8
from __future__ import unicode_literals

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone


JOB_LOG_STATE_RUNNING = "running"
JOB_LOG_STATE_FINISHED = "finished"
JOB_LOG_STATE_ERROR = "error"

JOB_LOG_STATE_CHOICES = (
    (JOB_LOG_STATE_RUNNING, _("▶ running")),
    (JOB_LOG_STATE_FINISHED, _("✔ finished")),
    (JOB_LOG_STATE_ERROR, _("❌ error")),
)

JOB_LOG_STATE_MAP = {s[0]: s[1] for s in JOB_LOG_STATE_CHOICES}


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
                             choices=JOB_LOG_STATE_CHOICES, default=JOB_LOG_STATE_RUNNING)
    log_text = models.TextField(verbose_name=_("log"), default=None, null=True, blank=True, editable=False)
    error_text = models.TextField(verbose_name=_("error log"), default=None, null=True, blank=True, editable=False)

    @classmethod
    def is_job_running(cls, name, since_hours=24):
        date_started = timezone.now() - timezone.timedelta(hours=since_hours)
        return cls.objects.filter(
            name=name,
            state=JOB_LOG_STATE_RUNNING,
            date_started__gte=date_started,
        ).exists()

    @classmethod
    def start_job(cls, name):
        """Not part of public API, use JobLogger instead"""
        now = timezone.now()
        count = cls.objects.filter(name=name).count() + 1
        print("\n%s.%s started @ %s" % (name, count, now))
        return cls.objects.create(name=name, count=count, date_started=now)

    def finish(self, exception_or_error=None):
        """Not part of public API, use JobLogger instead"""
        self.date_ended = timezone.now()
        self.duration = self.date_ended - self.date_started
        self.state = JOB_LOG_STATE_FINISHED
        if exception_or_error is not None:
            if self.error_text:
                self.error_text = "%s\n%s" % (self.error_text, exception_or_error)
            else:
                self.error_text = "%s" % exception_or_error
            self.state = JOB_LOG_STATE_ERROR
        self.save()
        if self.log_text or self.error_text:
            print("-----")
        if self.log_text:
            print("LOG: %s" % self.log_text)
        if self.error_text:
            print("ERROR: %s" % self.error_text)
        print("%s finished after %s" % (self.name, self.duration))

