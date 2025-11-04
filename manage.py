#!/usr/bin/env python
"""Django's command-line utility for administrative tasks.

This file is a convenience wrapper so you can run Django management commands
from the project root directory. It points to the news_project settings module
and ensures the inner project directory is on the Python path.
"""
import os
import sys
from django.core.management import execute_from_command_line


def main():
    """Entry point for running Django management commands from the project
    root.
    This allows you to run commands like:
    - python manage.py runserver
    - python manage.py migrate
    - python manage.py test

    From the top-level directory without needing to cd into news_project/
    """
    # Add the news_project directory to Python path so imports work correctly
    project_root = os.path.dirname(os.path.abspath(__file__))
    news_project_path = os.path.join(project_root, "news_project")
    if news_project_path not in sys.path:
        sys.path.insert(0, news_project_path)

    # Set the default Django settings module
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "news_project.settings")

    try:
        # Import to verify Django is installed
        execute_from_command_line  # noqa: B018
    except NameError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
