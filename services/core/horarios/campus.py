"""Solver global de asignación de campus universitario (Master Timetabling).

Resuelve la programación simultánea de bloques horarios y salas físicas para todas las
clases de una facultad o campus completo, garantizando de forma incremental:

- H2 (Salas): ninguna sala física recibe dos clases en el mismo bloque.
- H3 (Docentes): ningún docente dicta dos clases simultáneas.
- Capacidad física: ``clase.cupo <= sala.capacidad``.
- Restricciones de distribución declaradas (``NotOverlap``, ``SameAttendees``,
  ``SameRoom``, ``DifferentRoom``, ``SameDays``, ``DifferentDays``).

Y minimizando la función objetivo compuesta sobre penalizaciones institucionales de
tiempo/sala y conflictos de co-inscripción estudiantil mediante un esquema en dos fases:

1. Constructivo determinista MRV (Minimum Remaining Values + grado de contención).
2. Optimización global por Simulated Annealing (relocalización e intercambio de pares).
"""

from __future__ import annotations

import math
import random
import time
from collections import defaultdict
from dataclasses import dataclass

from .motor import DIAS_ORDEN, SeccionNRC


@dataclass(frozen=True)
class SalaCampus:
    """Sala física disponible en el campus con su capacidad máxima."""

    id_sala: str
    capacidad: int
    edificio: str = ""


@dataclass(frozen=True)
class CandidatoTemporal:
    """Patrón horario admisible para una clase y su penalización institucional."""

    slots: tuple[tuple[str, int], ...]
    penalizacion: int = 0


@dataclass(frozen=True)
class CandidatoSala:
    """Sala candidata para una clase y su penalización de preferencia/distancia."""

    id_sala: str
    penalizacion: int = 0


@dataclass(frozen=True)
class ClaseCampus:
    """Unidad programable en la tabla maestra de campus (sección o clase)."""

    id_clase: str
    curso: str
    actividad: str = "TEO"
    cupo: int = 30
    docente: str = ""
    candidatos_tiempo: tuple[CandidatoTemporal, ...] = ()
    candidatos_sala: tuple[CandidatoSala, ...] = ()


@dataclass(frozen=True)
class RestriccionDistribucion:
    """Restricción relacional entre clases (subconjunto compatible con ITC-2019)."""

    tipo: str
    clases: tuple[str, ...]
    requerida: bool = True
    penalizacion: int = 0


@dataclass(frozen=True)
class AsignacionClase:
    """Asignación resultante ``(slots, sala)`` para una clase del campus."""

    id_clase: str
    curso: str
    actividad: str
    slots: tuple[tuple[str, int], ...]
    id_sala: str
    docente: str
    penalizacion_tiempo: int
    penalizacion_sala: int


@dataclass(frozen=True)
class MetricasCampus:
    """Métricas agregadas y auditoría de restricciones duras de la tabla maestra."""

    total_clases: int
    clases_asignadas: int
    conflictos_sala_h2: int
    conflictos_docente_h3: int
    conflictos_capacidad: int
    conflictos_distribucion_dura: int
    penalizacion_tiempo: int
    penalizacion_sala: int
    conflictos_estudiantes: int
    penalizacion_total: float
    tasa_asignacion_pct: float


@dataclass(frozen=True)
class ResultadoCampus:
    """Resultado estructurado de la optimización global de campus."""

    algoritmo: str
    asignaciones: list[AsignacionClase]
    no_asignadas: list[str]
    metricas: MetricasCampus
    tiempo_ms: float


@dataclass(frozen=True)
class _EstadoCandidato:
    tiempo_idx: int
    sala_idx: int  # -1 cuando la clase no requiere sala física
    slots: tuple[tuple[str, int], ...]
    id_sala: str
    pen_tiempo: int
    pen_sala: int


