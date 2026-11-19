"""Configuración de la aplicación Django para optimización horaria UCTP."""

from django.apps import AppConfig


class HorariosConfig(AppConfig):
    """Registra el módulo de optimización combinatoria de horarios."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "horarios"
    verbose_name = "Optimización Horaria (UCTP)"
