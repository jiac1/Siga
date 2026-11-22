"""Registra los módulos de la Suite, la institución UNAB y (opcional) datos de demostración.

Idempotente: puede ejecutarse en cada despliegue.

  python manage.py inicializar_suite            módulos + UNAB + superusuario (si SUITE_ADMIN_* está definido)
  python manage.py inicializar_suite --demo     además, usuarios e institución de demostración
"""

import os
import secrets

from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand
from django.db import transaction

from identidad.models import Licencia, Modulo, Organizacion, Rol, Usuario

MODULOS = [
    dict(
        slug="malla",
        nombre="Malla curricular",
        icono="M",
        color="#102338",
        orden=10,
        ruta="/apps/malla/index.html",
        descripcion="Consulta interactiva de la malla de tu carrera, con prerrequisitos y registro de avance.",
        roles_permitidos="superadmin,admin_institucion,staff,docente,estudiante",
    ),
    dict(
        slug="convalidacion",
        nombre="Convalidación de asignaturas",
        icono="C",
        color="#d8232a",
        orden=20,
        ruta="/apps/convalidacion/index.html",
        acceso_publico=True,
        descripcion=(
            "Pre-evaluación de convalidación para postulantes de otras universidades, "
            "con revisión de la Dirección de Carrera."
        ),
        roles_permitidos="superadmin,admin_institucion,staff,docente,estudiante",
    ),
    dict(
        slug="horarios",
        nombre="Generador de horarios",
        icono="H",
        color="#5b7495",
        orden=30,
        ruta="/apps/horarios/index.html",
        descripcion="Arma combinaciones de horario sin topes a partir de la programación académica.",
        roles_permitidos="superadmin,admin_institucion,staff,docente,estudiante",
    ),
    dict(
        slug="mapa-calor",
        nombre="Mapa de calor de salas",
        icono="MC",
        color="#1d3e63",
        orden=40,
        ruta="/mapa-calor/",
        tipo=Modulo.Tipo.SERVICIO,
        descripcion="Ocupación de salas por bloque horario a partir de la programación académica.",
        roles_permitidos="superadmin,admin_institucion,staff,docente",
    ),
    dict(
        slug="estres-malla",
        nombre="Estrés de malla",
        icono="EM",
        color="#2f5233",
        orden=50,
        ruta="/estres-malla/",
        tipo=Modulo.Tipo.SERVICIO,
        descripcion="Detecta cuellos de botella de la malla según tasas de reprobación por asignatura.",
        roles_permitidos="superadmin,admin_institucion,staff,docente",
    ),
    dict(
        slug="siga",
        nombre="SIGA · visión de producto",
        icono="S",
        color="#8794a6",
        orden=60,
        ruta="/apps/siga/index.html",
        descripcion="Presentación del sistema integrado de gestión académica (demostración con datos de ejemplo).",
        roles_permitidos="superadmin,admin_institucion,staff,docente,estudiante",
    ),
]


def _clave(variable: str) -> tuple[str, bool]:
    valor = os.environ.get(variable)
    return (valor, False) if valor else (secrets.token_urlsafe(12), True)


class Command(BaseCommand):
    help = "Inicializa módulos, institución UNAB, licencias y usuarios base de la Suite"

    def add_arguments(self, parser):
        parser.add_argument("--demo", action="store_true", help="Crea usuarios e institución de demostración")

    @transaction.atomic
    def handle(self, *args, demo=False, **opts):
        for datos in MODULOS:
            Modulo.objects.update_or_create(slug=datos["slug"], defaults=datos)
        self.stdout.write(f"Módulos registrados: {Modulo.objects.count()}")

        unab, _ = Organizacion.objects.update_or_create(
            slug="unab",
            defaults={
                "nombre": "Universidad Andrés Bello",
                "dominios_correo": "unab.cl,uandresbello.edu",
                "activa": True,
            },
        )
        for m in Modulo.objects.all():
            Licencia.objects.update_or_create(
                organizacion=unab, modulo=m, defaults={"plan": Licencia.Plan.SUITE, "activa": True}
            )

        grupo = self._grupo_revisores()

        email = os.environ.get("SUITE_ADMIN_EMAIL")
        if email and not Usuario.objects.filter(email=email.lower()).exists():
            clave, generada = _clave("SUITE_ADMIN_PASSWORD")
            Usuario.objects.create_superuser(email=email, password=clave, first_name="Administrador", organizacion=unab)
            self.stdout.write(
                f"Superusuario creado: {email}" + (f"  (contraseña generada: {clave})" if generada else "")
            )

        if demo:
            self._demo(unab, grupo)
        self.stdout.write(self.style.SUCCESS("Suite inicializada."))

    def _grupo_revisores(self):
        """Permisos mínimos del personal que revisa convalidaciones en el backoffice."""
        grupo, _ = Group.objects.get_or_create(name="Revisores de convalidación")
        codigos = [
            "view_solicitud",
            "change_solicitud",
            "view_item",
            "change_item",
            "view_equivalencia",
            "change_equivalencia",
            "add_equivalencia",
            "view_universidad",
            "view_carrera",
            "view_asignatura",
        ]
        grupo.permissions.set(Permission.objects.filter(codename__in=codigos))
        return grupo

    def _demo(self, unab, grupo):
        # Una segunda institución con licencia parcial: demuestra la venta por módulo.
        demo_org, _ = Organizacion.objects.update_or_create(
            slug="universidad-demo",
            defaults={"nombre": "Universidad Demo (licencia parcial)", "dominios_correo": "demo.cl", "activa": True},
        )
        for slug in ("malla", "convalidacion"):
            Licencia.objects.update_or_create(
                organizacion=demo_org,
                modulo=Modulo.objects.get(slug=slug),
                defaults={"plan": Licencia.Plan.PILOTO, "activa": True},
            )
        usuarios = [
            ("staff@unab.cl", "Paula", "Rojas", unab, Rol.STAFF, "SUITE_DEMO_STAFF_PASSWORD"),
            ("docente@unab.cl", "Jorge", "Sabattin", unab, Rol.DOCENTE, "SUITE_DEMO_DOCENTE_PASSWORD"),
            ("estudiante@unab.cl", "Camila", "Muñoz", unab, Rol.ESTUDIANTE, "SUITE_DEMO_ESTUDIANTE_PASSWORD"),
            ("staff@demo.cl", "Andrés", "Pérez", demo_org, Rol.STAFF, "SUITE_DEMO_STAFF_PASSWORD"),
        ]
        for email, nombre, apellido, org, rol, var in usuarios:
            if Usuario.objects.filter(email=email).exists():
                continue
            clave, generada = _clave(var)
            u = Usuario.objects.create_user(
                email=email,
                password=clave,
                first_name=nombre,
                last_name=apellido,
                organizacion=org,
                rol=rol,
                is_staff=rol == Rol.STAFF,
                correo_verificado=True,
            )
            if rol == Rol.STAFF:
                u.groups.add(grupo)
            self.stdout.write(f"  usuario demo {email} ({rol})" + (f"  contraseña: {clave}" if generada else ""))
