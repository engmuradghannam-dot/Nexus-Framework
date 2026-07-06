import os
from celery import Celery
from celery.signals import task_failure
import logging

logger = logging.getLogger(__name__)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nexus.settings')

app = Celery('nexus')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Queue configuration
app.conf.task_queues = {
    'default': {
        'exchange': 'default',
        'routing_key': 'default',
    },
    'high_priority': {
        'exchange': 'high_priority',
        'routing_key': 'high_priority',
    },
    'low_priority': {
        'exchange': 'low_priority',
        'routing_key': 'low_priority',
    },
}

app.conf.task_default_queue = 'default'
app.conf.task_routes = {
    'apps.hr.tasks.*': {'queue': 'default'},
    'apps.projects.tasks.*': {'queue': 'default'},
    'apps.accounts.tasks.*': {'queue': 'low_priority'},
}

# Result backend
app.conf.result_backend = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
app.conf.result_expires = 3600  # 1 hour

# Task execution settings
app.conf.task_time_limit = 300  # 5 minutes
app.conf.task_soft_time_limit = 240  # 4 minutes
app.conf.worker_prefetch_multiplier = 1  # Fair task distribution
app.conf.worker_max_tasks_per_child = 1000  # Restart worker after 1000 tasks

# Retry settings
app.conf.task_default_retry_delay = 60  # 1 minute
app.conf.task_max_retries = 3

# Monitoring
app.conf.worker_send_task_events = True
app.conf.task_send_sent_event = True


@task_failure.connect
def handle_task_failure(sender=None, task_id=None, exception=None, args=None, kwargs=None, traceback=None, einfo=None, **kw):
    """Handle task failures - log and notify."""
    logger.error(f"Task {sender.name} [{task_id}] failed: {exception}")
    # Could send notification to admin here
