# encoding=utf-8
from __future__ import unicode_literals

from .JobLoggerBase import JobLoggerBase


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
        assert isinstance(log, JobLoggerBase)
        self._log = log
        self._name = name

    def __enter__(self):
        self._log.push_context(self._name)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not exc_tb:
            self._log.pop_context()

