"""Pruebas unitarias e integración para el solver global de asignación de campus."""

import pytest
from django.core import mail
from suite_sso import COOKIE_NAME, SuiteIdentity, emitir_token

from horarios.campus import (
    CandidatoSala,
    CandidatoTemporal,
    ClaseCampus,
    RestriccionDistribucion,
    SalaCampus,
    construir_campus_desde_secciones,
    resolver_campus_aleatorio,
    resolver_campus_global,
)
from horarios.motor import BloqueHorario, SeccionNRC


def test_campus_global_evita_colisiones_sala_docente_y_capacidad():
    """Garantiza H2=0, H3=0 y respeto estricto de capacidad física de salas."""
    salas = [
        SalaCampus("S101", capacidad=30),
        SalaCampus("S202", capacidad=60),
    ]
    t1 = CandidatoTemporal(slots=(("Lunes", 1), ("Lunes", 2)), penalizacion=0)
    t2 = CandidatoTemporal(slots=(("Martes", 1), ("Martes", 2)), penalizacion=2)

    clases = [
        ClaseCampus(
            id_clase="C1",
            curso="INF101",
            cupo=50,
            docente="PROF-A",
            candidatos_tiempo=(t1, t2),
            candidatos_sala=(CandidatoSala("S101", 0), CandidatoSala("S202", 1)),
        ),
        ClaseCampus(
            id_clase="C2",
            curso="INF102",
            cupo=25,
            docente="PROF-A",
            candidatos_tiempo=(t1, t2),
            candidatos_sala=(CandidatoSala("S101", 0), CandidatoSala("S202", 0)),
        ),
        ClaseCampus(
            id_clase="C3",
            curso="MAT101",
            cupo=25,
            docente="PROF-B",
            candidatos_tiempo=(t1, t2),
            candidatos_sala=(CandidatoSala("S101", 0), CandidatoSala("S202", 0)),
        ),
    ]

    res = resolver_campus_global(
        clases,
        salas,
        perfiles_estudiantes=[["INF101", "MAT101"]],
        iteraciones=500,
    )

    assert res.metricas.clases_asignadas == 3
    assert res.metricas.conflictos_sala_h2 == 0
    assert res.metricas.conflictos_docente_h3 == 0
    assert res.metricas.conflictos_capacidad == 0

    asig_c1 = next(a for a in res.asignaciones if a.id_clase == "C1")
    assert asig_c1.id_sala == "S202"


def test_campus_global_respeta_not_overlap_y_supera_aleatorio():
    """Respeta restricciones NotOverlap y reduce penalización/conflictos frente a aleatorio."""
    salas = [SalaCampus("S1", 40), SalaCampus("S2", 40)]
    patrones = (
        CandidatoTemporal(slots=(("Lunes", 1), ("Lunes", 2)), penalizacion=0),
        CandidatoTemporal(slots=(("Miércoles", 3), ("Miércoles", 4)), penalizacion=1),
        CandidatoTemporal(slots=(("Jueves", 5), ("Jueves", 6)), penalizacion=5),
    )
    clases = [
        ClaseCampus(
            id_clase=f"CL-{i}",
            curso=f"CUR-{i}",
            cupo=30,
            docente=f"DOC-{i % 2}",
            candidatos_tiempo=patrones,
            candidatos_sala=(CandidatoSala("S1", 0), CandidatoSala("S2", 2)),
        )
        for i in range(4)
    ]
    restricciones = (RestriccionDistribucion(tipo="NotOverlap", clases=("CL-0", "CL-2"), requerida=True),)
    perfiles = [["CUR-0", "CUR-1"], ["CUR-2", "CUR-3"]]

    base = resolver_campus_aleatorio(clases, salas, perfiles_estudiantes=perfiles, restricciones=restricciones)
    opt = resolver_campus_global(
        clases, salas, perfiles_estudiantes=perfiles, restricciones=restricciones, iteraciones=1_000
    )

    assert opt.metricas.clases_asignadas == 4
    assert opt.metricas.conflictos_sala_h2 == 0
    assert opt.metricas.conflictos_docente_h3 == 0
    assert opt.metricas.conflictos_distribucion_dura == 0
    assert opt.metricas.penalizacion_total <= base.metricas.penalizacion_total


