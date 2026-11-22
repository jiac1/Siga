from django.conf import settings
from django.urls import include, path
from suite_sso.views import salud

rutas = [
    path('salud/', salud, name='salud'),
    path('', include('heatmap.urls')),
]

# El ALB de AWS no reescribe rutas: el servicio responde bajo su prefijo.
urlpatterns = [path(settings.URL_PREFIX, include(rutas))]
