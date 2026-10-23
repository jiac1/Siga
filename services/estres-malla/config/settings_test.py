"""Configuración para pruebas automatizadas."""
import os

os.environ.setdefault("DEBUG", "True")
os.environ.setdefault("SUITE_SSO_SECRET", "pruebas-" + "x" * 40)
os.environ.setdefault("DATABASE_URL", "sqlite://:memory:")

from .settings import *  # noqa: E402,F401,F403

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
STORAGES = {**STORAGES, "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"}}
