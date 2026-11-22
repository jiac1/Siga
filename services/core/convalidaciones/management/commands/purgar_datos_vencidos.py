"""Anonimiza los datos personales de solicitudes cuyo plazo de retención venció (RN-06).

Se conservan los datos académicos (asignaturas, decisiones, precedentes) porque
no identifican a la persona y alimentan la base de equivalencias.
Programar diariamente (en AWS: tarea programada de ECS con EventBridge).

  python manage.py purgar_datos_vencidos [--simular]
"""

from django.core.management.base import BaseCommand
from django.utils import timezone

from convalidaciones.models import Solicitud
from identidad.models import EventoAuditoria

ANONIMO = "anonimizado"


class Command(BaseCommand):
    help = "Anonimiza datos personales de solicitudes con retención vencida"

    def add_arguments(self, parser):
        parser.add_argument("--simular", action="store_true", help="Solo informa cuántas se anonimizarían")

    def handle(self, *args, simular=False, **opts):
        vencidas = Solicitud.objects.filter(eliminar_desde__lte=timezone.localdate()).exclude(nombres=ANONIMO)
        total = vencidas.count()
        if simular:
            self.stdout.write(f"{total} solicitudes con retención vencida (simulación, sin cambios).")
            return
        for sol in vencidas:
            sol.documento = f"ANON-{sol.pk}"
            sol.nombres = ANONIMO
            sol.apellidos = ANONIMO
            sol.correo = f"anonimizado+{sol.pk}@invalid.local"
            sol.telefono = ""
            sol.certificado_verificacion = {}
            sol.save(
                update_fields=["documento", "nombres", "apellidos", "correo", "telefono", "certificado_verificacion"]
            )
        if total:
            EventoAuditoria.objects.create(accion="purga_datos_personales", detalle={"solicitudes": total})
        self.stdout.write(self.style.SUCCESS(f"{total} solicitudes anonimizadas."))
