"""Backoffice de convalidaciones para la Dirección de Carrera / Servicio al Estudiante."""

from django.contrib import admin, messages
from django.utils import timezone

from catalogo.models import Carrera
from .models import Equivalencia, Item, Solicitud


class CarreraDestinoFilter(admin.SimpleListFilter):
    """Filtra las solicitudes por carrera de destino, limitada a carreras de UNAB.

    Por defecto Django listaría todas las carreras del catálogo; este filtro
    restringe las opciones a las carreras de destino de la propia institución
    (universidad.es_destino), que es lo que usa la Dirección de Carrera.
    """

    title = "carrera destino"
    parameter_name = "carrera_destino"

    def lookups(self, request, model_admin):
        return [
            (str(c.pk), str(c))
            for c in Carrera.objects.filter(universidad__es_destino=True, vigente=True)
            .select_related("universidad")
            .order_by("universidad__nombre", "nombre")
        ]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(carrera_destino__pk=self.value())
        return queryset


class ItemInline(admin.TabularInline):
    model = Item
    extra = 0
    fields = (
        "asignatura_origen_nombre",
        "nota",
        "aprobada_en_origen",
        "asignatura_destino",
        "puntaje",
        "estado_sugerido",
        "fuente_sugerencia",
        "decision",
        "asignatura_destino_final",
    )
    readonly_fields = (
        "asignatura_origen_nombre",
        "nota",
        "aprobada_en_origen",
        "asignatura_destino",
        "puntaje",
        "estado_sugerido",
        "fuente_sugerencia",
    )
    autocomplete_fields = ("asignatura_destino_final",)

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Solicitud)
class SolicitudAdmin(admin.ModelAdmin):
    list_display = (
        "folio",
        "nombres",
        "apellidos",
        "carrera_destino",
        "carrera_origen",
        "estado",
        "creada_en",
        "revisor",
    )
    list_filter = ("estado", CarreraDestinoFilter, "carrera_origen__universidad")
    search_fields = ("folio", "documento", "nombres", "apellidos", "correo")
    date_hierarchy = "creada_en"
    readonly_fields = (
        "folio",
        "tipo_documento",
        "documento",
        "nombres",
        "apellidos",
        "correo",
        "telefono",
        "consentimiento",
        "consentimiento_en",
        "carrera_destino",
        "carrera_origen",
        "institucion_origen_texto",
        "certificado_verificacion",
        "creada_en",
        "actualizada_en",
        "eliminar_desde",
    )
    fieldsets = (
        (
            "Postulante",
            {
                "fields": (
                    "folio",
                    "tipo_documento",
                    "documento",
                    "nombres",
                    "apellidos",
                    "correo",
                    "telefono",
                    "consentimiento",
                    "consentimiento_en",
                )
            },
        ),
        (
            "Contexto académico",
            {"fields": ("carrera_destino", "carrera_origen", "institucion_origen_texto", "certificado_verificacion")},
        ),
        (
            "Gestión",
            {"fields": ("estado", "revisor", "observaciones", "creada_en", "actualizada_en", "eliminar_desde")},
        ),
    )
    inlines = [ItemInline]
    actions = ["aceptar_sugerencias_convalidables"]

    def save_formset(self, request, form, formset, change):
        """Al aprobar un ítem con asignatura de catálogo, registra el precedente."""
        super().save_formset(request, form, formset, change)
        if formset.model is not Item:
            return
        for item in formset.queryset.filter(decision=Item.Decision.APROBADA):
            _registrar_precedente(item, request.user)
        sol = form.instance
        if not sol.revisor_id:
            sol.revisor = request.user
        if sol.estado == Solicitud.Estado.RECIBIDA:
            sol.estado = Solicitud.Estado.EN_REVISION
        sol.save(update_fields=["revisor", "estado"])

    @admin.action(description="Aceptar sugerencias 'Convalidable' (aprobadas en origen)")
    def aceptar_sugerencias_convalidables(self, request, queryset):
        n = 0
        for sol in queryset:
            for item in sol.items.filter(
                estado_sugerido=Item.Sugerencia.CONVALIDABLE,
                decision=Item.Decision.PENDIENTE,
                asignatura_destino__isnull=False,
            ).exclude(aprobada_en_origen=False):
                item.decision = Item.Decision.APROBADA
                item.asignatura_destino_final = item.asignatura_destino
                item.save(update_fields=["decision", "asignatura_destino_final"])
                _registrar_precedente(item, request.user)
                n += 1
            sol.revisor = sol.revisor or request.user
            sol.estado = Solicitud.Estado.EN_REVISION
            sol.save(update_fields=["revisor", "estado"])
        self.message_user(request, f"{n} ítems aprobados.", messages.SUCCESS)


def _registrar_precedente(item: Item, usuario):
    destino = item.asignatura_destino_final or item.asignatura_destino
    if not (item.asignatura_origen_id and destino):
        return
    Equivalencia.objects.update_or_create(
        origen_id=item.asignatura_origen_id,
        destino=destino,
        defaults={
            "estado": Equivalencia.Estado.APROBADA,
            "puntaje": item.puntaje,
            "decidida_por": usuario,
            "decidida_en": timezone.now(),
            "nota": f"Aprobada en solicitud {item.solicitud.folio}",
        },
    )


@admin.register(Equivalencia)
class EquivalenciaAdmin(admin.ModelAdmin):
    list_display = ("origen", "destino", "estado", "puntaje", "decidida_por", "decidida_en")
    list_filter = ("estado", "origen__carrera__universidad", "destino__carrera")
    search_fields = ("origen__nombre", "destino__nombre", "destino__codigo")
    autocomplete_fields = ("origen", "destino")
    actions = ["aprobar", "rechazar"]

    @admin.action(description="Aprobar equivalencias seleccionadas")
    def aprobar(self, request, queryset):
        n = queryset.update(estado=Equivalencia.Estado.APROBADA, decidida_por=request.user, decidida_en=timezone.now())
        self.message_user(request, f"{n} equivalencias aprobadas.")

    @admin.action(description="Rechazar equivalencias seleccionadas")
    def rechazar(self, request, queryset):
        n = queryset.update(estado=Equivalencia.Estado.RECHAZADA, decidida_por=request.user, decidida_en=timezone.now())
        self.message_user(request, f"{n} equivalencias rechazadas.")