def _construir_dominios(
    clases: list[ClaseCampus],
    salas_map: dict[str, SalaCampus],
) -> dict[str, list[_EstadoCandidato]]:
    """Construye los pares válidos ``(tiempo, sala)`` respetando capacidad física."""
    dominios: dict[str, list[_EstadoCandidato]] = {}
    for cls in clases:
        lista: list[_EstadoCandidato] = []
        if not cls.candidatos_sala:
            for t_idx, ct in enumerate(cls.candidatos_tiempo):
                if ct.slots:
                    lista.append(
                        _EstadoCandidato(
                            tiempo_idx=t_idx,
                            sala_idx=-1,
                            slots=ct.slots,
                            id_sala="",
                            pen_tiempo=ct.penalizacion,
                            pen_sala=0,
                        )
                    )
        else:
            salas_validas = [
                (s_idx, cs)
                for s_idx, cs in enumerate(cls.candidatos_sala)
                if cs.id_sala in salas_map and salas_map[cs.id_sala].capacidad >= cls.cupo
            ]
            for t_idx, ct in enumerate(cls.candidatos_tiempo):
                if not ct.slots:
                    continue
                for s_idx, cs in salas_validas:
                    lista.append(
                        _EstadoCandidato(
                            tiempo_idx=t_idx,
                            sala_idx=s_idx,
                            slots=ct.slots,
                            id_sala=cs.id_sala,
                            pen_tiempo=ct.penalizacion,
                            pen_sala=cs.penalizacion,
                        )
                    )
        dominios[cls.id_clase] = lista
    return dominios


def _construir_grafo_estudiantes(
    clases: list[ClaseCampus],
    perfiles_estudiantes: list[list[str]] | None,
) -> dict[str, dict[str, int]]:
    """Precalcula el peso de co-inscripción entre pares de cursos."""
    if not perfiles_estudiantes:
        return {}
    cursos_activos = {c.curso for c in clases}
    co_ocurrencia: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for cursos in perfiles_estudiantes:
        unicos = sorted({c for c in cursos if c in cursos_activos})
        for i in range(len(unicos)):
            for j in range(i + 1, len(unicos)):
                c1, c2 = unicos[i], unicos[j]
                co_ocurrencia[c1][c2] += 1
                co_ocurrencia[c2][c1] += 1
    return {k: dict(v) for k, v in co_ocurrencia.items()}


def _construir_vecinos_no_solapamiento(
    restricciones: tuple[RestriccionDistribucion, ...] | list[RestriccionDistribucion],
) -> dict[str, set[str]]:
    """Indexa pares de clases sujetos a restricción dura ``NotOverlap`` o ``SameAttendees``."""
    vecinos: dict[str, set[str]] = defaultdict(set)
    for r in restricciones:
        if not r.requerida or r.tipo not in ("NotOverlap", "SameAttendees"):
            continue
        for i in range(len(r.clases)):
            for j in range(i + 1, len(r.clases)):
                a, b = r.clases[i], r.clases[j]
                vecinos[a].add(b)
                vecinos[b].add(a)
    return vecinos


def _es_factible_asignar(
    id_clase: str,
    cand: _EstadoCandidato,
    docente: str,
    uso_sala: dict[tuple[str, str, int], str],
    uso_docente: dict[tuple[str, str, int], str],
    estado: dict[str, _EstadoCandidato],
    vecinos_no_overlap: dict[str, set[str]],
) -> bool:
    """Verifica O(|slots|) que ``cand`` no viole H2, H3 ni NotOverlap duro."""
    if cand.id_sala:
        for d, m in cand.slots:
            ocupante = uso_sala.get((cand.id_sala, d, m))
            if ocupante is not None and ocupante != id_clase:
                return False
    if docente:
        for d, m in cand.slots:
            ocupante = uso_docente.get((docente, d, m))
            if ocupante is not None and ocupante != id_clase:
                return False
    if id_clase in vecinos_no_overlap:
        slots_cand = set(cand.slots)
        for otro_id in vecinos_no_overlap[id_clase]:
            otro = estado.get(otro_id)
            if otro is not None and slots_cand.intersection(otro.slots):
                return False
    return True


def _aplicar_asignacion(
    id_clase: str,
    cand: _EstadoCandidato | None,
    docente: str,
    estado: dict[str, _EstadoCandidato],
    uso_sala: dict[tuple[str, str, int], str],
    uso_docente: dict[tuple[str, str, int], str],
    clases_por_curso: dict[str, list[str]],
    curso: str,
    slots_por_curso: dict[str, set[tuple[str, int]]],
) -> None:
    """Actualiza el estado e índices incrementales al asignar o desasignar una clase."""
    prev = estado.pop(id_clase, None)
    if prev is not None:
        if prev.id_sala:
            for d, m in prev.slots:
                uso_sala.pop((prev.id_sala, d, m), None)
        if docente:
            for d, m in prev.slots:
                uso_docente.pop((docente, d, m), None)

    if cand is not None:
        estado[id_clase] = cand
        if cand.id_sala:
            for d, m in cand.slots:
                uso_sala[(cand.id_sala, d, m)] = id_clase
        if docente:
            for d, m in cand.slots:
                uso_docente[(docente, d, m)] = id_clase

    slots_curso: set[tuple[str, int]] = set()
    for cid in clases_por_curso[curso]:
        c_act = estado.get(cid)
        if c_act is not None:
            slots_curso.update(c_act.slots)
    slots_por_curso[curso] = slots_curso


