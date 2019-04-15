# encoding=utf-8
from __future__ import unicode_literals

import time
import asyncio
import threading
import traceback

from django.utils.translation import ugettext_lazy as _
from django.conf import settings


class JobLoggerThread(object):

    def __init__(self, joblog):
        self._p = joblog
        self._ioloop = None
        self._thread = None
        self._ping_delay = getattr(settings, "JOBLOG_CONFIG", {}).get("ping_delay", 10)
        self._stop = False

    def start(self):
        if not self._thread:
            self._thread = threading.Thread(target=self._start_io_loop)
            self._thread.start()

    def stop(self):
        self._stop = True
        if self._ioloop:
            self._ioloop.call_soon_threadsafe(self._ioloop.stop)
        if self._thread:
            self._thread.join()

    def _start_io_loop(self):
        if not self._ioloop:
            try:
                self._ioloop = asyncio.get_event_loop()
            except RuntimeError:
                self._ioloop = asyncio.new_event_loop()
            self._ioloop.call_later(self._ping_delay, self._ping)
            self._ioloop.run_forever()

            self._ioloop.close()
            self._ioloop = None

    def _ping(self):
        print("PING")
        # self._p._model.update_model()
        if not self._stop:
            self._ioloop.call_later(self._ping_delay, self._ping)



