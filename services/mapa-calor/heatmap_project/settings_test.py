"""Configuración para pruebas automatizadas."""
import os

os.environ.setdefault("DEBUG", "True")
os.environ.setdefault("SUITE_SSO_SECRET", "pruebas-" + "x" * 40)

from .settings import *  # noqa: E402,F401,F403
