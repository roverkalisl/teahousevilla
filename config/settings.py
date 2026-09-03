"""
Django settings for the Villa Website project.
"""

import os
from pathlib import Path

import dj_database_url
import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(DEBUG=(bool, False))
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env.list(
    "ALLOWED_HOSTS",
    default=[
        "localhost",
        "127.0.0.1",
        "teahousevilla.onrender.com",
        "teahousevillagalle.com",
        "www.teahousevillagalle.com",
    ],
)
CSRF_TRUSTED_ORIGINS = env.list(
    "CSRF_TRUSTED_ORIGINS",
    default=[
        "https://teahousevilla.onrender.com",
        "https://teahousevillagalle.com",
        "https://www.teahousevillagalle.com",
    ],
)

CLOUDINARY_URL = env("CLOUDINARY_URL", default="")
OTA_SYNC_ENABLED = env.bool("OTA_SYNC_ENABLED", default=False)
OTA_EXPORT_ENABLED = env.bool("OTA_EXPORT_ENABLED", default=False)
WHATSAPP_API_URL = env("WHATSAPP_API_URL", default="https://graph.facebook.com/v20.0")
WHATSAPP_ACCESS_TOKEN = env("WHATSAPP_ACCESS_TOKEN", default="")
WHATSAPP_PHONE_NUMBER_ID = env("WHATSAPP_PHONE_NUMBER_ID", default="")

INSTALLED_APPS = [
    "cloudinary_storage",
    "cloudinary",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "property.apps.PropertyConfig",
    "bookings.apps.BookingsConfig",
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

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "property.context_processors.site_property",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


DATABASES = {
    "default": dj_database_url.config(
        default=os.environ.get("DATABASE_URL") or f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
        ssl_require=not DEBUG,
    )
}


AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True


# Static files
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

STATICFILES_STORAGE = (
    "cloudinary_storage.storage.StaticCloudinaryStorage"
    if CLOUDINARY_URL
    else ("django.contrib.staticfiles.storage.StaticFilesStorage" if DEBUG else "whitenoise.storage.CompressedManifestStaticFilesStorage")
)
DEFAULT_FILE_STORAGE = (
    "cloudinary_storage.storage.MediaCloudinaryStorage"
    if CLOUDINARY_URL
    else "django.core.files.storage.FileSystemStorage"
)

# Manifest storage (cache-busted filenames) is only safe once `collectstatic` has run,
# so it's reserved for production; dev keeps plain storage + WhiteNoise finder passthrough.
STORAGES = {
    "staticfiles": {
        "BACKEND": STATICFILES_STORAGE,
    },
    "default": {
        "BACKEND": DEFAULT_FILE_STORAGE,
    },
}
WHITENOISE_USE_FINDERS = DEBUG

# Media files
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

if CLOUDINARY_URL:
    CLOUDINARY_STORAGE = {
        "CLOUDINARY_URL": CLOUDINARY_URL,
    }

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "admin:login"

# Email — booking inquiry notifications to the owner.
# Defaults to printing to the console in dev; set real SMTP vars in .env for production.
EMAIL_BACKEND = env(
    "EMAIL_BACKEND",
    default="django.core.mail.backends.console.EmailBackend" if DEBUG else "django.core.mail.backends.smtp.EmailBackend",
)
EMAIL_HOST = env("EMAIL_HOST", default="")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="no-reply@teahousevilla.example")
