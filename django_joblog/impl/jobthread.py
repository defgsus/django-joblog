# encoding=utf-8
from __future__ import unicode_literals

import time
import threading
import traceback
import datetime

from django.utils.translation import ugettext_lazy as _
from django.conf import settings


class JobLoggerThread(object):

    def __init__(self, joblog):
        self._p = joblog
        self._ioloop = None
        self._thread = None
        self._ping_delay = getattr(settings, "JOBLOG_CONFIG", {}).get("ping_delay", 10)
        self._next_ping_time = None
        self._stop = False

    def start(self):
        if not self._thread:
            self._next_ping_time = datetime.datetime.now() + datetime.timedelta(seconds=self._ping_delay)
            self._thread = threading.Thread(target=self._mainloop)
            self._thread.start()

    def stop(self):
        self._stop = True
        if self._thread:
            self._thread.join()
            self._thread = None

    def _mainloop(self):
        while not self._stop:
            time.sleep(.5)
            if datetime.datetime.now() >= self._next_ping_time:
                self._next_ping_time = datetime.datetime.now() + datetime.timedelta(seconds=self._ping_delay)
                # print("PING")
                if not self._stop:
                    self._p._model.update_model(allow_fail=True)
