from pathlib import Path

import pytest
from django.core.management import call_command
from django.test import override_settings
from suite_sso import COOKIE_NAME, SuiteIdentity, emitir_token

from accounts.models import Organization, User
from malla.models import AnalisisMalla, Carrera

pytestmark = pytest.mark.django_db
EJEMPLOS = Path(__file__).resolve().parents[1] / "ejemplos"
CLAVE = "clave-de-prueba-123"


@pytest.fixture
def carrera():
    call_command("inicializar_mallaiq", verbosity=0)
    return Carrera.objects.get(codigo="UNAB12210")


@pytest.fixture
def docente(carrera):
    return User.objects.create_user(username="docente", password=CLAVE, organization=carrera.organization,
                                    rol=User.Rol.DOCENTE)


def test_salud(client):
    r = client.get("/salud/")
    assert r.status_code == 200 and r.json()["bd"] == "ok"


def test_login_local_y_dashboard_lista_carreras_en_sidebar(client, docente):
    r = client.post("/accounts/login/", {"username": "docente", "password": CLAVE})
    assert r.status_code == 302
    html = client.get("/").content.decode()
    assert "Ingeniería Civil en Informática" in html


def test_login_no_redirige_a_sitios_externos(client, docente):
    r = client.post("/accounts/login/?next=https://malicioso.example", {"username": "docente", "password": CLAVE})
    assert r["Location"] == "/"


def test_analisis_completo_con_archivos_de_ejemplo(client, docente, carrera):
    client.force_login(docente)
    with (EJEMPLOS / "malla.xlsx").open("rb") as m, (EJEMPLOS / "actas.xlsx").open("rb") as a:
        r = client.post(f"/carrera/{carrera.pk}/subir/",
                        {"archivo_malla": m, "archivo_actas": a, "periodo": "202510"})
    assert r.status_code == 302, r.content[:500]
    analisis = AnalisisMalla.objects.get()
    assert analisis.estado == AnalisisMalla.Estado.LISTO and analisis.n_asignaturas > 0
    assert client.get(f"/analisis/{analisis.pk}/").status_code == 200
    assert client.get(f"/analisis/{analisis.pk}/api/").json()["n_asignaturas"] == analisis.n_asignaturas


def test_analisis_con_malla_del_catalogo(client, docente, carrera):
    client.force_login(docente)
    with (EJEMPLOS / "actas.xlsx").open("rb") as a:
        r = client.post(f"/carrera/{carrera.pk}/subir/",
                        {"malla_slug": "civil-informatica", "archivo_actas": a, "periodo": "202510"})
    assert r.status_code == 302
    assert AnalisisMalla.objects.get().malla_catalogo_slug == "civil-informatica"


def test_aislamiento_entre_instituciones(client, docente, carrera):
    otra = Organization.objects.create(nombre="Otra U", slug="otra")
    intruso = User.objects.create_user(username="intruso", password=CLAVE, organization=otra, rol=User.Rol.DOCENTE)
    client.force_login(intruso)
    assert client.get(f"/carrera/{carrera.pk}/").status_code == 404


@override_settings(SUITE_MODE="suite")
def test_modo_suite_aprovisiona_usuario_e_institucion(client, carrera):
    token = emitir_token(SuiteIdentity(sub="9", email="paula@unab.cl", nombre="Paula Rojas", organizacion="unab",
                                       organizacion_nombre="Universidad Andrés Bello",
                                       roles=("staff",), modulos=("estres-malla",)))
    client.cookies[COOKIE_NAME] = token
    r = client.get("/")
    assert r.status_code == 200
    u = User.objects.get(username="paula@unab.cl")
    assert u.organization.slug == "unab" and u.rol == User.Rol.DOCENTE and not u.has_usable_password()
    assert 'id="suite-bar"' in r.content.decode()


@override_settings(SUITE_MODE="suite")
def test_modo_suite_sin_cookie_redirige_a_core(client):
    r = client.get("/")
    assert r.status_code == 302 and r["Location"].startswith("/core/ingresar/")


@override_settings(SUITE_MODE="suite")
def test_modo_suite_actualiza_rol_si_cambia_en_sso(client, carrera):
    # Primera entrada como staff/docente
    token1 = emitir_token(SuiteIdentity(sub="10", email="carlos@unab.cl", nombre="Carlos Soto", organizacion="unab",
                                        roles=("staff",), modulos=("estres-malla",)))
    client.cookies[COOKIE_NAME] = token1
    r1 = client.get("/")
    assert r1.status_code == 200
    u = User.objects.get(username="carlos@unab.cl")
    assert u.rol == User.Rol.DOCENTE

    # Segunda entrada con rol promovido a admin_institucion
    token2 = emitir_token(SuiteIdentity(sub="10", email="carlos@unab.cl", nombre="Carlos Soto", organizacion="unab",
                                        roles=("admin_institucion",), modulos=("estres-malla",)))
    client.cookies[COOKIE_NAME] = token2
    r2 = client.get("/")
    assert r2.status_code == 200
    u.refresh_from_db()
    assert u.rol == User.Rol.ORG_ADMIN


def test_calcular_metricas_grafo_curricular_analytics():
    import pandas as pd
    from malla.engine import calcular_metricas_grafo

    # Cadena A101 -> B201 -> C301 y rama paralela B201 -> D302, más nodo aislado E101
    df = pd.DataFrame([
        {"codigo": "MAT101", "prerrequisitos": "—"},
        {"codigo": "MAT201", "prerrequisitos": "MAT101"},
        {"codigo": "INF301", "prerrequisitos": "MAT201"},
        {"codigo": "INF302", "prerrequisitos": "MAT201"},
        {"codigo": "HUM101", "prerrequisitos": "—"},
    ])
    res = calcular_metricas_grafo(df)
    assert res["tiene_ciclos"] is False
    assert res["n_aristas"] == 3
    # MAT101 bloquea 3 cursos (MAT201, INF301, INF302) y está en camino de largo 3 -> c = 6
    assert res["por_codigo"]["MAT101"] == {"factor_bloqueo": 3, "factor_retraso": 3, "complejidad": 6}
    # MAT201 bloquea 2 cursos y está en camino de largo 3 -> c = 5
    assert res["por_codigo"]["MAT201"] == {"factor_bloqueo": 2, "factor_retraso": 3, "complejidad": 5}
    # HUM101 aislado -> b = 0, d = 1, c = 1
    assert res["por_codigo"]["HUM101"] == {"factor_bloqueo": 0, "factor_retraso": 1, "complejidad": 1}


def test_calcular_metricas_grafo_detecta_ciclo():
    import pandas as pd
    from malla.engine import calcular_metricas_grafo

    df = pd.DataFrame([
        {"codigo": "INF101", "prerrequisitos": "INF102"},
        {"codigo": "INF102", "prerrequisitos": "INF101"},
    ])
    assert calcular_metricas_grafo(df)["tiene_ciclos"] is True