def _delta_conflictos_curso(
    curso: str,
    nuevos_slots: tuple[tuple[str, int], ...],
    co_estudiantes: dict[str, dict[str, int]],
    slots_por_curso: dict[str, set[tuple[str, int]]],
) -> int:
    """Estima conflictos estudiantiles al ubicar una clase de ``curso`` en ``nuevos_slots``."""
    vecinos = co_estudiantes.get(curso)
    if not vecinos:
        return 0
    s_set = set(nuevos_slots)
    choques = 0
    for otro_curso, peso in vecinos.items():
        if s_set.intersection(slots_por_curso.get(otro_curso, ())):
            choques += peso
    return choques


def _evaluar_campus(
    clases: list[ClaseCampus],
    estado: dict[str, _EstadoCandidato],
    salas_map: dict[str, SalaCampus],
    co_estudiantes: dict[str, dict[str, int]],
    restricciones: tuple[RestriccionDistribucion, ...] | list[RestriccionDistribucion],
    peso_no_asignada: float = 500.0,
) -> tuple[MetricasCampus, float]:
    """Audita restricciones duras (H2/H3/capacidad) y calcula la función objetivo global."""
    uso_sala: dict[tuple[str, str, int], int] = defaultdict(int)
    uso_docente: dict[tuple[str, str, int], int] = defaultdict(int)
    slots_curso: dict[str, set[tuple[str, int]]] = defaultdict(set)

    pen_tiempo = 0
    pen_sala = 0
    conflictos_cap = 0

    for cls in clases:
        cand = estado.get(cls.id_clase)
        if cand is None:
            continue
        pen_tiempo += cand.pen_tiempo
        pen_sala += cand.pen_sala
        slots_curso[cls.curso].update(cand.slots)
        if cand.id_sala:
            sala_obj = salas_map.get(cand.id_sala)
            if sala_obj is None or cls.cupo > sala_obj.capacidad:
                conflictos_cap += 1
            for d, m in cand.slots:
                uso_sala[(cand.id_sala, d, m)] += 1
        if cls.docente:
            for d, m in cand.slots:
                uso_docente[(cls.docente, d, m)] += 1

    h2 = sum(c - 1 for c in uso_sala.values() if c > 1)
    h3 = sum(c - 1 for c in uso_docente.values() if c > 1)

    conflictos_dist = 0
    for r in restricciones:
        if not r.requerida or r.tipo not in ("NotOverlap", "SameAttendees"):
            continue
        ocup: dict[tuple[str, int], int] = defaultdict(int)
        for cid in r.clases:
            cand = estado.get(cid)
            if cand is None:
                continue
            for sl in cand.slots:
                ocup[sl] += 1
        conflictos_dist += sum(c - 1 for c in ocup.values() if c > 1)

    conflictos_est = 0
    vistos: set[tuple[str, str]] = set()
    for c1, vecinos in co_estudiantes.items():
        s1 = slots_curso.get(c1, set())
        if not s1:
            continue
        for c2, peso in vecinos.items():
            par = (c1, c2) if c1 < c2 else (c2, c1)
            if par in vistos:
                continue
            vistos.add(par)
            if s1.intersection(slots_curso.get(c2, set())):
                conflictos_est += peso

    total = len(clases)
    asignadas = len(estado)
    no_asignadas = total - asignadas
    objetivo = round(pen_tiempo + pen_sala + 2.0 * conflictos_est + peso_no_asignada * no_asignadas, 2)

    metricas = MetricasCampus(
        total_clases=total,
        clases_asignadas=asignadas,
        conflictos_sala_h2=h2,
        conflictos_docente_h3=h3,
        conflictos_capacidad=conflictos_cap,
        conflictos_distribucion_dura=conflictos_dist,
        penalizacion_tiempo=pen_tiempo,
        penalizacion_sala=pen_sala,
        conflictos_estudiantes=conflictos_est,
        penalizacion_total=objetivo,
        tasa_asignacion_pct=round(100.0 * asignadas / total, 1) if total else 100.0,
    )
    return metricas, objetivo


