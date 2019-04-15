# encoding=utf-8
from __future__ import unicode_literals

from .JobLoggerBase import JobLoggerBase


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

