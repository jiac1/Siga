from django.contrib import admin

from .models import Asignatura, Carrera, Universidad


@admin.register(Universidad)
class UniversidadAdmin(admin.ModelAdmin):
    list_display = ("nombre", "sigla", "region", "es_destino")
    list_filter = ("es_destino",)
    search_fields = ("nombre", "sigla")


class AsignaturaInline(admin.TabularInline):
    model = Asignatura
    extra = 0
    fields = ("semestre", "codigo", "nombre", "creditos", "generica", "semestre_incierto")


@admin.register(Carrera)
class CarreraAdmin(admin.ModelAdmin):
    list_display = ("nombre", "universidad", "area", "plan", "duracion", "vigente", "fuente_consultada")
    list_filter = ("universidad", "area", "vigente")
    search_fields = ("nombre", "slug", "universidad__nombre")
    inlines = [AsignaturaInline]


@admin.register(Asignatura)
class AsignaturaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "codigo", "semestre", "creditos", "carrera", "generica")
    list_filter = ("carrera__universidad", "generica")
    search_fields = ("nombre", "codigo", "carrera__nombre")
