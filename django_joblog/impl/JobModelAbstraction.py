# encoding=utf-8
from __future__ import unicode_literals

import traceback

from django.utils.translation import ugettext_lazy as _
from django.utils import timezone

from .exceptions import JobIsAlreadyRunningError


class JobModelAbstraction(object):
    """
    Base-class JobLogger communication with database.
    Not part of public API.
    """
    def __init__(self, joblog):
        self._p = joblog
        self._job_model = None
        self._thread = None

    def is_job_running(self, time_delta=None):
        """
        Return True if a job with the given name is currently running.
        :param time_delta: datetime.timedelta, optional,
                           if not None, return True only if the running job is started within now - time_delta
        :return: bool
        """
        from django_joblog.models import JobLogModel, JOB_LOG_STATE_ERROR, JOB_LOG_STATE_FINISHED, JOB_LOG_STATE_RUNNING

        if time_delta is None:
            return JobLogModel.objects.filter(
                name=self._p.name,
                state=JOB_LOG_STATE_RUNNING,
            ).exists()

        date_started = timezone.now() - time_delta
        return JobLogModel.objects.filter(
            name=self._p.name,
            state=JOB_LOG_STATE_RUNNING,
            date_started__gte=date_started,
        ).exists()

    def create_model(self):
        from django_joblog.models import JobLogModel
        if not self._p.allow_parallel and self.is_job_running():
            raise JobIsAlreadyRunningError(
                _("The job '%s' is already running and 'parallel' was set to False") % self._p.name
            )

        self._job_model = JobLogModel.start_job(self._p.name, print_to_console=self._p.print_to_console)

    def update_model(self):
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
            self._job_model.save()

    def finish(self, error_text=None):
        if self._job_model:
            self._job_model.finish(error_text, print_to_console=self._p.print_to_console)