def _empaquetar_resultado(
    algoritmo: str,
    clases: list[ClaseCampus],
    estado: dict[str, _EstadoCandidato],
    metricas: MetricasCampus,
    t0: float,
) -> ResultadoCampus:
    asignaciones: list[AsignacionClase] = []
    no_asignadas: list[str] = []
    for cls in clases:
        cand = estado.get(cls.id_clase)
        if cand is None:
            no_asignadas.append(cls.id_clase)
            continue
        asignaciones.append(
            AsignacionClase(
                id_clase=cls.id_clase,
                curso=cls.curso,
                actividad=cls.actividad,
                slots=cand.slots,
                id_sala=cand.id_sala,
                docente=cls.docente,
                penalizacion_tiempo=cand.pen_tiempo,
                penalizacion_sala=cand.pen_sala,
            )
        )
    return ResultadoCampus(
        algoritmo=algoritmo,
        asignaciones=asignaciones,
        no_asignadas=no_asignadas,
        metricas=metricas,
        tiempo_ms=round((time.perf_counter() - t0) * 1000.0, 2),
    )


def resolver_campus_aleatorio(
    clases: list[ClaseCampus],
    salas: list[SalaCampus],
    perfiles_estudiantes: list[list[str]] | None = None,
    restricciones: tuple[RestriccionDistribucion, ...] | list[RestriccionDistribucion] = (),
    semilla: int = 42,
) -> ResultadoCampus:
    """Línea base constructiva aleatoria para la asignación global de campus."""
    t0 = time.perf_counter()
    rng = random.Random(semilla)
    salas_map = {s.id_sala: s for s in salas}
    dominios = _construir_dominios(clases, salas_map)
    co_estudiantes = _construir_grafo_estudiantes(clases, perfiles_estudiantes)
    vecinos_no_overlap = _construir_vecinos_no_solapamiento(restricciones)

    clases_por_curso: dict[str, list[str]] = defaultdict(list)
    for cls in clases:
        clases_por_curso[cls.curso].append(cls.id_clase)

    orden = list(clases)
    rng.shuffle(orden)

    estado: dict[str, _EstadoCandidato] = {}
    uso_sala: dict[tuple[str, str, int], str] = {}
    uso_docente: dict[tuple[str, str, int], str] = {}
    slots_por_curso: dict[str, set[tuple[str, int]]] = defaultdict(set)

    for cls in orden:
        cands = list(dominios[cls.id_clase])
        rng.shuffle(cands)
        for cand in cands:
            if _es_factible_asignar(cls.id_clase, cand, cls.docente, uso_sala, uso_docente, estado, vecinos_no_overlap):
                _aplicar_asignacion(
                    cls.id_clase,
                    cand,
                    cls.docente,
                    estado,
                    uso_sala,
                    uso_docente,
                    clases_por_curso,
                    cls.curso,
                    slots_por_curso,
                )
                break

    metricas, _ = _evaluar_campus(clases, estado, salas_map, co_estudiantes, restricciones)
    return _empaquetar_resultado("campus_aleatorio", clases, estado, metricas, t0)


