"""Project package initializer.

Import the Celery app here so `celery -A news_project worker` will find it
when a worker is started. Import is safe even if Celery is not installed.
"""

try:  # pragma: no cover - import-time convenience for Celery workers
    from .celery import app as CELERY_APP  # noqa: F401
except ImportError:  # noqa: BLE001 - optional dependency may be absent
    # Celery may not be installed in all environments (development/test).
    CELERY_APP = None  # type: ignore
