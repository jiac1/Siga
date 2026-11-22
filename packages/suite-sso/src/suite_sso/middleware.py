"""Middleware de SSO para los módulos Django de la Suite.

En modo `suite` valida la cookie emitida por core, verifica la licencia del
módulo y deja la identidad en `request.suite_user`. En modo `standalone` no
hace nada: el módulo conserva su comportamiento original.
"""

from __future__ import annotations

import logging
from urllib.parse import urlencode

from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.utils.module_loading import import_string

from . import conf
from .tokens import COOKIE_NAME, TokenInvalido, verificar_token

log = logging.getLogger("suite_sso")


def _quiere_json(request) -> bool:
    accept = request.headers.get("Accept", "")
    return "application/json" in accept or request.headers.get("X-Requested-With") == "XMLHttpRequest"


class SuiteSSOMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        ruta_sync = conf.valor("SUITE_SSO_USER_SYNC")
        self.sincronizar = import_string(ruta_sync) if ruta_sync else None

    def __call__(self, request):
        request.suite_user = None
        if not conf.suite_activa() or request.path.startswith(conf.rutas_exentas()):
            return self.get_response(request)

        try:
            identidad = verificar_token(request.COOKIES.get(COOKIE_NAME))
        except TokenInvalido as exc:
            log.info("SSO rechazado en %s: %s", request.path, exc)
            if _quiere_json(request):
                return JsonResponse({"error": "no_autenticado", "login": conf.login_url()}, status=401)
            destino = f"{conf.login_url()}?{urlencode({'next': request.get_full_path()})}"
            return HttpResponseRedirect(destino)

        if conf.modulo() and not identidad.tiene_modulo(conf.modulo()):
            log.warning("Sin licencia: %s (%s) intentó usar %s", identidad.email, identidad.organizacion, conf.modulo())
            if _quiere_json(request):
                return JsonResponse({"error": "sin_licencia", "modulo": conf.modulo()}, status=403)
            return render(request, "suite_sso/sin_licencia.html", {"identidad": identidad}, status=403)

        request.suite_user = identidad
        if self.sincronizar:
            respuesta = self.sincronizar(request, identidad)
            if respuesta is not None:
                return respuesta
        return self.get_response(request)
