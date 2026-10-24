"""Describe en OpenAPI la autenticación por cookie SSO de la Suite."""

from drf_spectacular.extensions import OpenApiAuthenticationExtension


class SuiteCookieScheme(OpenApiAuthenticationExtension):
    target_class = "identidad.autenticacion.SuiteCookieAuthentication"
    name = "suiteSSO"

    def get_security_definition(self, auto_schema):
        return {
            "type": "apiKey",
            "in": "cookie",
            "name": "suite_sso",
            "description": "JWT HS256 emitido por core al iniciar sesión (cookie HttpOnly, SameSite=Lax).",
        }
