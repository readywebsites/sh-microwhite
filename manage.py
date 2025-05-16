#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'homeoayurcart.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        if "django" in str(exc).lower():
            raise ImportError(
                "Couldn't import Django. Ensure it's installed in your "
                "environment. Activate your virtual environment and run:\n"
                "    pip install django\n"
            ) from exc
        else:
            raise
    except Exception as exc:
        raise RuntimeError(
            "An unexpected error occurred while trying to run manage.py. "
            "Please check your environment and dependencies."
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
