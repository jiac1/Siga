"""Estrés de Malla (MallaIQ) — configuración.

Modos (variable SUITE_MODE):
  standalone  app independiente con sus propias cuentas (comportamiento original)
  suite       detrás del dominio de la Suite: identidad por SSO (core) con
              aprovisionamiento automático de usuarios e instituciones.
"""
import os
from pathlib import Path

import dj_database_url
from decouple import Csv, config

BASE_DIR = Path(__file__).resolve().parent.parent

DEBUG = config("DEBUG", default=False, cast=bool)
SECRET_KEY = config("SECRET_KEY", default="dev-inseguro-solo-local" if DEBUG else "")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY es obligatoria cuando DEBUG=False")
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="localhost,127.0.0.1", cast=Csv())
CSRF_TRUSTED_ORIGINS = config("CSRF_TRUSTED_ORIGINS", default="http://localhost:8080,http://127.0.0.1:8080", cast=Csv())

# ── Suite ──────────────────────────────────────────────────────────
URL_PREFIX = config("URL_PREFIX", default="")             # 'estres-malla/' detrás del gateway
SUITE_MODE = config("SUITE_MODE", default="standalone")
SUITE_MODULE = "estres-malla"
SUITE_MODULE_NAME = "Estrés de Malla"
SUITE_PORTAL_URL = config("SUITE_PORTAL_URL", default="/")
SUITE_LOGIN_URL = config("SUITE_LOGIN_URL", default="/core/ingresar/")
SUITE_LOGOUT_URL = config("SUITE_LOGOUT_URL", default="/core/salir/")
SUITE_SSO_USER_SYNC = "accounts.sso.sincronizar_usuario"
# Catálogo de mallas: en modo suite se usa el del portal (mismo dominio, sin duplicar)
SUITE_MALLAS_URL = config("SUITE_MALLAS_URL", default="/shared/mallas/")
if SUITE_MODE == "suite":
    os.environ.setdefault("SUITE_SSO_SECRET", config("SUITE_SSO_SECRET"))

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "suite_sso",
    "accounts",
    "malla",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "suite_sso.middleware.SuiteSSOMiddleware",   # tras AuthenticationMiddleware: puede iniciar sesión local
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [BASE_DIR / "templates"],
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.debug",
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
        "suite_sso.context_processors.suite",
        "malla.context_processors.navegacion",
    ]},
}]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=config("DB_CONN_MAX_AGE", default=60, cast=int),
        conn_health_checks=True,
    )
}

AUTH_USER_MODEL = "accounts.User"
LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "malla:dashboard"
LOGOUT_REDIRECT_URL = "accounts:login"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 10}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
]

LANGUAGE_CODE = "es-cl"
TIME_ZONE = "America/Santiago"
USE_I18N = True
USE_TZ = True

STATIC_URL = f"/{URL_PREFIX}static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"] if (BASE_DIR / "static").exists() else []

# Archivos subidos (Excel de malla y actas). En AWS van a S3: los contenedores
# de ECS son efímeros y puede haber varias instancias.
MEDIA_URL = f"/{URL_PREFIX}media/"
MEDIA_ROOT = BASE_DIR / "media"
AWS_STORAGE_BUCKET_NAME = config("AWS_STORAGE_BUCKET_NAME", default="")
if AWS_STORAGE_BUCKET_NAME:
    almacenamiento = {
        "BACKEND": "storages.backends.s3.S3Storage",
        "OPTIONS": {
            "bucket_name": AWS_STORAGE_BUCKET_NAME,
            "location": config("AWS_STORAGE_PREFIX", default="estres-malla"),
            "region_name": config("AWS_S3_REGION_NAME", default="us-east-1"),
            "default_acl": None,
            "querystring_auth": True,          # URLs firmadas: el bucket no es público
            "file_overwrite": False,
        },
    }
else:
    almacenamiento = {"BACKEND": "django.core.files.storage.FileSystemStorage"}
STORAGES = {
    "default": almacenamiento,
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = config("SECURE_SSL_REDIRECT", default=True, cast=bool)
    SECURE_REDIRECT_EXEMPT = [r"salud/$"]
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "SAMEORIGIN"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"stdout": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["stdout"], "level": config("LOG_LEVEL", default="INFO")},
}
