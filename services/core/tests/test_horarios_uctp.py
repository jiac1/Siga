"""Pruebas unitarias y de integración del motor de optimización horaria (UCTP)."""

from __future__ import annotations

import itertools

import pytest
from suite_sso import COOKIE_NAME, SuiteIdentity, emitir_token

from horarios.motor import (
    BloqueHorario,
    PreferenciasUCTP,
    SeccionNRC,
    auditar_conflictos_oferta,
    evaluar_slots,
    opciones_por_curso,
    optimizar_horarios,
    resolver_branch_and_bound,
    resolver_recocido_simulado,
    vacantes_sin_tope,
)


def _sec(
    nrc: str,
    curso: str,
    bloques: list[tuple[str, int, str, str]],
    actividad: str = "TEO",
    cupos: int = 30,
    rut: str = "",
) -> SeccionNRC:
    return SeccionNRC(
        nrc=nrc,
        curso=curso,
        actividad=actividad,
        bloques=tuple(BloqueHorario(dia=d, modulo=m, sala=s, edificio=e) for d, m, s, e in bloques),
        cupos=cupos,
        rut_docente=rut,
    )


def test_auditoria_conflictos_sala_y_docente():
    """Detecta colisiones de sala física (H2) y docente (H3) ignorando salas virtuales."""
    secciones = [
        _sec("1001", "CINF101", [("Lunes", 1, "301", "A1")], rut="11.111.111-1"),
        _sec("1002", "CINF102", [("Lunes", 1, "301", "A1")], rut="22.222.222-2"),
        _sec("1003", "CINF103", [("Martes", 3, "ONLINE", "")], rut="11.111.111-1"),
        _sec("1004", "CINF104", [("Martes", 3, "ONLINE", "")], rut="11.111.111-1"),
    ]
    c_salas, c_doc = auditar_conflictos_oferta(secciones)

    assert len(c_salas) == 1
    assert c_salas[0].recurso == "A1-301"
    assert c_salas[0].nrcs == ("1001", "1002")

    assert len(c_doc) == 1
    assert c_doc[0].recurso == "11.111.111-1"
    assert c_doc[0].nrcs == ("1003", "1004")


def test_opciones_por_curso_descarta_tope_interno_entre_actividades():
    """No genera opciones cuya cátedra (TEO) y laboratorio (LAB) se solapen."""
    secciones = [
        _sec("101", "PTEC101", [("Lunes", 1, "101", "A1"), ("Lunes", 2, "101", "A1")], actividad="TEO"),
        _sec("102", "PTEC101", [("Lunes", 2, "LAB1", "B1")], actividad="LAB"),
        _sec("103", "PTEC101", [("Lunes", 3, "LAB1", "B1")], actividad="LAB"),
    ]
    ops = opciones_por_curso(secciones)["PTEC101"]
    assert len(ops) == 1
    assert ops[0].nrcs == ("101", "103")


def test_evaluar_slots_calcula_ventanas_dias_jornada_y_sobrecarga():
    """Evalúa con exactitud ventanas intermedias, días activos y bloques fuera de jornada."""
    slots = frozenset({("Lunes", 1), ("Lunes", 4), ("Martes", 8)})
    m = evaluar_slots(slots, PreferenciasUCTP(jornada="manana"))
    assert m.ventanas == 2  # M2 y M3 libres el lunes
    assert m.dias_activos == 2
    assert m.bloques_fuera_jornada == 1  # Martes M8 fuera de M1..M6
    assert m.exceso_carga_diaria == 0
    assert m.penalizacion == pytest.approx(3.0 * 2 + 2.0 * 2 + 1.5 * 1)


