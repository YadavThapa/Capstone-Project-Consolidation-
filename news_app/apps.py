"""Application configuration for the ``news_app`` package.

This module registers the app's signal handlers during startup by
importing :mod:`news_app.signals` inside ``AppConfig.ready()``. The
import is executed for side-effects only and is therefore performed
inside ``ready()`` to avoid import-time side effects during manage
commands and migrations.
"""

import importlib
from django.apps import AppConfig


class NewsAppConfig(AppConfig):
    """Django AppConfig for the news_app application.

    The :meth:`ready` hook imports signal handlers so they are
    registered when Django starts. Importing inside ``ready`` is the
    recommended pattern to avoid import-time side effects.
    """

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'news_app'

    def ready(self):
        """Register signal handlers by importing the signals module.

        The import is intentionally inside this method. Linters may
        warn about an import outside the module top-level or about an
        unused import because the import is performed solely for
        side-effects; those warnings are disabled on the import line.
        """
        try:
            # Imported for side-effects (signal registration).
            importlib.import_module("news_app.signals")
            # pylint: disable=unused-import
        except Exception:  # pylint: disable=broad-exception-caught
            # Avoid raising during migrations when signals' dependencies
            # may not be ready.
            pass
