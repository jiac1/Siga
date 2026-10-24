from django.conf import settings
from django.templatetags.static import static


def navegacion(request):
    """Datos comunes del layout.

    `sidebar_carreras` lo usaba base.html desde el prototipo, pero ninguna
    vista lo entregaba: la barra lateral nunca listaba las carreras.
    """
    usuario = getattr(request, "user", None)
    carreras = []
    if usuario is not None and usuario.is_authenticated and getattr(usuario, "organization_id", None):
        from .models import Carrera
        carreras = Carrera.objects.filter(organization_id=usuario.organization_id, activa=True).only("pk", "nombre")
    en_suite = getattr(settings, "SUITE_MODE", "standalone") == "suite"
    return {
        "sidebar_carreras": carreras,
        "mallas_base_url": settings.SUITE_MALLAS_URL if en_suite else static("mallas/"),
    }
