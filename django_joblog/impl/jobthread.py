# encoding=utf-8
from __future__ import unicode_literals

import time
import asyncio
import threading
import traceback

from django.utils.translation import ugettext_lazy as _


class JobLoggerThread(object):

    def __init__(self, joblog):
        self._p = joblog
        self._ioloop = None
        self._thread = None

    def start(self):
        if not self._thread:
            self._thread = threading.Thread(target=self._start_io_loop)
            self._thread.start()

    def stop(self):
        if self._ioloop:
            self._ioloop.call_soon_threadsafe(self._ioloop.stop)

    def _start_io_loop(self):
        if not self._ioloop:
            try:
                self._ioloop = asyncio.get_event_loop()
            except RuntimeError:
                self._ioloop = asyncio.new_event_loop()
            self._ioloop.call_soon_threadsafe(self._createModel)
            self._ioloop.run_forever()

            self._ioloop.close()
            self._ioloop = None

    def _createModel(self):
        print("CREATE MODEL")
        from django_joblog.models import JobLogModel

        self._p._job_model = JobLogModel.start_job(
            name=self._p._name,
            print_to_console=self._p._print_to_console
        )

        self._ioloop.call_later(1, self._mainloop)

    def _mainloop(self):
        print("MAINLOOP")
        self._ioloop.call_later(1, self._mainloop)



