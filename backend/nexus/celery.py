"""Celery application for Nexus.

The broker/result settings live in settings/base.py under the CELERY_ namespace;
this module builds the app, pulls that config, and auto-discovers tasks.py in
every installed app. With no REDIS_URL the broker falls back to memory:// so the
app still imports in dev and tests without a running broker.
"""
import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nexus.settings.base")

app = Celery("nexus")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