def test_branch_and_bound_coincide_con_optimo_fuerza_bruta():
    """La poda por cota inferior admisible halla exactamente el óptimo global."""
    secciones = [
        # Curso A: Lunes M1-M2 o Lunes M5-M6 o Miércoles M1-M2
        _sec("A1", "C1", [("Lunes", 1, "101", "A1"), ("Lunes", 2, "101", "A1")]),
        _sec("A2", "C1", [("Lunes", 5, "102", "A1"), ("Lunes", 6, "102", "A1")]),
        _sec("A3", "C1", [("Miércoles", 1, "103", "A1"), ("Miércoles", 2, "103", "A1")]),
        # Curso B: Lunes M3-M4 (compacto con A1 y A2!) o Martes M7-M8
        _sec("B1", "C2", [("Lunes", 3, "201", "A1"), ("Lunes", 4, "201", "A1")]),
        _sec("B2", "C2", [("Martes", 7, "202", "A1"), ("Martes", 8, "202", "A1")]),
        # Curso C: Lunes M5-M6 (0 ventanas con A1+B1 en 1 solo día!) o Jueves M9-M10
        _sec("C1", "C3", [("Lunes", 5, "301", "A1"), ("Lunes", 6, "301", "A1")]),
        _sec("C2", "C3", [("Jueves", 9, "302", "A1"), ("Jueves", 10, "302", "A1")]),
        # Curso D: Lunes M1-M2 (choca con A1) o Martes M1-M2
        _sec("D1", "C4", [("Lunes", 1, "401", "A1"), ("Lunes", 2, "401", "A1")]),
        _sec("D2", "C4", [("Martes", 1, "402", "A1"), ("Martes", 2, "402", "A1")]),
    ]
    prefs = PreferenciasUCTP(jornada="manana")

    # Fuerza bruta exhaustiva
    ops = opciones_por_curso(secciones)
    cursos = sorted(ops)
    optimo_bruto = float("inf")
    for comb in itertools.product(*(ops[c] for c in cursos)):
        usados: set[tuple[str, int]] = set()
        valido = True
        for op in comb:
            if not op.slots.isdisjoint(usados):
                valido = False
                break
            usados.update(op.slots)
        if valido:
            pen = evaluar_slots(frozenset(usados), prefs).penalizacion
            optimo_bruto = min(optimo_bruto, pen)

    res_bb = resolver_branch_and_bound(secciones, prefs=prefs, max_horarios=5)
    assert len(res_bb.soluciones) >= 1
    mejor = res_bb.soluciones[0]
    assert mejor.metricas.penalizacion == pytest.approx(optimo_bruto)
    assert mejor.metricas.ventanas == 0

    # Validar H1 = 0 en todas las soluciones devueltas
    for sol in res_bb.soluciones:
        vistos: set[tuple[str, int]] = set()
        for op in sol.asignacion.values():
            assert op.slots.isdisjoint(vistos)
            vistos.update(op.slots)


def test_recocido_simulado_mejora_o_iguala_linea_base_sin_topes():
    """Simulated Annealing preserva H1 = 0 y alcanza soluciones de alta calidad."""
    secciones = [
        _sec("1A", "MAT", [("Lunes", 1, "101", "A"), ("Lunes", 2, "101", "A")]),
        _sec("1B", "MAT", [("Viernes", 9, "102", "A"), ("Viernes", 10, "102", "A")]),
        _sec("2A", "FIS", [("Lunes", 3, "201", "A"), ("Lunes", 4, "201", "A")]),
        _sec("2B", "FIS", [("Lunes", 8, "202", "A"), ("Lunes", 9, "202", "A")]),
        _sec("3A", "PRG", [("Lunes", 5, "301", "A"), ("Lunes", 6, "301", "A")]),
        _sec("3B", "PRG", [("Miércoles", 7, "302", "A"), ("Miércoles", 8, "302", "A")]),
    ]
    res_sa = resolver_recocido_simulado(secciones, prefs=PreferenciasUCTP(jornada="manana"), iteraciones=600)
    assert len(res_sa.soluciones) >= 1
    assert res_sa.soluciones[0].metricas.ventanas == 0
    assert res_sa.soluciones[0].metricas.dias_activos == 1


