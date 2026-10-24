"""Emisión de la cookie SSO de la Suite a partir de un Usuario de core."""

import time

from django.conf import settings
from suite_sso import COOKIE_NAME, SuiteIdentity, emitir_token

from .models import EventoAuditoria

# Se re-emite el token cuando le queda menos de este tiempo de vida (sesión deslizante).
UMBRAL_RENOVACION = 3600


def identidad_de(usuario) -> SuiteIdentity:
    org = usuario.organizacion
    return SuiteIdentity(
        sub=str(usuario.pk),
        email=usuario.email,
        nombre=usuario.nombre_visible,
        organizacion=org.slug if org else "",
        organizacion_nombre=org.nombre if org else "",
        roles=tuple(usuario.roles()),
        modulos=tuple(m.slug for m in usuario.modulos_habilitados()),
    )


def poner_cookie(respuesta, usuario):
    token = emitir_token(identidad_de(usuario), ttl=settings.SUITE_SSO_TTL)
    respuesta.set_cookie(
        COOKIE_NAME,
        token,
        max_age=settings.SUITE_SSO_TTL,
        path="/",
        domain=settings.SUITE_COOKIE_DOMAIN,
        secure=not settings.DEBUG,
        httponly=True,
        samesite="Lax",
    )
    return respuesta


def quitar_cookie(respuesta):
    respuesta.delete_cookie(COOKIE_NAME, path="/", domain=settings.SUITE_COOKIE_DOMAIN, samesite="Lax")
    return respuesta


def debe_renovarse(exp: int) -> bool:
    return exp - time.time() < UMBRAL_RENOVACION


def ip_de(request):
    reenviada = request.META.get("HTTP_X_FORWARDED_FOR", "")
    return (reenviada.split(",")[0].strip() or request.META.get("REMOTE_ADDR")) or None


def auditar(request, accion: str, usuario=None, **detalle):
    EventoAuditoria.objects.create(
        usuario=usuario if usuario is not None else (request.user if request.user.is_authenticated else None),
        accion=accion,
        detalle=detalle,
        ip=ip_de(request),
    )
