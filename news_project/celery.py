
"""Celery app instance for the project.

Creates a Celery application and configures it from Django settings.
This file is intentionally small and safe to import even when Celery is
not configured - tasks are discovered only when Celery is installed and
the worker is started.
"""
from __future__ import annotations

import os

from celery import Celery  # type: ignore

# Set default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'news_project.settings')

app = Celery('news_project')

# Use a namespace so all celery-related config keys in Django settings
# should be prefixed with CELERY_ (e.g. CELERY_BROKER_URL).
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from installed apps (looks for tasks.py modules).
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):  # pragma: no cover - development helper
    """Prints the current Celery request for debugging purposes."""
    print(f'Request: {self.request!r}')