def test_vacantes_sin_tope_excluye_seccion_siempre_en_conflicto():
    """Las secciones que chocan con la única oferta de otro ramo no suman vacantes."""
    secciones = [
        _sec("100", "OBLIG", [("Lunes", 1, "101", "A")], cupos=40),
        _sec("201", "OTRO", [("Lunes", 1, "102", "A")], cupos=30),  # siempre choca con 100
        _sec("202", "OTRO", [("Martes", 1, "103", "A")], cupos=25),  # compatible
    ]
    vac = vacantes_sin_tope(secciones)
    assert vac["OBLIG"] == 40
    assert vac["OTRO"] == 25


def test_instancia_infactible_retorna_lista_vacia():
    """Ante choque inevitable en H1, retorna 0 soluciones sin lanzar excepción."""
    secciones = [
        _sec("1", "C1", [("Lunes", 1, "101", "A")]),
        _sec("2", "C2", [("Lunes", 1, "102", "A")]),
    ]
    for alg in ("branch_and_bound", "recocido_simulado", "aleatorio"):
        res = optimizar_horarios(secciones, algoritmo=alg)
        assert res.soluciones == []


def test_disjuntos_no_repite_nrcs():
    """En modo disjuntos=True cada horario generado consume NRCs distintos."""
    secciones = [
        _sec("A1", "C1", [("Lunes", 1, "101", "A")]),
        _sec("A2", "C1", [("Martes", 1, "102", "A")]),
        _sec("B1", "C2", [("Lunes", 2, "201", "A")]),
        _sec("B2", "C2", [("Martes", 2, "202", "A")]),
    ]
    res = resolver_branch_and_bound(secciones, max_horarios=5, disjuntos=True)
    assert len(res.soluciones) == 2
    usados_0 = {nrc for op in res.soluciones[0].asignacion.values() for nrc in op.nrcs}
    usados_1 = {nrc for op in res.soluciones[1].asignacion.values() for nrc in op.nrcs}
    assert usados_0.isdisjoint(usados_1)


@pytest.mark.django_db
def test_api_optimizar_horarios_requiere_auth_y_retorna_optimo(client, suite, crear_usuario):
    """El endpoint REST exige autenticación SSO y retorna soluciones óptimas + auditoría."""
    payload = {
        "algoritmo": "branch_and_bound",
        "preferencias": {"jornada": "manana"},
        "secciones": [
            {
                "nrc": "1001",
                "curso": "CINF201",
                "actividad": "TEO",
                "cupos": 30,
                "rut_docente": "11.111.111-1",
                "bloques": [{"dia": "Lunes", "modulo": 1, "sala": "301", "edificio": "A1"}],
            },
            {
                "nrc": "2001",
                "curso": "PTEC201",
                "actividad": "TEO",
                "cupos": 25,
                "rut_docente": "22.222.222-2",
                "bloques": [{"dia": "Lunes", "modulo": 2, "sala": "302", "edificio": "A1"}],
            },
            {
                "nrc": "2002",
                "curso": "PTEC201",
                "actividad": "TEO",
                "cupos": 25,
                "rut_docente": "11.111.111-1",
                "bloques": [{"dia": "Lunes", "modulo": 1, "sala": "301", "edificio": "A1"}],
            },
        ],
    }

    r_anon = client.post("/core/api/v1/horarios/optimizar", payload, content_type="application/json")
    assert r_anon.status_code in (401, 403)

    usuario = crear_usuario()
    token = emitir_token(
        SuiteIdentity(
            sub=str(usuario.pk),
            email=usuario.email,
            nombre=usuario.nombre_visible,
            organizacion="unab",
            roles=("estudiante",),
            modulos=("horarios",),
        )
    )
    client.cookies[COOKIE_NAME] = token

    r = client.post("/core/api/v1/horarios/optimizar", payload, content_type="application/json")
    assert r.status_code == 200, r.content
    data = r.json()
    assert len(data["soluciones"]) == 1
    assert data["soluciones"][0]["metricas"]["ventanas"] == 0
    assert data["soluciones"][0]["asignacion"] == {"CINF201": ["1001"], "PTEC201": ["2001"]}
    assert len(data["conflictos_sala"]) == 1
    assert len(data["conflictos_docente"]) == 1
    assert data["vacantes_sin_tope"] == {"CINF201": 30, "PTEC201": 25}
