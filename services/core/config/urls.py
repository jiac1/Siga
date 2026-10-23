"""Rutas del servicio core. Todo cuelga de URL_PREFIX (por defecto 'core/')."""

from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView
from suite_sso.views import salud

from catalogo import views as catalogo
from convalidaciones import views as conval
from identidad.urls import api_urlpatterns as identidad_api

api_v1 = identidad_api + [
    path("catalogo/universidades", catalogo.UniversidadesOrigenView.as_view(), name="api-universidades"),
    path("catalogo/unab", catalogo.CarrerasUnabView.as_view(), name="api-unab"),
    path("catalogo/carreras/<slug:slug>", catalogo.CarreraDetalleView.as_view(), name="api-carrera"),
    path("convalidaciones/sugerencias", conval.SugerenciasView.as_view(), name="api-sugerencias"),
    path("convalidaciones/solicitudes", conval.SolicitudesView.as_view(), name="api-solicitudes"),
    path("convalidaciones/solicitudes/<str:folio>", conval.EstadoSolicitudView.as_view(), name="api-solicitud-estado"),
    path("esquema", SpectacularAPIView.as_view(), name="api-esquema"),
    path("docs", SpectacularRedocView.as_view(url_name="api-esquema"), name="api-docs"),
]

rutas = [
    path("", include("identidad.urls")),
    path("salud/", salud, name="salud"),
    path("admin/", admin.site.urls),
    path("api/v1/", include(api_v1)),
]

urlpatterns = [path(settings.URL_PREFIX, include(rutas))]
