import pytest

from catalogo.models import Asignatura, Carrera
from convalidaciones.models import Equivalencia, Item, Solicitud
from convalidaciones.views import rut_valido

pytestmark = pytest.mark.django_db
DESTINO = "unab-ingenieria-civil-informatica"
API = "/core/api/v1/convalidaciones"


def postulante(**extra):
    datos = {
        "tipo_documento": "rut",
        "documento": "11.111.111-1",
        "nombres": "María",
        "apellidos": "Pérez",
        "correo": "maria@example.com",
        "consentimiento": True,
        "carrera_destino": DESTINO,
        "carrera_origen": "usach-civil-informatica",
        "asignaturas": [
            {"nombre": "Cálculo I para Ingeniería", "nota": "5.5", "aprobada": True},
            {"nombre": "Diseño de Bases de Datos", "nota": "3.2", "aprobada": False},
            {"nombre": "Procesamiento de Señales e Imágenes"},
        ],
    }
    datos.update(extra)
    return datos


@pytest.mark.parametrize(
    "rut,ok", [("11.111.111-1", True), ("12.345.678-5", True), ("12.345.678-9", False), ("1-9", False)]
)
def test_rut(rut, ok):
    assert rut_valido(rut) is ok


def test_catalogo_publico(client, suite):
    unis = client.get("/core/api/v1/catalogo/universidades").json()
    assert len(unis) >= 10
    malla = client.get("/core/api/v1/catalogo/carreras/uchile-civil-computacion").json()
    assert malla["sigla"] == "UCHILE" and malla["fuente"]["url"].startswith("https://")
    assert sum(len(s["asignaturas"]) for s in malla["semestres"]) > 40


def test_sugerencias_reconocen_equivalencias_evidentes(client, suite):
    r = client.post(
        f"{API}/sugerencias",
        {
            "carrera_destino": DESTINO,
            "asignaturas": [
                {"nombre": "Cálculo I para Ingeniería"},
                {"nombre": "Inglés II"},
                {"nombre": "Procesamiento de Señales e Imágenes"},
            ],
        },
        content_type="application/json",
    )
    assert r.status_code == 200
    res = r.json()["resultados"]
    assert res[0]["mejor"]["codigo"] == "FMMP112" and res[0]["mejor"]["estado"] == "convalidable"
    assert res[1]["mejor"]["codigo"] == "ING129", "debe respetar el nivel (Inglés II no es Inglés I)"
    assert res[2]["mejor"]["estado"] != "convalidable"


def test_solicitud_se_registra_y_recalcula_en_servidor(client, suite, mailoutbox):
    r = client.post(f"{API}/solicitudes", postulante(), content_type="application/json")
    assert r.status_code == 201, r.content
    sol = Solicitud.objects.get(folio=r.json()["folio"])
    estados = {i.asignatura_origen_nombre: i.estado_sugerido for i in sol.items.all()}
    assert estados["Cálculo I para Ingeniería"] == Item.Sugerencia.CONVALIDABLE
    assert estados["Diseño de Bases de Datos"] == Item.Sugerencia.NO_APROBADA
    assert sol.eliminar_desde is not None, "debe quedar fijada la fecha de retención de datos personales"
    assert len(mailoutbox) == 1 and sol.folio in mailoutbox[0].subject


def test_solicitud_sin_consentimiento_o_rut_invalido_es_rechazada(client, suite):
    assert (
        client.post(f"{API}/solicitudes", postulante(consentimiento=False), content_type="application/json").status_code
        == 400
    )
    assert (
        client.post(
            f"{API}/solicitudes", postulante(documento="12.345.678-9"), content_type="application/json"
        ).status_code
        == 400
    )


def test_estado_solo_con_correo_correcto(client, suite):
    folio = client.post(f"{API}/solicitudes", postulante(), content_type="application/json").json()["folio"]
    assert client.get(f"{API}/solicitudes/{folio}?correo=otro@x.cl").status_code == 404
    r = client.get(f"{API}/solicitudes/{folio}?correo=maria@example.com")
    assert r.status_code == 200 and r.json()["resumen"]["total"] == 3


def test_precedente_aprobado_tiene_prioridad(client, suite):
    destino = Carrera.objects.get(slug=DESTINO)
    origen = Asignatura.objects.get(carrera__slug="usach-civil-informatica", nombre="Modelos y Simulación")
    unab = Asignatura.objects.get(carrera=destino, codigo="CINF105")
    Equivalencia.objects.create(origen=origen, destino=unab, estado=Equivalencia.Estado.APROBADA)
    r = client.post(
        f"{API}/sugerencias",
        {"carrera_destino": DESTINO, "asignaturas": [{"nombre": origen.nombre, "asignatura_origen_id": origen.pk}]},
        content_type="application/json",
    )
    mejor = r.json()["resultados"][0]["mejor"]
    assert mejor["codigo"] == "CINF105" and mejor["fuente"] == "precedente"


def test_recarga_de_catalogo_no_destruye_precedentes(suite):
    from django.core.management import call_command

    origen = Asignatura.objects.get(carrera__slug="usach-civil-informatica", nombre="Ciberseguridad")
    unab = Asignatura.objects.get(carrera__slug=DESTINO, codigo="PTEC107")
    eq = Equivalencia.objects.create(origen=origen, destino=unab, estado=Equivalencia.Estado.APROBADA)
    call_command("cargar_catalogo", verbosity=0)
    assert Equivalencia.objects.filter(pk=eq.pk).exists()


def test_purga_anonimiza_solicitudes_vencidas(client, suite):
    import datetime

    from django.core.management import call_command

    folio = client.post(f"{API}/solicitudes", postulante(), content_type="application/json").json()["folio"]
    Solicitud.objects.filter(folio=folio).update(eliminar_desde=datetime.date(2020, 1, 1))
    call_command("purgar_datos_vencidos", verbosity=0)
    sol = Solicitud.objects.get(folio=folio)
    assert sol.nombres == "anonimizado" and "maria" not in sol.correo
    assert sol.items.count() == 3, "los datos académicos se conservan"
