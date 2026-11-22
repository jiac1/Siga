"""Datos iniciales de Estrés de Malla (reemplaza al antiguo seed.py).

  python manage.py inicializar_mallaiq            institución UNAB + carrera ICI
  python manage.py inicializar_mallaiq --demo     además usuarios locales (solo modo independiente)

Las contraseñas de los usuarios demo se leen de PASS_ADMIN / PASS_DOCENTE;
si no existen se generan y se muestran una única vez en consola.
"""
import os
import secrets

from django.core.management.base import BaseCommand

from accounts.models import Organization, User
from malla.models import Carrera


class Command(BaseCommand):
    help = "Crea la institución UNAB y la carrera de Ingeniería Civil Informática"

    def add_arguments(self, parser):
        parser.add_argument("--demo", action="store_true", help="Crea usuarios locales de demostración")

    def handle(self, *args, demo=False, **opts):
        org, _ = Organization.objects.get_or_create(
            slug="unab", defaults={"nombre": "Universidad Andrés Bello", "activa": True})
        carrera, creada = Carrera.objects.get_or_create(
            organization=org, codigo="UNAB12210",
            defaults={"nombre": "Ingeniería Civil en Informática", "campus": "Campus Antonio Varas",
                      "n_semestres": 10, "umbral_verde": 85, "umbral_amarillo": 70, "umbral_naranjo": 55})
        self.stdout.write(f"{'Creada' if creada else 'Ya existe'} carrera: {carrera}")

        if demo:
            for username, rol, var, nombre in [("admin", User.Rol.ORG_ADMIN, "PASS_ADMIN", "Admin"),
                                               ("jefe_carrera", User.Rol.DOCENTE, "PASS_DOCENTE", "Jefatura")]:
                if User.objects.filter(username=username).exists():
                    continue
                clave = os.environ.get(var) or secrets.token_urlsafe(12)
                User.objects.create_user(username=username, password=clave, first_name=nombre,
                                         organization=org, rol=rol, is_staff=rol == User.Rol.ORG_ADMIN)
                generada = "" if os.environ.get(var) else f"  (contraseña generada: {clave})"
                self.stdout.write(f"Usuario demo {username}{generada}")
        self.stdout.write(self.style.SUCCESS("Estrés de Malla inicializado."))