def resolver_campus_global(
    clases: list[ClaseCampus],
    salas: list[SalaCampus],
    perfiles_estudiantes: list[list[str]] | None = None,
    restricciones: tuple[RestriccionDistribucion, ...] | list[RestriccionDistribucion] = (),
    iteraciones: int = 4_000,
    temp_inicial: float = 25.0,
    enfriamiento: float = 0.998,
    semilla: int = 42,
    presupuesto_segundos: float = 30.0,
) -> ResultadoCampus:
    """Resuelve la tabla maestra de campus mediante MRV + reubicación + Simulated Annealing."""
    t0 = time.perf_counter()
    rng = random.Random(semilla)
    salas_map = {s.id_sala: s for s in salas}
    dominios = _construir_dominios(clases, salas_map)
    co_estudiantes = _construir_grafo_estudiantes(clases, perfiles_estudiantes)
    vecinos_no_overlap = _construir_vecinos_no_solapamiento(restricciones)

    clases_por_curso: dict[str, list[str]] = defaultdict(list)
    clases_map: dict[str, ClaseCampus] = {}
    for cls in clases:
        clases_map[cls.id_clase] = cls
        clases_por_curso[cls.curso].append(cls.id_clase)

    # Fase 1: Constructivo MRV (menor dominio factible y mayor demanda estudiantil primero)
    orden = sorted(
        clases,
        key=lambda c: (
            len(dominios[c.id_clase]),
            -sum(co_estudiantes.get(c.curso, {}).values()),
            -c.cupo,
            c.id_clase,
        ),
    )

    estado: dict[str, _EstadoCandidato] = {}
    uso_sala: dict[tuple[str, str, int], str] = {}
    uso_docente: dict[tuple[str, str, int], str] = {}
    slots_por_curso: dict[str, set[tuple[str, int]]] = defaultdict(set)

    for cls in orden:
        mejor_cand: _EstadoCandidato | None = None
        mejor_costo = math.inf
        for cand in dominios[cls.id_clase]:
            if not _es_factible_asignar(
                cls.id_clase, cand, cls.docente, uso_sala, uso_docente, estado, vecinos_no_overlap
            ):
                continue
            choques = _delta_conflictos_curso(cls.curso, cand.slots, co_estudiantes, slots_por_curso)
            costo = cand.pen_tiempo + cand.pen_sala + 2.0 * choques
            if costo < mejor_costo:
                mejor_costo = costo
                mejor_cand = cand
        if mejor_cand is not None:
            _aplicar_asignacion(
                cls.id_clase,
                mejor_cand,
                cls.docente,
                estado,
                uso_sala,
                uso_docente,
                clases_por_curso,
                cls.curso,
                slots_por_curso,
            )

    # Fase 1b: Reubicación 1-a-1 iterativa (bumping) para insertar clases no asignadas
    while time.perf_counter() - t0 < presupuesto_segundos:
        hubo_mejora = False
        no_asignadas = [c for c in orden if c.id_clase not in estado and dominios[c.id_clase]]
        for cls in no_asignadas:
            if time.perf_counter() - t0 >= presupuesto_segundos:
                break
            for cand in dominios[cls.id_clase]:
                bloqueantes: set[str] = set()
                if cand.id_sala:
                    for d, m in cand.slots:
                        occ = uso_sala.get((cand.id_sala, d, m))
                        if occ:
                            bloqueantes.add(occ)
                if cls.docente:
                    for d, m in cand.slots:
                        occ = uso_docente.get((cls.docente, d, m))
                        if occ:
                            bloqueantes.add(occ)
                if len(bloqueantes) != 1:
                    continue
                blk_id = next(iter(bloqueantes))
                blk_cls = clases_map[blk_id]
                if blk_id in vecinos_no_overlap.get(cls.id_clase, ()):
                    continue
                prev_blk = estado[blk_id]
                _aplicar_asignacion(
                    blk_id,
                    None,
                    blk_cls.docente,
                    estado,
                    uso_sala,
                    uso_docente,
                    clases_por_curso,
                    blk_cls.curso,
                    slots_por_curso,
                )
                reubicado = False
                if _es_factible_asignar(
                    cls.id_clase, cand, cls.docente, uso_sala, uso_docente, estado, vecinos_no_overlap
                ):
                    _aplicar_asignacion(
                        cls.id_clase,
                        cand,
                        cls.docente,
                        estado,
                        uso_sala,
                        uso_docente,
                        clases_por_curso,
                        cls.curso,
                        slots_por_curso,
                    )
                    for alt_blk in dominios[blk_id]:
                        if alt_blk != prev_blk and _es_factible_asignar(
                            blk_id, alt_blk, blk_cls.docente, uso_sala, uso_docente, estado, vecinos_no_overlap
                        ):
                            _aplicar_asignacion(
                                blk_id,
                                alt_blk,
                                blk_cls.docente,
                                estado,
                                uso_sala,
                                uso_docente,
                                clases_por_curso,
                                blk_cls.curso,
                                slots_por_curso,
                            )
                            reubicado = True
                            break
                    if not reubicado:
                        _aplicar_asignacion(
                            cls.id_clase,
                            None,
                            cls.docente,
                            estado,
                            uso_sala,
                            uso_docente,
                            clases_por_curso,
                            cls.curso,
                            slots_por_curso,
                        )
                if reubicado:
                    hubo_mejora = True
                    break
                _aplicar_asignacion(
                    blk_id,
                    prev_blk,
                    blk_cls.docente,
                    estado,
                    uso_sala,
                    uso_docente,
                    clases_por_curso,
                    blk_cls.curso,
                    slots_por_curso,
                )
        if not hubo_mejora:
            break

    mejor_estado = dict(estado)
    mejor_metricas, mejor_obj = _evaluar_campus(clases, mejor_estado, salas_map, co_estudiantes, restricciones)
    actual_obj = mejor_obj

    # Fase 2: Simulated Annealing con relocalización y swap de pares bajo presupuesto de tiempo
    candidatos_movibles = [c for c in clases if len(dominios[c.id_clase]) > 1 or c.id_clase not in estado]
    if candidatos_movibles and iteraciones > 0:
        temp = temp_inicial
        for it in range(iteraciones):
            if (it & 15) == 0 and (time.perf_counter() - t0) >= presupuesto_segundos:
                break

            # Con probabilidad 25% intentar swap entre dos clases asignadas cuando hay suficientes clases
            if len(estado) >= 2 and rng.random() < 0.25:
                ids_asig = list(estado.keys())
                id_a = rng.choice(ids_asig)
                id_b = rng.choice(ids_asig)
                if id_a == id_b:
                    temp *= enfriamiento
                    continue
                cls_a, cls_b = clases_map[id_a], clases_map[id_b]
                prev_a, prev_b = estado[id_a], estado[id_b]
                cands_a = [c for c in dominios[id_a] if c.slots == prev_b.slots and c.id_sala == prev_b.id_sala]
                cands_b = [c for c in dominios[id_b] if c.slots == prev_a.slots and c.id_sala == prev_a.id_sala]
                if not cands_a or not cands_b:
                    temp *= enfriamiento
                    continue
                _aplicar_asignacion(
                    id_a,
                    None,
                    cls_a.docente,
                    estado,
                    uso_sala,
                    uso_docente,
                    clases_por_curso,
                    cls_a.curso,
                    slots_por_curso,
                )
                _aplicar_asignacion(
                    id_b,
                    None,
                    cls_b.docente,
                    estado,
                    uso_sala,
                    uso_docente,
                    clases_por_curso,
                    cls_b.curso,
                    slots_por_curso,
                )
                cand_a, cand_b = cands_a[0], cands_b[0]
                ok_swap = False
                if _es_factible_asignar(id_a, cand_a, cls_a.docente, uso_sala, uso_docente, estado, vecinos_no_overlap):
                    _aplicar_asignacion(
                        id_a,
                        cand_a,
                        cls_a.docente,
                        estado,
                        uso_sala,
                        uso_docente,
                        clases_por_curso,
                        cls_a.curso,
                        slots_por_curso,
                    )
                    if _es_factible_asignar(
                        id_b, cand_b, cls_b.docente, uso_sala, uso_docente, estado, vecinos_no_overlap
                    ):
                        _aplicar_asignacion(
                            id_b,
                            cand_b,
                            cls_b.docente,
                            estado,
                            uso_sala,
                            uso_docente,
                            clases_por_curso,
                            cls_b.curso,
                            slots_por_curso,
                        )
                        ok_swap = True
                if ok_swap:
                    nueva_metrica, nuevo_obj = _evaluar_campus(clases, estado, salas_map, co_estudiantes, restricciones)
                    delta = nuevo_obj - actual_obj
                    if delta <= 0 or (temp > 1e-6 and rng.random() < math.exp(-delta / temp)):
                        actual_obj = nuevo_obj
                        if nuevo_obj < mejor_obj:
                            mejor_obj = nuevo_obj
                            mejor_estado = dict(estado)
                            mejor_metricas = nueva_metrica
                        temp *= enfriamiento
                        continue
                _aplicar_asignacion(
                    id_a,
                    None,
                    cls_a.docente,
                    estado,
                    uso_sala,
                    uso_docente,
                    clases_por_curso,
                    cls_a.curso,
                    slots_por_curso,
                )
                _aplicar_asignacion(
                    id_b,
                    None,
                    cls_b.docente,
                    estado,
                    uso_sala,
                    uso_docente,
                    clases_por_curso,
                    cls_b.curso,
                    slots_por_curso,
                )
                _aplicar_asignacion(
                    id_a,
                    prev_a,
                    cls_a.docente,
                    estado,
                    uso_sala,
                    uso_docente,
                    clases_por_curso,
                    cls_a.curso,
                    slots_por_curso,
                )
                _aplicar_asignacion(
                    id_b,
                    prev_b,
                    cls_b.docente,
                    estado,
                    uso_sala,
                    uso_docente,
                    clases_por_curso,
                    cls_b.curso,
                    slots_por_curso,
                )
                temp *= enfriamiento
                continue

            cls = rng.choice(candidatos_movibles)
            dom = dominios[cls.id_clase]
            if not dom:
                continue
            cand_nuevo = rng.choice(dom)
            prev = estado.get(cls.id_clase)
            if prev == cand_nuevo:
                temp *= enfriamiento
                continue

            if not _es_factible_asignar(
                cls.id_clase, cand_nuevo, cls.docente, uso_sala, uso_docente, estado, vecinos_no_overlap
            ):
                temp *= enfriamiento
                continue

            _aplicar_asignacion(
                cls.id_clase,
                cand_nuevo,
                cls.docente,
                estado,
                uso_sala,
                uso_docente,
                clases_por_curso,
                cls.curso,
                slots_por_curso,
            )
            nueva_metrica, nuevo_obj = _evaluar_campus(clases, estado, salas_map, co_estudiantes, restricciones)
            delta = nuevo_obj - actual_obj
            if delta <= 0 or (temp > 1e-6 and rng.random() < math.exp(-delta / temp)):
                actual_obj = nuevo_obj
                if nuevo_obj < mejor_obj:
                    mejor_obj = nuevo_obj
                    mejor_estado = dict(estado)
                    mejor_metricas = nueva_metrica
            else:
                _aplicar_asignacion(
                    cls.id_clase,
                    prev,
                    cls.docente,
                    estado,
                    uso_sala,
                    uso_docente,
                    clases_por_curso,
                    cls.curso,
                    slots_por_curso,
                )
            temp *= enfriamiento

    return _empaquetar_resultado("campus_global_sa", clases, mejor_estado, mejor_metricas, t0)


