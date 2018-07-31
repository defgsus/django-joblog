# encoding=utf-8
from __future__ import unicode_literals

import traceback

from django.utils.translation import ugettext_lazy as _


__all__ = ("JobIsAlreadyRunningError", "JobLogger", "JobLoggerContext", "DummyJobLogger")


class JobIsAlreadyRunningError(BaseException):
    """
    Error thrown, if a job with the same name is already running
    """
    pass


class JobLoggerBase(object):
    """
    Base-class for JobLogger and DummyJobLogger.
    Not part of public API.
    """
    def __init__(self, name, parallel=False, print_to_console=False):
        self._name = name
        self._log_lines = []
        self._error_lines = []
        self._context = []
        self._allow_parallel = parallel
        self._print_to_console = print_to_console

    @property
    def name(self):
        return self._name

    @property
    def allow_parallel(self):
        return self._allow_parallel

    @property
    def context(self):
        """Returns the current context-prefix as str"""
        ctx = []
        for c in self._context:
            if not ctx or ctx[-1] != c:
                ctx.append(c)
        ret = ":".join(ctx)
        if ret:
            ret += ": "
        return ret

    def push_context(self, context_name):
        self._context.append("%s" % context_name)

    def pop_context(self):
        self._context = self._context[:-1]


class JobLogger(JobLoggerBase):
    """
    Automatic database logging,
    also catches exceptions and stores the traceback to the database

    with JobLogger("my_task") as job:
        the_task()
        job.log("some_info")
    """
    def __init__(self, name, parallel=False, print_to_console=False):
        """
        Constructs a JobLogger object. Always use with `with` statement.
        :param name: str, The name of the job
        :param parallel: bool, Allow parallel execution of jobs. If False, a JobIsAlreadyRunningError will be
                         thrown, if a job with the same name is actually running
        :param print_to_console: bool, if True, all log, error and exception texts are also printed to the console
        """
        super(JobLogger, self).__init__(name, parallel=parallel, print_to_console=print_to_console)
        self.job_model = None

    def __enter__(self):
        from .models import JobLogModel

        if not self.allow_parallel and JobLogModel.is_job_running(self._name):
            raise JobIsAlreadyRunningError(
                _("The job '%s' is already running and 'parallel' was set to False") % self._name
            )

        self.job_model = JobLogModel.start_job(self._name, print_to_console=self._print_to_console)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if self.job_model is None:
                return True
            if self._log_lines:
                self.job_model.log_text = "\n".join(self._log_lines)
            if self._error_lines:
                self.job_model.error_text = "\n".join(self._error_lines)
            if exc_tb:
                try:
                    type_name = exc_type.__name__
                except AttributeError:
                    type_name = exc_type
                if exc_val:
                    type_name = "%s - %s" % (type_name, exc_val)
                exc_val = "%s%s\n%s" % (
                    self.context,
                    type_name,
                    "".join(reversed(traceback.format_tb(exc_tb)))
                )
            self.job_model.finish(exc_val, print_to_console=self._print_to_console)
            return True
        except BaseException as e:
            self.job_model.finish("%s" % e, print_to_console=self._print_to_console)
            raise e

    def log(self, line):
        """
        Add a line to the log output
        :param line: anything
        :return: None
        """
        line = self.context + ("%s" % line).strip()
        self._log_lines.append(line)
        if self._print_to_console:
            try:
                print("LOG: %s" % line)
            except (UnicodeDecodeError, UnicodeEncodeError):
                pass

    def error(self, line):
        """
        Add a line to the error-output
        :param line: anything
        :return: None
        """
        line = self.context + ("%s" % line).strip()
        self._error_lines.append(line)
        if self._print_to_console:
            try:
                print("ERR: %s" % line)
            except (UnicodeDecodeError, UnicodeEncodeError):
                pass


class DummyJobLogger(JobLoggerBase):
    """
    A class that mimics a JobLogger,
    for functions that require a JobLogger-liker object.

    It provides no __enter__ nor __exit__ functions and can therefore not be
    used with the `with`-statement.

    It simply dumps logging and error output to the console

    with JobLogger("my_task") as log:
        the_task(log)

    def the_task(log=None):
        log = log or DummyJobLogger()
        log.log("some info")
        if 1 != 0:
            log.error("some error")

    """
    def __init__(self, name="", parallel=False):
        super(DummyJobLogger, self).__init__(name, parallel=parallel, print_to_console=True)

    def log(self, line):
        """
        Print text to the console
        :param line: anything
        :return: None
        """
        line = self.context + "%s" % line
        if self.name:
            line = self.name + ": " + line
        try:
            print("LOG: %s" % line)
        except (UnicodeDecodeError, UnicodeEncodeError):
            pass

    def error(self, line):
        """
        Print text to the console
        :param line: anything
        :return: None
        """
        line = self.context + "%s" % line
        if self.name:
            line = self.name + ": " + line
        try:
            print("ERR: %s" % line)
        except (UnicodeDecodeError, UnicodeEncodeError):
            pass


class JobLoggerContext(object):
    """
    Scoped context change for a Logger instance

    with JobLogger("my_task") as log:
        with JobLoggerContext(log, "subtask_1"):
            the_task_1(log)
        with JobLoggerContext(log, "subtask_2"):
            the_task_2(log)
            with JobLoggerContext(log, "subsubtask_2"):
                the_sub_task_2(log)
    """
    def __init__(self, log, name):
        self._log = log
        self._name = name

    def __enter__(self):
        self._log.push_context(self._name)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not exc_tb:
            self._log.pop_context()
