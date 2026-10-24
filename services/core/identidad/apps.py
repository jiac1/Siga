from django.apps import AppConfig


class IdentidadConfig(AppConfig):
    name = "identidad"
    verbose_name = "Identidad y licencias"

    def ready(self):
        from . import esquema  # noqa: F401  (registra la extensión OpenAPI)
