## django-joblog v0.1.1

A generic django-utility that helps to log stuff to the database.

```python
from django_joblog import JobLogger

with JobLogger("task-name") as log:
    log.log("task started")
    if 1 != 2:
        log.error("The impossible happened!") 
```

The following information is stored to the database for further inspection:
- the task's name
- the count of invocation for the specific task
- start-time
- end-time
- duration 
- any log or error output 
- the exception trace, for exception occuring inside the `with`-block

This can be useful in conjuction with cronjobs and asynchronous tasks with, e.g., these libraries:
[django-kronos](https://github.com/jgorset/django-kronos), 
[django-rq](https://github.com/rq/django-rq), ...


### Installation

```bash
pip install django-joblog
```

Then add `django_joblog` to `INSTALLED_APPS` in your django `settings.py` and call `manage.py migrate`.

### Requirements

- [Python](https://www.python.org) 2 or 3
- [Django](https://www.djangoproject.com) >= 1.10

### Parallelism

By default, jobs are not allowed to run in parallel. This can be changed with `parallel=True` in 
the `JobLogger` constructor. If you start a JobLogger while a job with the same name is already
running, a `django_joblog.JobIsAlreadyRunningError` is raised.

For example, you might have a cronjob that runs every minute and looks for open tasks in the 
database. If you wrap the task in a `JobLogger` you can be sure, that the tasks are not 
worked on in parallel:

```python
from django_joblog import JobLogger, JobIsAlreadyRunningError

def cronjob_open_task_worker():
    if open_tasks():
        with JobLogger("work-open-tasks") as log:
            work_open_tasks(log)
            
# to avoid the error message on multiple invocation:
def cronjob_open_task_worker():
    if open_tasks():
        try:
            with JobLogger("work-open-tasks") as log:
                work_open_tasks(log)
        except JobIsAlreadyRunningError:
            pass
```

### Change logging context

To change the logging-context within a job, use `JobLoggerContext`. 
It might help to spot at which point an output is generated or an exception is thrown.

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
 File "/home/user/python/awesome_project/api/Api.py, line 178, in Api._make_request
   self.session.post(url, data=params)
 File "/home/user/python/awesome_project/api/Api.py, line 66, in Api.submit
   self._make_request(url, params)
 File "/home/user/python/awesome_project/main.py, line 12
   api.submit(data) 
```

### Prepare for database logging, but do not require it

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
    
    log.log("Gonna buy some eggs!")
    ...
```

### Using the model

By default, there is a django admin view for the `JobLogModel`. 
You can find the model, as usual, in `django_joblog.models`. 
Please check the file [django_joblog/models.py](https://github.com/defgsus/django-joblog/blob/master/django_joblog/models.py)
for the specific fields. It's nothing special.

![admin changelist screenshot](./docs/admin-changelist.png)

### Testing

Unit-tests are [Django-style](https://docs.djangoproject.com/en/2.0/topics/testing/overview/#running-tests) 
and are placed in [django_joblog/tests.py](https://github.com/defgsus/django-joblog/blob/master/django_joblog/tests.py).

Note that the *parallel* tests will fail with the **Sqlite** backend, because of database-locking.

### The repository

[The repo](https://github.com/defgsus/django-joblog) contains a whole django project (`django_joblog_project`) for ease of development. 
`setup.py` only exports the `django_joblog` app. 

The default database backend is configured to **MySQL**.

To start the runserver or run the tests within the repo, open mysql console:

```mysql
CREATE USER 'django_logs_user'@'localhost' IDENTIFIED BY 'django_logs_pwd';

CREATE DATABASE django_logs_test CHARACTER SET utf8 COLLATE utf8_general_ci;

GRANT ALL ON django_logs_test.* TO 'django_logs_user'@'localhost';
GRANT ALL ON test_django_logs_test.* TO 'django_logs_user'@'localhost';
``` 

Then alternatively, depending on the python version:
```bash
pip install MySQL-python    # for python 2

pip install PyMySQL         # for python 3
pip install mysqlclient     #   or alternatively
```

And finally:
```bash
./manage.py test

# or
./manage.py migrate
./manage.py runserver
```
