""":mod:`cliche.worker` --- Celery_-backed task queue worker
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. _Celery: http://www.celeryproject.org/

"""
from celery import Celery

worker = Celery(__name__)
