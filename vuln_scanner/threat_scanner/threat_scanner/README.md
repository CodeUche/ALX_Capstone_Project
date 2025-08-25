# Django + Celery + Redis Setup Guide

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-4.x-green.svg)](https://www.djangoproject.com/)
[![Celery](https://img.shields.io/badge/Celery-5.x-%23A0C238.svg)](https://docs.celeryq.dev/)
[![Redis](https://img.shields.io/badge/Redis-6.x-red.svg)](https://redis.io/)

A quickstart guide to integrating **Celery** with **Django** using **Redis** as both the broker and result backend.
This setup allows you to run background tasks, offload heavy processing, and schedule jobs.


# Prerequisites

* Python 3.8+
* Django project installed
* Redis installed and running
* Celery installed and running

# Why Redis?
Redis is a powerhouse for caching, queues and backgound jobs.
Running scans can sometimes take time and a single user might be required to run multiple scans per time. Redis makes queuing scans and background tasks possible without disrupting the use of the app.


# 1. Install Dependencies

pip install celery[redis] redis


# 2. Install and Run Redis

I used Docker.

Run Redis:

redis-server


# 3. Configure Celery

Created `celery.py` inside my project folder:
# project/celery.py

`import os`
`from celery import Celery`

`os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')`

`app = Celery('project')`
`app.config_from_object('django.conf:settings', namespace='CELERY')`
`app.autodiscover_tasks()`


# 4. Update `__init__.py`

In project/init.py:

`from .celery import app as celery_app`

`__all__ = ('celery_app',)`



# 5. Configure `settings.py`

`CELERY_BROKER_URL = 'redis://127.0.0.1:6379/0'`
`CELERY_RESULT_BACKEND = 'redis://127.0.0.1:6379/0'`
`CELERY_ACCEPT_CONTENT = ['json']`
`CELERY_TASK_SERIALIZER = 'json'`
`CELERY_RESULT_SERIALIZER = 'json'`
`CELERY_TIMEZONE = 'UTC'`


# 6. Create a Task

Inside myapp/tasks.py:

`from celery import shared_task`
`import time`

`@shared_task`
`def add(x, y):`
    `time.sleep(5)  # simulate long process`
    `return x + y`


# 7. Run Celery Worker

`celery -A project worker --loglevel=info`


# 8. Call the Task

`from vul_hunter.tasks import add`

# Run asynchronously
`result = add.delay(4, 6)`

# Get result later
`print(result.get(timeout=10))  # → 10`

At this point, your Django + Celery + Redis stack is fully working!
Tasks are queued in Redis, executed by Celery workers, and results are stored back in Redis.

