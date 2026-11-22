import os

os.environ.setdefault("DEBUG", "True")
os.environ.setdefault("SUITE_SSO_SECRET", "pruebas-" + "x" * 40)

import pytest  # noqa: E402
from django.core.management import call_command  # noqa: E402


@pytest.fixture
def suite(db):
    """Módulos, institución UNAB, licencias y catálogo completo cargados."""
    call_command("inicializar_suite", verbosity=0)
    call_command("cargar_catalogo", verbosity=0)


@pytest.fixture
def crear_usuario(db):
    from identidad.models import Organizacion, Usuario

    def _crear(email="estudiante@unab.cl", rol="estudiante", org="unab", password="Clave-Segura-2026"):
        organizacion = Organizacion.objects.get(slug=org) if org else None
        return Usuario.objects.create_user(
            email=email, password=password, organizacion=organizacion, rol=rol, first_name="Prueba"
        )

    return _crear
