"""Modelos de persistencia para trabajos asíncronos de planificación global de campus."""

from __future__ import annotations

import uuid

from django.db import models


class TrabajoPlanificacionCampus(models.Model):
    """Registra la ejecución asíncrona (batch/correo) de una tabla maestra de campus."""

    ESTADO_PENDIENTE = "pendiente"
    ESTADO_EN_PROCESO = "en_proceso"
    ESTADO_COMPLETADO = "completado"
    ESTADO_ERROR = "error"
    ESTADOS = [
        (ESTADO_PENDIENTE, "Pendiente"),
        (ESTADO_EN_PROCESO, "En proceso"),
        (ESTADO_COMPLETADO, "Completado"),
        (ESTADO_ERROR, "Error"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    estado = models.CharField(max_length=20, choices=ESTADOS, default=ESTADO_PENDIENTE)
    email_notificacion = models.EmailField(blank=True, default="")
    presupuesto_segundos = models.FloatField(default=60.0)
    total_clases = models.IntegerField(default=0)
    clases_asignadas = models.IntegerField(default=0)
    conflictos_h2 = models.IntegerField(default=0)
    conflictos_h3 = models.IntegerField(default=0)
    conflictos_estudiantes = models.IntegerField(default=0)
    tiempo_ms = models.FloatField(default=0.0)
    resultado = models.JSONField(default=dict, blank=True)
    error_detalle = models.TextField(blank=True, default="")
    creado_en = models.DateTimeField(auto_now_add=True)
    completado_en = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-creado_en"]
