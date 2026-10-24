"""Vistas transversales que todo servicio expone (health check para el ALB)."""

import os

from django.conf import settings
from django.db import connection
from django.http import JsonResponse

from . import conf


def salud(request):
    """Liveness/readiness: responde 200 si el proceso y (si existe) la BD responden."""
    estado = {
        "estado": "ok",
        "servicio": conf.modulo() or "core",
        "modo": conf.modo(),
        "version": os.environ.get("APP_VERSION", "dev"),
    }
    motor_bd = (settings.DATABASES.get("default") or {}).get("ENGINE", "django.db.backends.dummy")
    if motor_bd.endswith("dummy"):  # servicios sin base de datos (p. ej. Mapa de Calor)
        return JsonResponse(estado)
    try:
        with connection.cursor() as c:
            c.execute("SELECT 1")
        estado["bd"] = "ok"
    except Exception as exc:  # pragma: no cover - depende de la infraestructura
        estado.update(estado="degradado", bd=f"error: {exc.__class__.__name__}")
        return JsonResponse(estado, status=503)
    return JsonResponse(estado)
