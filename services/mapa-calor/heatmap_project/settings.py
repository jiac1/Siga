"""Mapa de Calor de salas — configuración.

Funciona en dos modos (variable SUITE_MODE):
  standalone  app independiente, sin autenticación (comportamiento original)
  suite       detrás del dominio de la Suite: exige SSO y licencia del módulo
"""
from pathlib import Path

from decouple import Csv, config

BASE_DIR = Path(__file__).resolve().parent.parent

DEBUG = config('DEBUG', default=False, cast=bool)
SECRET_KEY = config('SECRET_KEY', default='dev-inseguro-solo-local' if DEBUG else '')
if not SECRET_KEY:
    raise RuntimeError('SECRET_KEY es obligatoria cuando DEBUG=False')
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=Csv())
CSRF_TRUSTED_ORIGINS = config('CSRF_TRUSTED_ORIGINS', default='http://localhost:8080,http://127.0.0.1:8080', cast=Csv())

# ── Suite ──────────────────────────────────────────────────────────
URL_PREFIX = config('URL_PREFIX', default='')            # 'mapa-calor/' detrás del gateway
SUITE_MODE = config('SUITE_MODE', default='standalone')
SUITE_MODULE = 'mapa-calor'
SUITE_MODULE_NAME = 'Mapa de Calor de salas'
SUITE_PORTAL_URL = config('SUITE_PORTAL_URL', default='/')
SUITE_LOGIN_URL = config('SUITE_LOGIN_URL', default='/core/ingresar/')
SUITE_LOGOUT_URL = config('SUITE_LOGOUT_URL', default='/core/salir/')
if SUITE_MODE == 'suite':
    import os
    os.environ.setdefault('SUITE_SSO_SECRET', config('SUITE_SSO_SECRET'))

INSTALLED_APPS = [
    'django.contrib.staticfiles',
    'django.contrib.contenttypes',
    'suite_sso',
    'heatmap',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'suite_sso.middleware.SuiteSSOMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'heatmap_project.urls'

TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [],
    'APP_DIRS': True,
    'OPTIONS': {'context_processors': [
        'django.template.context_processors.request',
        'django.template.context_processors.csrf',
        'suite_sso.context_processors.suite',
    ]},
}]

WSGI_APPLICATION = 'heatmap_project.wsgi.application'

# Sin base de datos: el servicio es sin estado (escala horizontalmente en ECS).
DATABASES = {}

LANGUAGE_CODE = 'es-cl'
TIME_ZONE = 'America/Santiago'
USE_I18N = True
USE_TZ = True

STATIC_URL = f'/{URL_PREFIX}static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'},
}

FILE_UPLOAD_MAX_MEMORY_SIZE = 20 * 1024 * 1024  # 20 MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 20 * 1024 * 1024

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=True, cast=bool)
    SECURE_REDIRECT_EXEMPT = [r'salud/$']
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_CONTENT_TYPE_NOSNIFF = True

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {'stdout': {'class': 'logging.StreamHandler'}},
    'root': {'handlers': ['stdout'], 'level': config('LOG_LEVEL', default='INFO')},
}
