"""Autenticación de la API de core mediante la cookie SSO de la Suite."""

from rest_framework.authentication import BaseAuthentication
from suite_sso import COOKIE_NAME, TokenInvalido, verificar_token

from .models import Usuario


class SuiteCookieAuthentication(BaseAuthentication):
    """Acepta la cookie `suite_sso` (la misma que validan los demás módulos)."""

    def authenticate(self, request):
        token = request.COOKIES.get(COOKIE_NAME)
        if not token:
            return None
        try:
            identidad = verificar_token(token)
        except TokenInvalido:
            return None
        usuario = Usuario.objects.filter(pk=identidad.sub, is_active=True).select_related("organizacion").first()
        if usuario is None:
            return None
        return usuario, identidad

    def authenticate_header(self, request):
        return 'Cookie realm="suite-unab"'
