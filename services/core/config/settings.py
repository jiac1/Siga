"""Configuración del servicio core de SIGA-DSS.

Toda la configuración sensible o dependiente del ambiente viene de variables
de entorno (12-factor). Ver services/core/.env.example.
"""

from pathlib import Path

import dj_database_url
from decouple import Csv, config

BASE_DIR = Path(__file__).resolve().parent.parent
REPO_DIR = BASE_DIR.parent.parent

# ── Seguridad ──────────────────────────────────────────────────────
DEBUG = config("DEBUG", default=False, cast=bool)
SECRET_KEY = config("SECRET_KEY", default="dev-inseguro-solo-local" if DEBUG else "")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY es obligatoria cuando DEBUG=False")
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="localhost,127.0.0.1", cast=Csv())
CSRF_TRUSTED_ORIGINS = config("CSRF_TRUSTED_ORIGINS", default="http://localhost:8080,http://127.0.0.1:8080", cast=Csv())

# ── Suite ──────────────────────────────────────────────────────────
# Prefijo bajo el que se publica el servicio. El ALB de AWS no reescribe
# rutas, así que el servicio debe responder ya con el prefijo incluido.
URL_PREFIX = config("URL_PREFIX", default="core/")
SUITE_MODE = "suite"  # core es, por definición, el corazón de la suite
SUITE_MODULE = ""  # core no requiere licencia propia
SUITE_MODULE_NAME = "Cuenta"
SUITE_PORTAL_URL = config("SUITE_PORTAL_URL", default="/")
SUITE_LOGIN_URL = f"/{URL_PREFIX}ingresar/"
SUITE_LOGOUT_URL = f"/{URL_PREFIX}salir/"
SUITE_SSO_SECRET = config("SUITE_SSO_SECRET", default="dev-sso-secret-solo-local-cambiar-0123456789" if DEBUG else "")
if len(SUITE_SSO_SECRET) < 32:
    raise RuntimeError("SUITE_SSO_SECRET es obligatoria (mín. 32 caracteres)")
SUITE_SSO_TTL = config("SUITE_SSO_TTL", default=8 * 3600, cast=int)
SUITE_COOKIE_DOMAIN = config("SUITE_COOKIE_DOMAIN", default=None)
# Dominios de correo autorizados para autoregistro de estudiantes (vacío = registro cerrado)
REGISTRO_DOMINIOS = config("REGISTRO_DOMINIOS", default="unab.cl,uandresbello.edu", cast=Csv())

import os  # noqa: E402  (la librería suite_sso lee el secreto desde el entorno)

os.environ.setdefault("SUITE_SSO_SECRET", SUITE_SSO_SECRET)

# ── Aplicaciones ───────────────────────────────────────────────────
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "drf_spectacular",
    "suite_sso",
    "identidad",
    "catalogo",
    "convalidaciones",
    "horarios",
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
    "identidad.middleware.IdentidadSuiteMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

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
                "suite_sso.context_processors.suite",
            ]
        },
    }
]

# ── Base de datos ──────────────────────────────────────────────────
DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=config("DB_CONN_MAX_AGE", default=60, cast=int),
        conn_health_checks=True,
    )
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "identidad.Usuario"
LOGIN_URL = SUITE_LOGIN_URL
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 10}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ── Internacionalización ──────────────────────────────────────────
LANGUAGE_CODE = "es-cl"
TIME_ZONE = "America/Santiago"
USE_I18N = True
USE_TZ = True

# ── Estáticos ──────────────────────────────────────────────────────
STATIC_URL = f"/{URL_PREFIX}static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}
DATA_DIR = config("SUITE_DATA_DIR", default=str(REPO_DIR / "data"))

# ── API ────────────────────────────────────────────────────────────
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "identidad.autenticacion.SuiteCookieAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_THROTTLE_RATES": {"anon": "60/min", "user": "240/min", "solicitudes": "10/hour"},
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
}
SPECTACULAR_SETTINGS = {
    "TITLE": "SIGA-DSS · API core",
    "DESCRIPTION": "Identidad, licencias por módulo, catálogo de mallas y convalidaciones.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

# ── Correo (SES en AWS; consola en desarrollo) ─────────────────────
EMAIL_BACKEND = config("EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend")
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default="SIGA-DSS <no-responder@suite-unab.cl>")
EMAIL_HOST = config("EMAIL_HOST", default="")
EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = True

# ── Producción ────────────────────────────────────────────────────
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = config("SECURE_SSL_REDIRECT", default=True, cast=bool)
    SECURE_REDIRECT_EXEMPT = [r"^core/salud/$"]
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "SAMEORIGIN"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {"format": '{"t":"%(asctime)s","nivel":"%(levelname)s","logger":"%(name)s","msg":"%(message)s"}'}
    },
    "handlers": {"stdout": {"class": "logging.StreamHandler", "formatter": "json"}},
    "root": {"handlers": ["stdout"], "level": config("LOG_LEVEL", default="INFO")},
}
