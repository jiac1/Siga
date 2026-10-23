"""Aprovisionamiento automático (just-in-time) desde el SSO de la Suite.

En modo suite, la primera vez que alguien entra con la cookie de core se le
crea (o actualiza) su usuario local y su institución, con el rol equivalente.
Así el modelo multi-institución original de MallaIQ se mantiene intacto y
solo cambia la fuente de identidad.
"""
from django.contrib.auth import login

from .models import Organization, User

ROL_DESDE_SUITE = [
    ("superadmin", User.Rol.ADMIN),
    ("admin_institucion", User.Rol.ORG_ADMIN),
    ("staff", User.Rol.DOCENTE),
    ("docente", User.Rol.DOCENTE),
]


def rol_local(roles_suite) -> str:
    return next((local for suite, local in ROL_DESDE_SUITE if suite in roles_suite), User.Rol.VIEWER)


def sincronizar_usuario(request, identidad):
    actual = request.user if request.user.is_authenticated else None
    if actual and actual.username == identidad.email:
        return None

    org = None
    if identidad.organizacion:
        org, _ = Organization.objects.get_or_create(
            slug=identidad.organizacion,
            defaults={"nombre": identidad.organizacion_nombre or identidad.organizacion, "activa": True})

    nombre, _, apellido = (identidad.nombre or "").partition(" ")
    usuario, _ = User.objects.update_or_create(
        username=identidad.email,
        defaults={
            "email": identidad.email, "first_name": nombre[:150], "last_name": apellido[:150],
            "organization": org, "rol": rol_local(identidad.roles),
            "is_staff": "superadmin" in identidad.roles, "is_superuser": "superadmin" in identidad.roles,
        },
    )
    if usuario.has_usable_password():
        usuario.set_unusable_password()  # en modo suite no se inicia sesión con clave local
        usuario.save(update_fields=["password"])
    login(request, usuario, backend="django.contrib.auth.backends.ModelBackend")
    return None
