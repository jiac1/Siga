"""Emisión y verificación de tokens de sesión de la Suite (JWT HS256).

El secreto compartido se lee de la variable de entorno SUITE_SSO_SECRET (en
AWS viene de Secrets Manager). Todos los servicios deben usar el mismo valor.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field

import jwt

COOKIE_NAME = "suite_sso"
ALGORITMO = "HS256"
EMISOR = "suite-unab-core"
AUDIENCIA = "suite-unab"
TTL_POR_DEFECTO = 8 * 3600  # una jornada de trabajo


class TokenInvalido(Exception):
    """El token no existe, expiró, fue alterado o no corresponde a la Suite."""


def _secreto(secreto: str | None) -> str:
    valor = secreto or os.environ.get("SUITE_SSO_SECRET", "")
    if len(valor) < 32:
        raise TokenInvalido("SUITE_SSO_SECRET no configurado o demasiado corto (mín. 32 caracteres)")
    return valor


@dataclass(frozen=True)
class SuiteIdentity:
    """Identidad del usuario tal como viaja entre módulos."""

    sub: str  # id estable del usuario en core
    email: str
    nombre: str
    organizacion: str  # slug de la institución (tenant)
    organizacion_nombre: str = ""
    roles: tuple[str, ...] = ()
    modulos: tuple[str, ...] = ()  # slugs de módulos licenciados para la institución
    exp: int = 0
    extra: dict = field(default_factory=dict)

    def tiene_modulo(self, slug: str) -> bool:
        return slug in self.modulos

    def tiene_rol(self, *roles: str) -> bool:
        return any(r in self.roles for r in roles)

    def como_dict(self) -> dict:
        return {
            "sub": self.sub,
            "email": self.email,
            "nombre": self.nombre,
            "organizacion": self.organizacion,
            "organizacion_nombre": self.organizacion_nombre,
            "roles": list(self.roles),
            "modulos": list(self.modulos),
            "exp": self.exp,
        }


def emitir_token(identidad: SuiteIdentity, ttl: int = TTL_POR_DEFECTO, secreto: str | None = None) -> str:
    ahora = int(time.time())
    payload = identidad.como_dict()
    payload.update({"iss": EMISOR, "aud": AUDIENCIA, "iat": ahora, "exp": ahora + ttl})
    return jwt.encode(payload, _secreto(secreto), algorithm=ALGORITMO)


def verificar_token(token: str | None, secreto: str | None = None) -> SuiteIdentity:
    if not token:
        raise TokenInvalido("sin token")
    try:
        p = jwt.decode(
            token,
            _secreto(secreto),
            algorithms=[ALGORITMO],
            audience=AUDIENCIA,
            issuer=EMISOR,
            options={"require": ["exp", "iat", "sub"]},
        )
    except jwt.PyJWTError as exc:
        raise TokenInvalido(str(exc)) from exc
    return SuiteIdentity(
        sub=str(p["sub"]),
        email=p.get("email", ""),
        nombre=p.get("nombre", ""),
        organizacion=p.get("organizacion", ""),
        organizacion_nombre=p.get("organizacion_nombre", ""),
        roles=tuple(p.get("roles", ())),
        modulos=tuple(p.get("modulos", ())),
        exp=int(p["exp"]),
    )
