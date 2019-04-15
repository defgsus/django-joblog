# encoding=utf-8
from __future__ import unicode_literals

import traceback

from django.utils.translation import ugettext_lazy as _
from django.utils import timezone

from .exceptions import JobIsAlreadyRunningError


class JobModelAbstraction(object):
    """
    Helper for JobLogger communication with database.
    Not part of public API.
    """
    def __init__(self, joblog):
        self._p = joblog
        self._job_model = None
        self._thread = None

    @property
    def manager(self):
        from django_joblog.models import JobLogModel, db_alias
        return JobLogModel.objects.using(db_alias())

    def is_job_running(self, time_delta=None):
        """
        Return True if a job with the given name is currently running.
        :param time_delta: datetime.timedelta, optional,
                           if not None, return True only if the running job is started within now - time_delta
        :return: bool
        """
        from django_joblog.models import JOB_LOG_STATE_ERROR, JOB_LOG_STATE_FINISHED, JOB_LOG_STATE_RUNNING

        if time_delta is None:
            return self.manager.filter(
                name=self._p.name,
                state=JOB_LOG_STATE_RUNNING,
            ).exists()

        date_started = timezone.now() - time_delta
        return self.manager.filter(
            name=self._p.name,
            state=JOB_LOG_STATE_RUNNING,
            date_started__gte=date_started,
        ).exists()

    def create_model(self):
        if not self._p.allow_parallel and self.is_job_running():
            raise JobIsAlreadyRunningError(
                _("The job '%s' is already running and 'parallel' was set to False") % self._p.name
            )

        self._job_model = self._create_model()

    def update_model(self):
        from django_joblog.models import db_alias

        if not self._job_model:
            self.create_model()

        log_text = None
        error_text = None

        if self._p._log_lines:
            log_text = "\n".join(self._p._log_lines)

        if self._p._error_lines:
            error_text = "\n".join(self._p._error_lines)

        if log_text != self._job_model.log_text or error_text != self._job_model.error_text:
            self._job_model.log_text = log_text
            self._job_model.error_text = error_text
            self._job_model.save(using=db_alias())

    def finish(self, error_text=None):
        if self._job_model:
            self._finish(error_text)

    def _create_model(self):
        now = timezone.now()
        count = self.manager.filter(name=self._p.name).count() + 1
        if self._p.print_to_console:
            print("\n%s.%s started @ %s" % (self._p.name, count, now))
        return self.manager.create(name=self._p.name, count=count, date_started=now)

    def _finish(self, exception_or_error=None):
        from django_joblog.models import db_alias, JOB_LOG_STATE_FINISHED, JOB_LOG_STATE_ERROR
        
        model = self._job_model
        
        model.date_ended = timezone.now()
        model.duration = model.date_ended - model.date_started
        model.state = JOB_LOG_STATE_FINISHED
        if exception_or_error is not None:
            if model.error_text:
                model.error_text = "%s\n%s" % (model.error_text, exception_or_error)
            else:
                model.error_text = "%s" % exception_or_error
            model.state = JOB_LOG_STATE_ERROR
        model.save(using=db_alias())

        if self._p.print_to_console:
            if model.log_text or model.error_text:
                print("\n---summary---")
            if model.log_text:
                print("LOG:\n%s" % model.log_text)
            if model.error_text:
                print("ERROR:\n%s" % model.error_text)
            print("%s.%s finished after %s" % (model.name, model.count, model.duration))

