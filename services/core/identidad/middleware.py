"""Mantiene sincronizadas la sesión Django de core y la cookie SSO de la Suite."""

from suite_sso import COOKIE_NAME, TokenInvalido, verificar_token

from .sso import debe_renovarse, poner_cookie


class IdentidadSuiteMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        respuesta = self.get_response(request)
        usuario = getattr(request, "user", None)
        if getattr(request, "_suite_cookie_gestionada", False) or not (usuario and usuario.is_authenticated):
            return respuesta
        try:
            identidad = verificar_token(request.COOKIES.get(COOKIE_NAME))
            renovar = identidad.sub != str(usuario.pk) or debe_renovarse(identidad.exp)
        except TokenInvalido:
            renovar = True
        if renovar:
            poner_cookie(respuesta, usuario)
        return respuesta
