import os
import sys
from pathlib import Path

from taskmaster.recaptchav3 import RECAPTCHA_SECRET_KEY, RECAPTCHA_SITE_KEY

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Load local secrets if present.
try:
    from local_settings import (
        RESEND_API_KEY as LOCAL_RESEND_API_KEY,
        DATABASE_URL as LOCAL_DATABASE_URL,
    )
except ImportError:
    LOCAL_RESEND_API_KEY = None
    LOCAL_DATABASE_URL = None

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "django-insecure-taskmaster-dev-key")
DEBUG = os.environ.get("DJANGO_DEBUG", "True").lower() in ("1", "true", "yes")
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "*").split(",")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "taskmaster",
    "crispy_forms",
    "crispy_bootstrap4",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "taskmaster_site.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [str(BASE_DIR / "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]

WSGI_APPLICATION = "taskmaster_site.wsgi.application"
ASGI_APPLICATION = "taskmaster_site.asgi.application"

DATABASE_URL = os.environ.get("DATABASE_URL", LOCAL_DATABASE_URL)
if DATABASE_URL:
    from urllib.parse import parse_qs, urlparse

    parsed_db_url = urlparse(DATABASE_URL)
    if parsed_db_url.scheme in ("postgresql", "postgres", "postgresql+psycopg2"):
        engine = "django.db.backends.postgresql"
    elif parsed_db_url.scheme in ("mysql", "mysql+mysqlconnector"):
        engine = "django.db.backends.mysql"
    else:
        raise ValueError(f"Unsupported DATABASE_URL scheme: {parsed_db_url.scheme}")

    query_params = parse_qs(parsed_db_url.query)
    options = {}
    if "sslmode" in query_params:
        options["sslmode"] = query_params["sslmode"][0]

    DATABASES = {
        "default": {
            "ENGINE": engine,
            "NAME": parsed_db_url.path.lstrip("/"),
            "USER": parsed_db_url.username,
            "PASSWORD": parsed_db_url.password,
            "HOST": parsed_db_url.hostname,
            "PORT": parsed_db_url.port or "",
            "OPTIONS": options,
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = "en-us"
TIME_ZONE = "America/New_York"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATICFILES_DIRS = [BASE_DIR / "static"]
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CRISPY_TEMPLATE_PACK = "bootstrap4"

# Resend email service configuration
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", LOCAL_RESEND_API_KEY)
DEFAULT_FROM_EMAIL = "Task Master <no-reply@masteroftasks.com>"