def test_construir_campus_desde_secciones_resuelve_choques_banner():
    """Convierte secciones Banner con choques H2/H3 en una programación global libre de conflictos."""
    secciones = [
        SeccionNRC(
            nrc="1001",
            curso="TDFI102",
            actividad="TEO",
            bloques=(BloqueHorario("Lunes", 1, sala="A101", edificio="C1"),),
            cupos=35,
            rut_docente="11.111.111-1",
        ),
        SeccionNRC(
            nrc="1002",
            curso="FMMP012",
            actividad="TEO",
            bloques=(BloqueHorario("Lunes", 1, sala="A101", edificio="C1"),),
            cupos=35,
            rut_docente="11.111.111-1",
        ),
    ]
    salas = [SalaCampus("A101", 45), SalaCampus("A102", 45)]
    clases = construir_campus_desde_secciones(secciones, salas)
    res = resolver_campus_global(clases, salas, iteraciones=300)

    assert res.metricas.clases_asignadas == 2
    assert res.metricas.conflictos_sala_h2 == 0
    assert res.metricas.conflictos_docente_h3 == 0
    assert res.metricas.conflictos_capacidad == 0


@pytest.mark.django_db
def test_api_planificar_campus_genera_tabla_y_envia_correo(client, suite, crear_usuario):
    """El endpoint de planificación global resuelve choques, persiste trabajo y envía correo."""
    payload = {
        "presupuesto_segundos": 5.0,
        "iteraciones": 300,
        "email_notificacion": "coordinacion@unab.cl",
        "ejecucion_sincrona": True,
        "salas": [
            {"id_sala": "A101", "capacidad": 45, "edificio": "C1"},
            {"id_sala": "A102", "capacidad": 45, "edificio": "C1"},
        ],
        "secciones": [
            {
                "nrc": "1001",
                "curso": "TDFI102",
                "actividad": "TEO",
                "cupos": 35,
                "rut_docente": "11.111.111-1",
                "bloques": [{"dia": "Lunes", "modulo": 1, "sala": "A101", "edificio": "C1"}],
            },
            {
                "nrc": "1002",
                "curso": "FMMP012",
                "actividad": "TEO",
                "cupos": 35,
                "rut_docente": "11.111.111-1",
                "bloques": [{"dia": "Lunes", "modulo": 1, "sala": "A101", "edificio": "C1"}],
            },
        ],
    }

    r_anon = client.post("/core/api/v1/horarios/campus/planificar", payload, content_type="application/json")
    assert r_anon.status_code in (401, 403)

    usuario = crear_usuario()
    client.cookies[COOKIE_NAME] = emitir_token(
        SuiteIdentity(
            sub=str(usuario.pk),
            email=usuario.email,
            nombre=usuario.nombre_visible,
            organizacion="unab",
            roles=("director",),
            modulos=("horarios",),
        )
    )

    r = client.post("/core/api/v1/horarios/campus/planificar", payload, content_type="application/json")
    assert r.status_code == 200, r.content
    data = r.json()
    assert data["estado"] == "completado"
    assert data["clases_asignadas"] == 2
    assert data["conflictos_h2"] == 0
    assert data["conflictos_h3"] == 0

    assert len(mail.outbox) == 1
    assert "coordinacion@unab.cl" in mail.outbox[0].to
    assert "2/2" in mail.outbox[0].subject

    r_get = client.get(f"/core/api/v1/horarios/campus/trabajos/{data['trabajo_id']}")
    assert r_get.status_code == 200
    assert r_get.json()["estado"] == "completado"
