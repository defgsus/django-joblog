from django.conf import settings


class Config:

    def __init__(self):
        self._config = getattr(settings, "JOBLOG_CONFIG", {})

    @property
    def print_to_console(self):
        return self._config.get("print_to_console", False)

    @property
    def db_alias(self):
        from django.db import DEFAULT_DB_ALIAS
        return self._config.get("db_alias", DEFAULT_DB_ALIAS)

    @property
    def live_updates(self):
        return self._config.get("live_updates", False)

    @property
    def ping(self):
        return self._config.get("ping", False)

    @property
    def ping_interval(self):
        return self._config.get("ping_interval", 10)

