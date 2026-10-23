"""
Test settings for executing test suites with in-memory SQLite
when a local PostgreSQL service is not running.
This keeps production database configuration in config/settings.py unmodified.
"""

from .settings import *  # noqa: F401, F403

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}
