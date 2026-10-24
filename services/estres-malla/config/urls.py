"""config/urls.py — el servicio responde bajo URL_PREFIX (el ALB no reescribe rutas)."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from suite_sso.views import salud

rutas = [
    path("salud/", salud, name="salud"),
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("", include("malla.urls")),
]

urlpatterns = [path(settings.URL_PREFIX, include(rutas))]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
