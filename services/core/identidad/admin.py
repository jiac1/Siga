from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import EventoAuditoria, Licencia, Modulo, Organizacion, Usuario

admin.site.site_header = "SIGA-DSS · Administración"
admin.site.site_title = "SIGA-DSS"
admin.site.index_title = "Backoffice de la Suite"


class LicenciaInline(admin.TabularInline):
    model = Licencia
    extra = 0


@admin.register(Organizacion)
class OrganizacionAdmin(admin.ModelAdmin):
    list_display = ("nombre", "slug", "dominios_correo", "activa", "creada_en")
    list_filter = ("activa",)
    search_fields = ("nombre", "slug")
    prepopulated_fields = {"slug": ("nombre",)}
    inlines = [LicenciaInline]


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    ordering = ("email",)
    list_display = ("email", "first_name", "last_name", "organizacion", "rol", "is_active", "last_login")
    list_filter = ("rol", "organizacion", "is_active", "is_staff")
    search_fields = ("email", "first_name", "last_name")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Datos personales", {"fields": ("first_name", "last_name")}),
        ("Suite", {"fields": ("organizacion", "rol", "correo_verificado")}),
        ("Permisos", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Fechas", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("email", "organizacion", "rol", "password1", "password2")}),
    )


@admin.register(Modulo)
class ModuloAdmin(admin.ModelAdmin):
    list_display = ("nombre", "slug", "ruta", "tipo", "acceso_publico", "orden", "activo")
    list_editable = ("orden", "activo")
    list_filter = ("tipo", "activo")


@admin.register(Licencia)
class LicenciaAdmin(admin.ModelAdmin):
    list_display = ("organizacion", "modulo", "plan", "activa", "vigente_desde", "vigente_hasta")
    list_filter = ("plan", "activa", "modulo")


@admin.register(EventoAuditoria)
class EventoAuditoriaAdmin(admin.ModelAdmin):
    list_display = ("momento", "accion", "usuario", "ip")
    list_filter = ("accion",)
    search_fields = ("usuario__email", "accion")
    readonly_fields = [f.name for f in EventoAuditoria._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
