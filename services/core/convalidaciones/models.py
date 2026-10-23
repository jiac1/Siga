"""Solicitudes de convalidación y base de conocimiento de equivalencias.

Flujo: el postulante evalúa sus asignaturas en la app (cliente) y, con su
consentimiento, envía la solicitud. El personal de la Dirección de Carrera
la revisa ítem por ítem. Cada decisión aprobada alimenta la tabla de
Equivalencias, que pasa a ser el primer criterio para futuros postulantes
(precedentes), por sobre la similitud automática.
"""

import secrets

from django.conf import settings
from django.db import models

from catalogo.models import Asignatura, Carrera


def _nuevo_folio() -> str:
    return "CV-" + secrets.token_hex(4).upper()


class Solicitud(models.Model):
    class Estado(models.TextChoices):
        RECIBIDA = "recibida", "Recibida"
        EN_REVISION = "en_revision", "En revisión"
        RESUELTA = "resuelta", "Resuelta"
        DESCARTADA = "descartada", "Descartada"

    class TipoDocumento(models.TextChoices):
        RUT = "rut", "RUT"
        PASAPORTE = "pasaporte", "Pasaporte"

    folio = models.CharField(max_length=16, unique=True, default=_nuevo_folio, editable=False)
    estado = models.CharField(max_length=12, choices=Estado.choices, default=Estado.RECIBIDA, db_index=True)
    # Postulante (datos personales: Ley 19.628 / Ley 21.719 — finalidad única: gestionar la solicitud)
    tipo_documento = models.CharField(max_length=10, choices=TipoDocumento.choices)
    documento = models.CharField(max_length=20)
    nombres = models.CharField(max_length=120)
    apellidos = models.CharField(max_length=120)
    correo = models.EmailField()
    telefono = models.CharField(max_length=20, blank=True)
    consentimiento = models.BooleanField()
    consentimiento_en = models.DateTimeField()
    # Contexto académico
    carrera_destino = models.ForeignKey(Carrera, on_delete=models.PROTECT, related_name="solicitudes_destino")
    carrera_origen = models.ForeignKey(
        Carrera, null=True, blank=True, on_delete=models.SET_NULL, related_name="solicitudes_origen"
    )
    institucion_origen_texto = models.CharField(
        max_length=200, blank=True, help_text="Si la universidad de origen no está en el catálogo"
    )
    certificado_verificacion = models.JSONField(
        default=dict, blank=True, help_text="Resultado del triaje del certificado de notas (cliente)"
    )
    # Gestión
    creada_en = models.DateTimeField(auto_now_add=True, db_index=True)
    actualizada_en = models.DateTimeField(auto_now=True)
    revisor = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="solicitudes_revisadas"
    )
    observaciones = models.TextField(blank=True)
    eliminar_desde = models.DateField(
        null=True, blank=True, help_text="Fecha a partir de la cual los datos personales deben eliminarse"
    )

    class Meta:
        verbose_name = "solicitud de convalidación"
        verbose_name_plural = "solicitudes de convalidación"
        ordering = ["-creada_en"]

    def __str__(self):
        return f"{self.folio} · {self.nombres} {self.apellidos}"

    @property
    def resumen(self) -> dict:
        items = list(self.items.all())
        return {
            "total": len(items),
            "convalidables": sum(i.estado_sugerido == Item.Sugerencia.CONVALIDABLE for i in items),
            "aprobados": sum(i.decision == Item.Decision.APROBADA for i in items),
            "pendientes": sum(i.decision == Item.Decision.PENDIENTE for i in items),
        }


class Item(models.Model):
    """Una asignatura cursada en origen dentro de una solicitud."""

    class Sugerencia(models.TextChoices):
        CONVALIDABLE = "convalidable", "Convalidable"
        REVISION = "revision", "Revisión manual"
        SIN_COINCIDENCIA = "sin_coincidencia", "Sin coincidencia"
        NO_APROBADA = "no_aprobada", "No aprobada en origen"

    class Decision(models.TextChoices):
        PENDIENTE = "pendiente", "Pendiente"
        APROBADA = "aprobada", "Convalidación aprobada"
        RECHAZADA = "rechazada", "Rechazada"

    solicitud = models.ForeignKey(Solicitud, on_delete=models.CASCADE, related_name="items")
    asignatura_origen_nombre = models.CharField(max_length=250)
    asignatura_origen = models.ForeignKey(
        Asignatura,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="Si se identificó en el catálogo",
    )
    nota = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    aprobada_en_origen = models.BooleanField(null=True)
    asignatura_destino = models.ForeignKey(
        Asignatura,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name="asignatura UNAB sugerida",
    )
    puntaje = models.FloatField(null=True, blank=True)
    estado_sugerido = models.CharField(max_length=20, choices=Sugerencia.choices, default=Sugerencia.REVISION)
    fuente_sugerencia = models.CharField(
        max_length=12, default="motor", help_text="motor (similitud) o precedente (equivalencia aprobada)"
    )
    decision = models.CharField(max_length=10, choices=Decision.choices, default=Decision.PENDIENTE)
    asignatura_destino_final = models.ForeignKey(
        Asignatura,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name="asignatura UNAB resuelta",
    )

    class Meta:
        verbose_name = "ítem de solicitud"
        verbose_name_plural = "ítems de solicitud"

    def __str__(self):
        return self.asignatura_origen_nombre


class Equivalencia(models.Model):
    """Precedente: asignatura de origen ↔ asignatura UNAB, validado por personal."""

    class Estado(models.TextChoices):
        SUGERIDA = "sugerida", "Sugerida por el motor"
        APROBADA = "aprobada", "Aprobada"
        RECHAZADA = "rechazada", "Rechazada"

    origen = models.ForeignKey(Asignatura, on_delete=models.CASCADE, related_name="equivalencias_como_origen")
    destino = models.ForeignKey(Asignatura, on_delete=models.CASCADE, related_name="equivalencias_como_destino")
    estado = models.CharField(max_length=10, choices=Estado.choices, default=Estado.SUGERIDA, db_index=True)
    puntaje = models.FloatField(null=True, blank=True)
    decidida_por = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    decidida_en = models.DateTimeField(null=True, blank=True)
    nota = models.CharField(max_length=300, blank=True)

    class Meta:
        verbose_name = "equivalencia"
        verbose_name_plural = "equivalencias (precedentes)"
        unique_together = [("origen", "destino")]
        ordering = ["origen__carrera", "origen__semestre"]

    def __str__(self):
        return f"{self.origen} → {self.destino} ({self.get_estado_display()})"
