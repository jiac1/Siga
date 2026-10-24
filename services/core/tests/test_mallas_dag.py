"""Validación matemática de Grafos Dirigidos Acíclicos (DAG) de las 10 mallas UNAB.

Recupera la cobertura de pruebas de tests/malla.test.js y certifica que los
planes de estudio de la Facultad de Ingeniería de la UNAB son formalmente
acíclicos (sin ciclos infinitos de prerrequisitos) y que la lógica de
disponibilidad y cascada de aprobación opera correctamente.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]
PORTAL_MALLAS_HTML = RAIZ / "services" / "portal" / "apps" / "malla"
PORTAL_MALLAS_JSON = RAIZ / "services" / "portal" / "shared" / "mallas"


def create_prereq_graph(cursos: list[dict]) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    by_code = {c["codigo"]: c for c in cursos if "codigo" in c}
    pre: dict[str, list[str]] = {
        c["codigo"]: [p for p in c.get("requisitos", []) if p in by_code] for c in cursos if "codigo" in c
    }
    dep: dict[str, list[str]] = {c["codigo"]: [] for c in cursos if "codigo" in c}
    for codigo, reqs in pre.items():
        for p in reqs:
            dep[p].append(codigo)
    return pre, dep


def get_ancestors(codigo: str, pre: dict[str, list[str]]) -> set[str]:
    res: set[str] = set()

    def walk(c: str):
        for p in pre.get(c, []):
            if p not in res:
                res.add(p)
                walk(p)

    walk(codigo)
    return res


def get_descendants(codigo: str, dep: dict[str, list[str]]) -> set[str]:
    res: set[str] = set()

    def walk(c: str):
        for d in dep.get(c, []):
            if d not in res:
                res.add(d)
                walk(d)

    walk(codigo)
    return res


def is_available(codigo: str, aprobadas: set[str], pre: dict[str, list[str]]) -> bool:
    if codigo in aprobadas:
        return False
    return all(p in aprobadas for p in pre.get(codigo, []))


def is_offered(semestre: int, periodo: str) -> bool:
    if semestre <= 4 or periodo == "todos":
        return True
    if periodo == "1":
        return semestre % 2 != 0
    if periodo == "2":
        return semestre % 2 == 0
    return False


def simulate_approval_cascade(
    codigo: str, aprobadas: set[str], pre: dict[str, list[str]], dep: dict[str, list[str]]
) -> set[str]:
    estado = set(aprobadas)
    if codigo in estado:
        estado.remove(codigo)
        for d in get_descendants(codigo, dep):
            estado.discard(d)
    else:
        estado.add(codigo)
        for a in get_ancestors(codigo, pre):
            estado.add(a)
    return estado


def detect_cycle(cursos: list[dict]) -> list[str] | None:
    by_code = {c["codigo"]: c for c in cursos if "codigo" in c}
    adj: dict[str, list[str]] = {
        c["codigo"]: [p for p in c.get("requisitos", []) if p in by_code] for c in cursos if "codigo" in c
    }

    visitado: dict[str, int] = {}  # 0: no visitado, 1: en progreso, 2: completado
    padre: dict[str, str] = {}

    for nodo in adj:
        if nodo in visitado:
            continue
        pila = [nodo]
        while pila:
            curr = pila[-1]
            if curr not in visitado:
                visitado[curr] = 1
                for vecino in adj.get(curr, []):
                    if visitado.get(vecino) == 1:
                        # Ciclo detectado: reconstruir camino
                        ciclo = [vecino, curr]
                        p = padre.get(curr)
                        while p and p != vecino:
                            ciclo.append(p)
                            p = padre.get(p)
                        ciclo.append(vecino)
                        return ciclo[::-1]
                    if vecino not in visitado:
                        padre[vecino] = curr
                        pila.append(vecino)
            else:
                pila.pop()
                visitado[curr] = 2
    return None


def test_algoritmos_grafos_simples():
    mock = [
        {"codigo": "A", "semestre": 1, "requisitos": []},
        {"codigo": "B", "semestre": 2, "requisitos": ["A"]},
        {"codigo": "E", "semestre": 2, "requisitos": []},
        {"codigo": "C", "semestre": 3, "requisitos": ["B", "E"]},
        {"codigo": "D", "semestre": 5, "requisitos": ["C"]},
        {"codigo": "F", "semestre": 6, "requisitos": []},
    ]
    pre, dep = create_prereq_graph(mock)
    assert pre["A"] == []
    assert pre["B"] == ["A"]
    assert set(pre["C"]) == {"B", "E"}
    assert dep["A"] == ["B"]
    assert dep["C"] == ["D"]

    # Ancestros y descendientes
    assert get_ancestors("D", pre) == {"A", "B", "C", "E"}
    assert get_descendants("A", dep) == {"B", "C", "D"}

    # Disponibilidad
    aprobadas = {"A", "E"}
    assert is_available("B", aprobadas, pre) is True
    assert is_available("C", aprobadas, pre) is False
    assert is_available("A", aprobadas, pre) is False

    # Oferta académica
    assert is_offered(1, "1") is True
    assert is_offered(1, "2") is True
    assert is_offered(4, "1") is True
    assert is_offered(5, "1") is True
    assert is_offered(5, "2") is False
    assert is_offered(6, "1") is False
    assert is_offered(6, "2") is True

    # Cascada
    estado = simulate_approval_cascade("D", set(), pre, dep)
    assert {"A", "B", "C", "D", "E"}.issubset(estado)
    estado = simulate_approval_cascade("B", estado, pre, dep)
    assert "B" not in estado and "C" not in estado and "D" not in estado
    assert "A" in estado and "E" in estado

    # Detección de ciclo
    assert detect_cycle(mock) is None
    con_ciclo = [
        {"codigo": "X", "requisitos": ["Z"]},
        {"codigo": "Y", "requisitos": ["X"]},
        {"codigo": "Z", "requisitos": ["Y"]},
    ]
    assert detect_cycle(con_ciclo) is not None


def test_validacion_diez_mallas_reales_unab():
    archivos = sorted(PORTAL_MALLAS_HTML.glob("malla_*.html"))
    assert len(archivos) == 10, f"Se esperaban exactamente 10 mallas, encontradas: {len(archivos)}"

    re_cursos = re.compile(r"const\s+CURSOS\s*=\s*(\[.*?\]);", re.DOTALL)

    for ruta in archivos:
        contenido = ruta.read_text(encoding="utf-8")
        match = re_cursos.search(contenido)
        assert match is not None, f"No se encontró 'const CURSOS' en {ruta.name}"

        cursos = json.loads(match.group(1))
        assert len(cursos) >= 30, f"{ruta.name} tiene muy pocas asignaturas ({len(cursos)})"

        ciclo = detect_cycle(cursos)
        assert ciclo is None, f"¡Ciclo infinito detectado en la malla {ruta.name}!: {ciclo}"

        pre, dep = create_prereq_graph(cursos)
        max_sem = max(c["semestre"] for c in cursos)
        ramo_final = next((c for c in cursos if c["semestre"] >= max_sem - 1 and c.get("requisitos")), None)
        if ramo_final:
            anc = get_ancestors(ramo_final["codigo"], pre)
            assert len(anc) > 0, f"Ramo de último año {ramo_final['codigo']} debe tener prerrequisitos"
            cascada = simulate_approval_cascade(ramo_final["codigo"], set(), pre, dep)
            assert ramo_final["codigo"] in cascada
            assert anc.issubset(cascada)
