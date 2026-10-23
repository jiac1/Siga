import datetime

import pytest
from suite_sso import COOKIE_NAME, verificar_token

from identidad.models import EventoAuditoria, Licencia, Modulo, Organizacion

pytestmark = pytest.mark.django_db
CLAVE = "Clave-Segura-2026"


def ingresar(client, email="estudiante@unab.cl", password=CLAVE):
    return client.post(
        "/core/api/v1/auth/login", {"email": email, "password": password}, content_type="application/json"
    )


def test_login_api_emite_cookie_sso_con_modulos_del_rol(client, suite, crear_usuario):
    crear_usuario()
    r = ingresar(client)
    assert r.status_code == 200
    ident = verificar_token(r.cookies[COOKIE_NAME].value)
    assert ident.organizacion == "unab"
    assert "malla" in ident.modulos
    assert "mapa-calor" not in ident.modulos, "un estudiante no debe acceder a herramientas de gestión"
    assert r.cookies[COOKIE_NAME]["httponly"]


def test_staff_recibe_modulos_de_gestion(client, suite, crear_usuario):
    crear_usuario(email="staff@unab.cl", rol="staff")
    r = ingresar(client, "staff@unab.cl")
    assert {"mapa-calor", "estres-malla"} <= set(verificar_token(r.cookies[COOKIE_NAME].value).modulos)


def test_login_fallido_responde_401_y_audita(client, suite, crear_usuario):
    crear_usuario()
    assert ingresar(client, password="incorrecta").status_code == 401
    assert EventoAuditoria.objects.filter(accion="login_fallido").exists()


def test_institucion_inactiva_no_puede_ingresar(client, suite, crear_usuario):
    crear_usuario()
    Organizacion.objects.filter(slug="unab").update(activa=False)
    assert ingresar(client).status_code == 403


def test_licencia_vencida_retira_el_modulo(suite, crear_usuario):
    usuario = crear_usuario()
    Licencia.objects.filter(organizacion__slug="unab", modulo__slug="horarios").update(
        vigente_hasta=datetime.date(2020, 1, 1)
    )
    assert "horarios" not in {m.slug for m in usuario.modulos_habilitados()}


def test_institucion_con_licencia_parcial(suite, crear_usuario):
    from django.core.management import call_command

    call_command("inicializar_suite", "--demo", verbosity=0)
    usuario = crear_usuario(email="otro@demo.cl", rol="staff", org="universidad-demo")
    assert {m.slug for m in usuario.modulos_habilitados()} == {"malla", "convalidacion"}


def test_me_requiere_sesion_y_devuelve_modulos(client, suite, crear_usuario):
    assert client.get("/core/api/v1/auth/me").status_code in (401, 403)
    crear_usuario()
    ingresar(client)
    r = client.get("/core/api/v1/auth/me")
    assert r.status_code == 200 and "malla" in r.json()["modulos"]


def test_modulos_publicos_para_anonimos(client, suite):
    datos = {m["slug"]: m for m in client.get("/core/api/v1/modulos").json()}
    assert datos["convalidacion"]["habilitado"] is True
    assert datos["mapa-calor"]["habilitado"] is False
    assert len(datos) == Modulo.objects.count()


def test_login_html_redirige_solo_a_destinos_internos(client, suite, crear_usuario):
    crear_usuario()
    malicioso = "https://malicioso.example/robar"
    r = client.post(
        f"/core/ingresar/?next={malicioso}", {"email": "estudiante@unab.cl", "password": CLAVE, "next": malicioso}
    )
    assert r.status_code == 302 and r["Location"] == "/"


def test_logout_borra_cookie(client, suite, crear_usuario):
    crear_usuario()
    ingresar(client)
    r = client.get("/core/salir/")
    assert r.cookies[COOKIE_NAME].value == ""


def test_registro_exige_dominio_institucional(client, suite):
    r = client.post(
        "/core/registro/",
        {"first_name": "A", "last_name": "B", "email": "alguien@gmail.com", "password1": CLAVE, "password2": CLAVE},
    )
    assert r.status_code == 200 and "correo institucional" in r.content.decode()


def test_salud(client, db):
    r = client.get("/core/salud/")
    assert r.status_code == 200 and r.json()["bd"] == "ok"
