import os
from pathlib import Path

import pytest
from django.test import Client, override_settings

EJEMPLO = Path(__file__).resolve().parents[1] / "ejemplos" / "mapa_calor_prueba.xlsx"


@pytest.fixture
def client():
    return Client()


def test_salud_sin_base_de_datos(client):
    r = client.get("/salud/")
    assert r.status_code == 200 and r.json()["estado"] == "ok"


def test_home(client):
    assert client.get("/").status_code == 200


def test_procesa_excel_de_ejemplo_y_ofrece_descarga_sin_sesion(client):
    with EJEMPLO.open("rb") as f:
        r = client.post("/procesar/", {"archivo": f})
    html = r.content.decode()
    assert r.status_code == 200
    assert "data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64," in html
    assert "mapa_calor_prueba_heatmap.xlsx" in html


def test_rechaza_extension_invalida(client):
    from django.core.files.uploadedfile import SimpleUploadedFile
    r = client.post("/procesar/", {"archivo": SimpleUploadedFile("datos.csv", b"a,b")})
    assert "Solo se aceptan archivos .xlsx" in r.content.decode()


@override_settings(SUITE_MODE="suite")
def test_modo_suite_exige_sso(client):
    r = client.get("/")
    assert r.status_code == 302 and r["Location"].startswith("/core/ingresar/")


@override_settings(SUITE_MODE="suite")
def test_modo_suite_exige_licencia(client):
    from suite_sso import COOKIE_NAME, SuiteIdentity, emitir_token
    sin_licencia = emitir_token(SuiteIdentity(sub="1", email="e@unab.cl", nombre="E", organizacion="unab",
                                              roles=("estudiante",), modulos=("malla",)))
    client.cookies[COOKIE_NAME] = sin_licencia
    assert client.get("/").status_code == 403
    con_licencia = emitir_token(SuiteIdentity(sub="2", email="s@unab.cl", nombre="S", organizacion="unab",
                                              roles=("staff",), modulos=("mapa-calor",)))
    client.cookies[COOKIE_NAME] = con_licencia
    r = client.get("/")
    assert r.status_code == 200 and "Suite UNAB" in r.content.decode()