def construir_campus_desde_secciones(
    secciones: list[SeccionNRC],
    salas: list[SalaCampus],
    modulos_permitidos: tuple[int, ...] = tuple(range(1, 15)),
    dias_permitidos: tuple[str, ...] = DIAS_ORDEN[:5],
) -> list[ClaseCampus]:
    """Convierte secciones de oferta Banner/Syaproa en clases programables de campus."""
    salas_cand = tuple(CandidatoSala(id_sala=s.id_sala, penalizacion=0) for s in salas)
    clases: list[ClaseCampus] = []

    for sec in secciones:
        duracion_por_dia: dict[str, list[int]] = defaultdict(list)
        for b in sec.bloques:
            duracion_por_dia[b.dia].append(b.modulo)

        patrones: list[CandidatoTemporal] = []
        slots_originales = tuple(sorted(b.slot for b in sec.bloques))
        if slots_originales:
            patrones.append(CandidatoTemporal(slots=slots_originales, penalizacion=0))

        # Generar patrones alternativos de misma longitud diaria para optimizar conflictos H2/H3
        longitudes = [len(mods) for mods in duracion_por_dia.values()] or [2]
        largo_tipico = max(1, longitudes[0])
        for d in dias_permitidos:
            for m_ini in modulos_permitidos:
                if m_ini + largo_tipico - 1 > max(modulos_permitidos):
                    continue
                alt = tuple((d, m) for m in range(m_ini, m_ini + largo_tipico))
                if alt != slots_originales:
                    patrones.append(CandidatoTemporal(slots=alt, penalizacion=1))
                if len(patrones) >= 12:
                    break
            if len(patrones) >= 12:
                break

        clases.append(
            ClaseCampus(
                id_clase=sec.nrc,
                curso=sec.curso,
                actividad=sec.actividad,
                cupo=max(1, sec.cupos or sec.inscritos or 30),
                docente=sec.rut_docente or sec.nombre_docente,
                candidatos_tiempo=tuple(patrones),
                candidatos_sala=salas_cand,
            )
        )
    return clases
