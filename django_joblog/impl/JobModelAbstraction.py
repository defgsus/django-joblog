# encoding=utf-8
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.db import transaction

from .exceptions import JobIsAlreadyRunningError


class JobModelAbstraction(object):
    """
    Helper for JobLogger communication with database.
    Not part of public API.
    """
    def __init__(self, joblog):
        self._p = joblog
        self._model_pk = None

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
        from django_joblog.models import JobLogModel
        return JobLogModel.is_job_running(self._p.name, time_delta=time_delta)

    def create_model(self):
        if not self._p.allow_parallel and self.is_job_running():
            self._create_blocked_model()
            raise JobIsAlreadyRunningError(
                _("The job '%s' is already running and 'parallel' was set to False") % self._p.name
            )
        self._create_model()

    def update_model(self, allow_fail=False):
        from django_joblog.models import db_alias
        with transaction.atomic(using=db_alias()):
            model = self._get_model(allow_fail=allow_fail)
            if not model and allow_fail:
                return

            now = timezone.now()
            duration = now - model.date_started

            model.log_text = self._p.get_log_text()
            model.error_text = self._p.get_error_text()
            model.duration = duration
            model.save(using=db_alias())

    def finish(self, error_text=None):
        from django_joblog.models import db_alias
        if self._model_pk is not None:
            with transaction.atomic(using=db_alias()):
                self._finish(error_text)

    def _create_model(self):
        now = timezone.now()
        count = self.manager.filter(name=self._p.name).count() + 1
        model = self.manager.create(name=self._p.name, count=count, date_started=now)
        self._model_pk = model.pk
        if self._p.print_to_console:
            print("\n%s.%s started @ %s" % (self._p.name, count, now))
        return model

    def _create_blocked_model(self):
        from django_joblog.models import JobLogStates
        now = timezone.now()
        count = self.manager.filter(name=self._p.name).count() + 1
        model = self.manager.create(
            name=self._p.name, count=count, date_started=now,
            state=JobLogStates.blocked.name,
        )
        return model

    def _get_model(self, allow_fail=False):
        from django_joblog.models import JobLogModel
        if self._model_pk is None:
            return self._create_model()
        else:
            if not allow_fail:
                return self.manager.get(pk=self._model_pk)
            else:
                try:
                    return self.manager.get(pk=self._model_pk)
                except JobLogModel.DoesNotExist:
                    return None

    def _finish(self, exception_or_error=None):
        from django_joblog.models import db_alias, JobLogStates
        
        model = self._get_model()
        
        model.date_ended = timezone.now()
        model.duration = model.date_ended - model.date_started
        model.state = JobLogStates.finished.name
        if exception_or_error is not None:
            if model.error_text:
                model.error_text = "%s\n%s" % (model.error_text, exception_or_error)
            else:
                model.error_text = "%s" % exception_or_error
            model.state = JobLogStates.error.name
        model.save(using=db_alias())

        if self._p.print_to_console:
            if model.log_text or model.error_text:
                print("\n---summary---")
            if model.log_text:
                print("LOG:\n%s" % model.log_text)
            if model.error_text:
                print("ERROR:\n%s" % model.error_text)
            print("%s.%s finished after %s" % (model.name, model.count, model.duration))

