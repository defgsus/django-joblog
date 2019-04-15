# encoding=utf-8
from __future__ import unicode_literals

import traceback

from django.utils.translation import ugettext_lazy as _

from .JobLoggerBase import JobLoggerBase
from .JobModelAbstraction import JobModelAbstraction


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
        self._model = None
        self._thread = None

    def __enter__(self):
        if self._model is None:
            self._model = JobModelAbstraction(self)
            self._model.create_model()
            if self.config.ping:
                from .JobLoggerPingThread import JobLoggerPingThread
                self._thread = JobLoggerPingThread(self)
                self._thread.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._model is None:
            return True

        try:
            self._model.update_model()
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
            self._model.finish(exc_val)

            if self._thread is not None:
                self._thread.stop()

            return True

        except BaseException as e:
            self._model.finish("%s: %s" % (e.__class__.__name__, e))

            if self._thread is not None:
                self._thread.stop()

            raise e

    def log(self, line):
        """
        Add a line to the log output
        :param line: anything
        :return: None
        """
        line = self.context + ("%s" % line).strip()
        self._log_lines.append(line)

        if self._model and self.config.live_updates:
            self._model.update_model()

        if self.print_to_console:
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

        if self._model and self.config.live_updates:
            self._model.update_model()

        if self.print_to_console:
            try:
                print("ERR: %s" % line)
            except (UnicodeDecodeError, UnicodeEncodeError):
                pass

