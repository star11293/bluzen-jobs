"""
Production settings (Render).

DEBUG is hard-coded False. Never flip it to True here. If you need to debug
prod, read the Render logs.

Required environment variables on Render:
    DJANGO_SECRET_KEY
    DATABASE_URL                (auto-injected by the Render Postgres add-on)
    DJANGO_ALLOWED_HOSTS        comma-separated, e.g.
                                jobs.bluzenhealthcarestaffing.com,bluzen-jobs.onrender.com
    SENDGRID_API_KEY
    CLOUDINARY_URL              cloudinary://api_key:api_secret@cloud_name
    DEFAULT_FROM_EMAIL          (optional, has a sensible default)
"""
from .base import *  # noqa: F401, F403
from .base import MIDDLEWARE, THIRD_PARTY_APPS, env, INSTALLED_APPS

DEBUG = False

ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS")

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
DATABASES = {
    "default": env.db_url("DATABASE_URL"),
}
# Render Postgres requires SSL.
DATABASES["default"].setdefault("OPTIONS", {})
DATABASES["default"]["OPTIONS"]["sslmode"] = "require"
DATABASES["default"]["CONN_MAX_AGE"] = 60

# ---------------------------------------------------------------------------
# Static files via WhiteNoise
# ---------------------------------------------------------------------------
# Insert WhiteNoise right after SecurityMiddleware.
MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")

STORAGES = {
    "default": {
        # Cloudinary for resume uploads (configured below).
        "BACKEND": "cloudinary_storage.storage.RawMediaCloudinaryStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# ---------------------------------------------------------------------------
# Email via SendGrid SMTP
# ---------------------------------------------------------------------------
INSTALLED_APPS = INSTALLED_APPS + ["cloudinary", "cloudinary_storage"]

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.sendgrid.net"
EMAIL_PORT = 587
EMAIL_HOST_USER = "apikey"  # literally the string "apikey", per SendGrid SMTP docs
EMAIL_HOST_PASSWORD = env("SENDGRID_API_KEY")
EMAIL_USE_TLS = True

# ---------------------------------------------------------------------------
# Cloudinary
# ---------------------------------------------------------------------------
# CLOUDINARY_URL is read automatically by the cloudinary package, but the
# django-cloudinary-storage package expects this dict form.
CLOUDINARY_STORAGE = {
    "CLOUDINARY_URL": env("CLOUDINARY_URL"),
}

# ---------------------------------------------------------------------------
# Security headers
# ---------------------------------------------------------------------------
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30  # 30 days, bump to 1 year once stable
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = False  # turn on once you're confident
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"

# CSRF trusted origins (needed for the custom subdomain).
CSRF_TRUSTED_ORIGINS = [f"https://{h}" for h in ALLOWED_HOSTS if h]

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
