"""
Development settings.

Run locally with:
    export DJANGO_SETTINGS_MODULE=config.settings.dev
    python manage.py runserver

Or just rely on manage.py's default (already points here).
"""
from .base import *  # noqa: F401, F403
from .base import BASE_DIR, env

DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0"]

# Local SQLite by default. If you want to test against Postgres locally,
# set DATABASE_URL in your .env and it'll switch over.
DATABASES = {
    "default": env.db_url(
        "DATABASE_URL",
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
    ),
}

# Emails print to the runserver console. No SendGrid spend in dev.
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Resume uploads land on the local filesystem in dev.
DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"

# Internal IPs for django-debug-toolbar if you add it later.
INTERNAL_IPS = ["127.0.0.1"]
