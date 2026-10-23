"""Lectura centralizada de la configuración SUITE_* desde settings de Django.

Modos de operación de un módulo:
  standalone  el módulo funciona solo, con su propia autenticación (o sin ella).
  suite       el módulo vive detrás del dominio de la Suite y confía en la
              cookie SSO emitida por `core`; exige licencia para el módulo.
"""

from django.conf import settings

MODO_STANDALONE = "standalone"
MODO_SUITE = "suite"


def valor(nombre: str, defecto=None):
    return getattr(settings, nombre, defecto)


def modo() -> str:
    return valor("SUITE_MODE", MODO_STANDALONE)


def suite_activa() -> bool:
    return modo() == MODO_SUITE


def modulo() -> str:
    return valor("SUITE_MODULE", "")


def modulo_nombre() -> str:
    return valor("SUITE_MODULE_NAME", modulo())


def portal_url() -> str:
    return valor("SUITE_PORTAL_URL", "/")


def login_url() -> str:
    return valor("SUITE_LOGIN_URL", "/core/ingresar/")


def logout_url() -> str:
    return valor("SUITE_LOGOUT_URL", "/core/salir/")


def rutas_exentas() -> tuple[str, ...]:
    base = ("/salud/", "/static/", "/favicon.ico")
    extra = tuple(valor("SUITE_SSO_EXEMPT_PATHS", ()))
    prefijo = valor("URL_PREFIX", "")
    con_prefijo = tuple(f"/{prefijo}{r.lstrip('/')}" for r in base) if prefijo else ()
    return base + con_prefijo + extra
