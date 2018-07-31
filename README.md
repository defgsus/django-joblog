## django-joblog

A generic django-utility that helps to log stuff to the database.

```python
from django_joblog import JobLogger

with JobLogger("task-name") as log:
    log.log("task started")
    if 1 != 2:
        log.error("The impossible happened") 
```

The task's name, start-time, end-time and any logging or error output as well as exceptions 
inside the `with`-block are stored to the database for further inspection.

This can be useful in conjuction with cronjobs and asynchronous tasks with, e.g., these libraries:
[django-kronos](https://github.com/jgorset/django-kronos), 
[django-rq](https://github.com/rq/django-rq), ...

![admin changelist screenshot](./docs/admin-changelist.png)


### Installation

```bash
pip install django-joblog
```

Then add `django_joblog` to `INSTALLED_APPS` in your django `settings.py`


### Parallelism

By default, jobs are not allowed to run in parallel. This can be changed with `parallel=True` in 
the `JobLogger` constructor. If you start a JobLogger while a job with the same name is already
running, a `django_joblog.JobIsAlreadyRunningError` is raised.

### Logging context

To change the logging-context within a job, use `JobLoggerContext`. 
It might help to spot at which point an exception is thrown.

```python
from django_joblog import JobLogger, JobLoggerContext

with JobLogger("pull-the-api") as log:
    
    credentials = get_credentials()
    log.log("using user %s" % credentials.name)
    
    with JobLoggerContext(log, "api"):
        api = Api(credentials)
        log.log("connected")
        
        with JobLoggerContext(log, "submit"):
            api.submit(data)
            log.log("%s items submitted" % len(data))
            
        with JobLoggerContext(log, "check result"):
            log.log(api.check_result())
```            

The log output in database will look like this:
```
using user Herbert
api: connected
api:submit: 42 items submitted
api:check result: 23 items updated
```

An exception caught by the error log might look like this:
```
api:submit: IOError - Status code 404 returned for url https://my.api.com/submit
 File "/home/user/python/awesome_project/api/Api.py, line 66, in Api.submit
   self._make_request(url, params)
 File "/home/user/python/awesome_project/main.py, line 12
   api.submit(data) 
```

### prepare for database logging, but do not require it

You can use the `DummyJobLogger` class to provide logging without storing stuff to the database. 
This might be useful for debugging purposes, or if you run a function as a `manage.py`-task but
need database logging only for cronjobs.

```python
from django_joblog import JobLogger, DummyJobLogger

def cronjob_invokation():
    with JobLogger("buy-eggs") as log:
        buy_eggs(log)
        
def debug_invokation():
    buy_eggs()

def buy_eggs(log=None):
    log = log or DummyJobLogger()
    
    log("Gonna buy some eggs!")
    ...
```
