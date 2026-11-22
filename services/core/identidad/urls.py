from django.urls import path

from . import views

app_name = "identidad"

urlpatterns = [
    path("ingresar/", views.ingresar, name="ingresar"),
    path("salir/", views.salir, name="salir"),
    path("registro/", views.registro, name="registro"),
    path("verificar/<str:token>/", views.verificar, name="verificar"),
]

api_urlpatterns = [
    path("auth/login", views.LoginApiView.as_view(), name="api-login"),
    path("auth/logout", views.LogoutApiView.as_view(), name="api-logout"),
    path("auth/me", views.MeView.as_view(), name="api-me"),
    path("modulos", views.ModulosView.as_view(), name="api-modulos"),
]
