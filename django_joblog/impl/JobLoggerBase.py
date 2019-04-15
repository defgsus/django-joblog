# encoding=utf-8
from __future__ import unicode_literals


class JobLoggerBase(object):
    """
    Base-class for JobLogger and DummyJobLogger.
    Not part of public API.
    """
    def __init__(self, name, parallel=False, print_to_console=False):
        from .Config import Config
        self.config = Config()
        self._name = name
        self._log_lines = []
        self._error_lines = []
        self._context = []
        self._allow_parallel = parallel
        self._print_to_console = print_to_console or self.config.print_to_console

    @property
    def name(self):
        return self._name

    @property
    def allow_parallel(self):
        return self._allow_parallel

    @property
    def print_to_console(self):
        return self._print_to_console

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
