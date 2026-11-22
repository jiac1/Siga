"""Motor de optimización combinatoria para UCTP (University Course Timetabling Problem).

Formaliza y resuelve la generación de horarios libres de topes (restricción dura H1),
audita choques de sala física (H2) y docente (H3) sobre la programación académica, y
minimiza restricciones blandas (ventanas horarias, días activos, jornada y sobrecarga)
mediante tres estrategias comparables:

1. ``aleatorio``: backtracking MRV con ordenamiento aleatorio (línea base).
2. ``branch_and_bound``: búsqueda exacta con ordenamiento MRV y poda por cota inferior
   admisible garantizando optimalidad global dentro del presupuesto de nodos.
3. ``recocido_simulado``: metaheurística Simulated Annealing sobre el espacio de
   soluciones factibles (H1 = 0) para instancias de alta combinatoria.

No depende de Django ni de base de datos, permitiendo ejecución directa en benchmarks
y paridad exacta con el solver cliente (``services/portal/apps/horarios/uctp-solver.js``).
"""

from __future__ import annotations

import math
import random
import time
from collections import defaultdict
from dataclasses import dataclass

DIAS_ORDEN = ("Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado")

JORNADA_MODULOS: dict[str, range] = {
    "manana": range(1, 7),  # M1–M6 (08:30 - 13:50)
    "tarde": range(7, 15),  # M7–M14 (14:00 - 21:10)
    "vespertino": range(15, 21),  # M15–M20 (19:00 - 23:50)
}

SALAS_NO_FISICAS = frozenset({"", "TBA", "S/I", "SIN SALA", "ONLINE", "VIRTUAL", "REMOTO", "POR DEFINIR"})


@dataclass(frozen=True)
class BloqueHorario:
    """Representa una asignación atómica de día, módulo y espacio físico."""

    dia: str
    modulo: int
    sala: str = ""
    edificio: str = ""

    @property
    def slot(self) -> tuple[str, int]:
        """Retorna la tupla temporal ``(dia, modulo)``."""
        return (self.dia, self.modulo)

    @property
    def clave_sala(self) -> str:
        """Retorna un identificador normalizado de sala física o cadena vacía si es virtual."""
        sala = self.sala.strip().upper()
        edificio = self.edificio.strip().upper()
        if sala in SALAS_NO_FISICAS:
            return ""
        return f"{edificio}-{sala}" if edificio else sala


@dataclass(frozen=True)
class SeccionNRC:
    """Sección ofertada (NRC) de una asignatura con sus bloques, cupos y docente."""

    nrc: str
    curso: str
    actividad: str
    bloques: tuple[BloqueHorario, ...]
    cupos: int = 0
    inscritos: int = 0
    rut_docente: str = ""
    nombre_docente: str = ""
    nombre_curso: str = ""

    @property
    def slots(self) -> frozenset[tuple[str, int]]:
        """Conjunto inmutable de bloques temporales ocupados por la sección."""
        return frozenset(b.slot for b in self.bloques)


@dataclass(frozen=True)
class OpcionCurso:
    """Combinación de secciones (NRCs) que cubre todas las actividades de un curso sin choque interno."""

    curso: str
    secciones: tuple[SeccionNRC, ...]
    slots: frozenset[tuple[str, int]]

    @property
    def nrcs(self) -> tuple[str, ...]:
        """Tupla ordenada de códigos NRC que conforman esta opción."""
        return tuple(sorted(s.nrc for s in self.secciones))


@dataclass(frozen=True)
class PreferenciasUCTP:
    """Pesos y preferencias de la función objetivo de restricciones blandas."""

    jornada: str = "cualquiera"
    peso_ventanas: float = 3.0
    peso_dias: float = 2.0
    peso_jornada: float = 1.5
    peso_sobrecarga: float = 1.0
    max_modulos_dia: int = 6


@dataclass(frozen=True)
class ConflictoOferta:
    """Violación de restricción dura de sala (H2) o docente (H3) detectada en la oferta."""

    tipo: str
    recurso: str
    dia: str
    modulo: int
    nrcs: tuple[str, ...]


@dataclass(frozen=True)
class MetricasHorario:
    """Desglose cuantitativo de la función objetivo para un horario factible."""

    ventanas: int
    dias_activos: int
    bloques_fuera_jornada: int
    exceso_carga_diaria: int
    penalizacion: float


@dataclass(frozen=True)
class SolucionHorario:
    """Asignación completa sin topes de una opción por asignatura y sus métricas."""

    asignacion: dict[str, OpcionCurso]
    metricas: MetricasHorario

    def firma(self) -> tuple[tuple[str, tuple[str, ...]], ...]:
        """Clave determinista para deduplicar horarios equivalentes."""
        return tuple((curso, op.nrcs) for curso, op in sorted(self.asignacion.items()))


@dataclass(frozen=True)
class ResultadoUCTP:
    """Resultado consolidado de una ejecución de optimización y auditoría UCTP."""

    soluciones: list[SolucionHorario]
    conflictos_sala: list[ConflictoOferta]
    conflictos_docente: list[ConflictoOferta]
    vacantes_sin_tope: dict[str, int]
    nodos_explorados: int
    nodos_podados: int
    algoritmo: str
    tiempo_ms: float


def auditar_conflictos_oferta(
    secciones: list[SeccionNRC],
) -> tuple[list[ConflictoOferta], list[ConflictoOferta]]:
    """Audita restricciones duras institucionales H2 (salas) y H3 (docentes) sobre la oferta.

    Args:
        secciones: Lista de secciones (NRC) ofertadas en el período.

    Returns:
        Tupla ``(conflictos_sala, conflictos_docente)`` ordenada de forma determinista.
    """
    por_sala: dict[tuple[str, str, int], set[str]] = defaultdict(set)
    por_docente: dict[tuple[str, str, int], set[str]] = defaultdict(set)

    for sec in secciones:
        rut = sec.rut_docente.strip().upper()
        for bloque in sec.bloques:
            sala_key = bloque.clave_sala
            if sala_key:
                por_sala[(sala_key, bloque.dia, bloque.modulo)].add(sec.nrc)
            if rut:
                por_docente[(rut, bloque.dia, bloque.modulo)].add(sec.nrc)

    conflictos_sala = [
        ConflictoOferta(tipo="sala", recurso=sala, dia=dia, modulo=mod, nrcs=tuple(sorted(nrcs)))
        for (sala, dia, mod), nrcs in sorted(por_sala.items())
        if len(nrcs) > 1
    ]
    conflictos_docente = [
        ConflictoOferta(tipo="docente", recurso=rut, dia=dia, modulo=mod, nrcs=tuple(sorted(nrcs)))
        for (rut, dia, mod), nrcs in sorted(por_docente.items())
        if len(nrcs) > 1
    ]
    return conflictos_sala, conflictos_docente


def _opciones_de_curso(curso: str, secs: list[SeccionNRC], max_opciones: int) -> list[OpcionCurso]:
    """Genera las combinaciones de secciones sin tope interno para un único curso."""
    actividades = sorted({s.actividad for s in secs})
    secs_por_act: dict[str, list[SeccionNRC]] = {
        act: sorted([s for s in secs if s.actividad == act], key=lambda s: s.nrc) for act in actividades
    }
    encontradas: list[OpcionCurso] = []
    vistas: set[tuple[str, ...]] = set()

    def backtrack(idx: int, elegidas: list[SeccionNRC], ocupados: frozenset[tuple[str, int]]) -> None:
        if len(encontradas) >= max_opciones:
            return
        if idx == len(actividades):
            clave = tuple(sorted(s.nrc for s in elegidas))
            if clave not in vistas:
                vistas.add(clave)
                encontradas.append(OpcionCurso(curso=curso, secciones=tuple(elegidas), slots=ocupados))
            return
        act = actividades[idx]
        for sec in secs_por_act[act]:
            if len(encontradas) >= max_opciones:
                return
            if not sec.slots.isdisjoint(ocupados):
                continue
            elegidas.append(sec)
            backtrack(idx + 1, elegidas, ocupados | sec.slots)
            elegidas.pop()

    backtrack(0, [], frozenset())
    return encontradas


def opciones_por_curso(
    secciones: list[SeccionNRC],
    max_opciones: int = 300,
) -> dict[str, list[OpcionCurso]]:
    """Construye coberturas exactas de actividades por curso garantizando ausencia de topes internos.

    Cada asignatura puede exigir múltiples tipos de actividad (por ejemplo ``TEO`` y ``LAB``).
    Se generan combinaciones de secciones que cubren cada tipo exactamente una vez y cuyos
    bloques horarios son disjuntos entre sí.

    Args:
        secciones: Secciones con al menos un bloque horario.
        max_opciones: Tope defensivo de combinaciones por curso para acotar el espacio.

    Returns:
        Diccionario ``codigo_curso -> lista de OpcionCurso`` deduplicado y determinista.
    """
    por_curso: dict[str, list[SeccionNRC]] = defaultdict(list)
    for sec in secciones:
        if sec.slots:
            por_curso[sec.curso].append(sec)

    return {curso: _opciones_de_curso(curso, secs, max_opciones) for curso, secs in sorted(por_curso.items())}


def _ventanas_dia(modulos: list[int]) -> int:
    """Calcula módulos libres intermedios (ventanas) dentro de un día académico."""
    diurnos = sorted(m for m in modulos if m <= 14)
    vespertinos = sorted(m for m in modulos if m >= 15)
    ventanas = 0
    if len(diurnos) >= 2:
        ventanas += (diurnos[-1] - diurnos[0] + 1) - len(diurnos)
    if len(vespertinos) >= 2:
        ventanas += (vespertinos[-1] - vespertinos[0] + 1) - len(vespertinos)
    return ventanas


def evaluar_slots(
    slots: frozenset[tuple[str, int]],
    prefs: PreferenciasUCTP | None = None,
) -> MetricasHorario:
    """Evalúa la función objetivo de restricciones blandas ``f(x)`` sobre un conjunto de bloques.

    Args:
        slots: Conjunto de tuplas ``(dia, modulo)`` ocupadas por el horario.
        prefs: Preferencias y pesos de penalización.

    Returns:
        Instancia ``MetricasHorario`` con desglose completo y puntaje compuesto.
    """
    p = prefs or PreferenciasUCTP()
    por_dia: dict[str, list[int]] = defaultdict(list)
    for dia, mod in slots:
        por_dia[dia].append(mod)

    ventanas = sum(_ventanas_dia(mods) for mods in por_dia.values())
    dias_activos = len(por_dia)

    rango_pref = JORNADA_MODULOS.get(p.jornada)
    if rango_pref is None:
        fuera_jornada = 0
    else:
        fuera_jornada = sum(1 for _, mod in slots if mod not in rango_pref)

    exceso_carga = sum(max(0, len(mods) - p.max_modulos_dia) for mods in por_dia.values())

    penalizacion = round(
        p.peso_ventanas * ventanas
        + p.peso_dias * dias_activos
        + p.peso_jornada * fuera_jornada
        + p.peso_sobrecarga * exceso_carga,
        4,
    )
    return MetricasHorario(
        ventanas=ventanas,
        dias_activos=dias_activos,
        bloques_fuera_jornada=fuera_jornada,
        exceso_carga_diaria=exceso_carga,
        penalizacion=penalizacion,
    )


def _cota_inferior_admisible(
    slots_parciales: frozenset[tuple[str, int]],
    slots_restantes_max: int,
    prefs: PreferenciasUCTP,
) -> float:
    """Calcula una cota inferior matemáticamente admisible para poda Branch-and-Bound.

    Los términos de días activos, bloques fuera de jornada y exceso de carga diaria son
    monótonamente no decrecientes al agregar asignaturas. El número de ventanas puede
    disminuir a lo sumo en ``slots_restantes_max`` si cada bloque futuro rellena un hueco
    existente, por lo que ``max(0, ventanas_actuales - slots_restantes_max)`` garantiza
    ausencia total de poda errónea del óptimo global.
    """
    m = evaluar_slots(slots_parciales, prefs)
    ventanas_min = max(0, m.ventanas - slots_restantes_max)
    return (
        prefs.peso_ventanas * ventanas_min
        + prefs.peso_dias * m.dias_activos
        + prefs.peso_jornada * m.bloques_fuera_jornada
        + prefs.peso_sobrecarga * m.exceso_carga_diaria
    )


def vacantes_sin_tope(
    secciones: list[SeccionNRC],
    opciones: dict[str, list[OpcionCurso]] | None = None,
) -> dict[str, int]:
    """Calcula las vacantes reales sin tope por asignatura en el semestre.

    Para cada asignatura suma los cupos de los NRC que pueden formar parte de al menos
    un horario completo libre de choques con las demás asignaturas.
    """
    if opciones is None:
        opciones = opciones_por_curso(secciones)
    cursos_con_horario = sorted(c for c, ops in opciones.items() if ops)

    def existe_con_nrc(curso_obj: str, nrc_obj: str) -> bool:
        orden = [curso_obj] + [c for c in cursos_con_horario if c != curso_obj]

        def bt(idx: int, usados: frozenset[tuple[str, int]]) -> bool:
            if idx == len(orden):
                return True
            curso = orden[idx]
            cands = opciones[curso]
            if curso == curso_obj:
                cands = [op for op in cands if any(s.nrc == nrc_obj for s in op.secciones)]
            for op in cands:
                if op.slots.isdisjoint(usados) and bt(idx + 1, usados | op.slots):
                    return True
            return False

        return bt(0, frozenset())

    cupos_nrc: dict[str, int] = {}
    nrcs_por_curso: dict[str, set[str]] = defaultdict(set)
    tiene_slots: dict[str, bool] = {}
    for sec in secciones:
        cupos_nrc.setdefault(sec.nrc, sec.cupos)
        nrcs_por_curso[sec.curso].add(sec.nrc)
        tiene_slots[sec.nrc] = tiene_slots.get(sec.nrc, False) or bool(sec.slots)

    vacantes: dict[str, int] = {}
    for curso, nrcs in sorted(nrcs_por_curso.items()):
        total = 0
        con_horario = curso in cursos_con_horario
        for nrc in sorted(nrcs):
            cabe = True if (not con_horario or not tiene_slots.get(nrc)) else existe_con_nrc(curso, nrc)
            if cabe:
                total += cupos_nrc.get(nrc, 0)
        vacantes[curso] = total
    return vacantes


def _construir_solucion_aleatoria(
    cursos_orden: list[str],
    opciones: dict[str, list[OpcionCurso]],
    rng: random.Random,
    contador: list[int],
) -> dict[str, OpcionCurso] | None:
    """Backtracking MRV aleatorio (línea base) que retorna el primer horario factible."""
    sel: dict[str, OpcionCurso] = {}

    def bt(idx: int, usados: frozenset[tuple[str, int]]) -> bool:
        contador[0] += 1
        if idx == len(cursos_orden):
            return True
        curso = cursos_orden[idx]
        cands = list(opciones[curso])
        rng.shuffle(cands)
        for op in cands:
            if not op.slots.isdisjoint(usados):
                continue
            sel[curso] = op
            if bt(idx + 1, usados | op.slots):
                return True
            del sel[curso]
        return False

    return dict(sel) if bt(0, frozenset()) else None


def resolver_aleatorio(
    secciones: list[SeccionNRC],
    prefs: PreferenciasUCTP | None = None,
    max_horarios: int = 5,
    disjuntos: bool = False,
    semilla: int = 42,
) -> ResultadoUCTP:
    """Resuelve UCTP mediante backtracking MRV aleatorio sin optimización de ventanas (línea base)."""
    t0 = time.perf_counter()
    p = prefs or PreferenciasUCTP()
    conflictos_sala, conflictos_docente = auditar_conflictos_oferta(secciones)
    opciones = opciones_por_curso(secciones)
    cursos = sorted((c for c, ops in opciones.items() if ops), key=lambda c: (len(opciones[c]), c))
    vac = vacantes_sin_tope(secciones, opciones)

    if not cursos:
        return ResultadoUCTP([], conflictos_sala, conflictos_docente, vac, 0, 0, "aleatorio", 0.0)

    rng = random.Random(semilla)
    soluciones: list[SolucionHorario] = []
    vistas: set[tuple[tuple[str, tuple[str, ...]], ...]] = set()
    nrcs_usados: set[str] = set()
    contador = [0]

    intentos_max = max(max_horarios * 20, 40)
    for _ in range(intentos_max):
        if len(soluciones) >= max_horarios:
            break
        if disjuntos:
            disp = {
                c: [op for op in opciones[c] if not any(s.nrc in nrcs_usados for s in op.secciones)] for c in cursos
            }
            if any(not disp[c] for c in cursos):
                break
        else:
            disp = opciones
        asignacion = _construir_solucion_aleatoria(cursos, disp, rng, contador)
        if asignacion is None:
            if disjuntos:
                break
            continue
        slots_tot = frozenset().union(*(op.slots for op in asignacion.values()))
        sol = SolucionHorario(asignacion=asignacion, metricas=evaluar_slots(slots_tot, p))
        firma = sol.firma()
        if firma not in vistas:
            vistas.add(firma)
            soluciones.append(sol)
            if disjuntos:
                for op in asignacion.values():
                    nrcs_usados.update(op.nrcs)

    ms = round((time.perf_counter() - t0) * 1000, 3)
    return ResultadoUCTP(
        soluciones=soluciones,
        conflictos_sala=conflictos_sala,
        conflictos_docente=conflictos_docente,
        vacantes_sin_tope=vac,
        nodos_explorados=contador[0],
        nodos_podados=0,
        algoritmo="aleatorio",
        tiempo_ms=ms,
    )


def resolver_branch_and_bound(
    secciones: list[SeccionNRC],
    prefs: PreferenciasUCTP | None = None,
    max_horarios: int = 5,
    disjuntos: bool = False,
    max_nodos: int = 80_000,
) -> ResultadoUCTP:
    """Resuelve UCTP con Branch-and-Bound, ordenamiento MRV y cota inferior admisible.

    Minimiza la función de penalización blanda ``f(x)`` garantizando ``H1 = 0`` (cero
    topes). Cuando ``disjuntos=False`` retorna los ``max_horarios`` horarios óptimos
    distintos ordenados por penalización creciente; cuando ``disjuntos=True`` selecciona
    iterativamente el horario óptimo consumiendo los NRCs elegidos en cada ronda.
    """
    t0 = time.perf_counter()
    p = prefs or PreferenciasUCTP()
    conflictos_sala, conflictos_docente = auditar_conflictos_oferta(secciones)
    opciones = opciones_por_curso(secciones)
    cursos = sorted((c for c, ops in opciones.items() if ops), key=lambda c: (len(opciones[c]), c))
    vac = vacantes_sin_tope(secciones, opciones)

    if not cursos:
        return ResultadoUCTP([], conflictos_sala, conflictos_docente, vac, 0, 0, "branch_and_bound", 0.0)

    nodos_explorados = 0
    nodos_podados = 0

    def buscar_top_k(
        disp: dict[str, list[OpcionCurso]], limite_soluciones: int, presupuesto: int
    ) -> list[SolucionHorario]:
        nonlocal nodos_explorados, nodos_podados
        orden = sorted(cursos, key=lambda c: (len(disp[c]), c))
        max_slots_por_curso = [max((len(op.slots) for op in disp[c]), default=0) for c in orden]
        sufijo_slots = [0] * (len(orden) + 1)
        for i in range(len(orden) - 1, -1, -1):
            sufijo_slots[i] = sufijo_slots[i + 1] + max_slots_por_curso[i]

        mejores: list[SolucionHorario] = []
        vistas: set[tuple[tuple[str, tuple[str, ...]], ...]] = set()
        sel: dict[str, OpcionCurso] = {}
        nodos_locales = 0

        def cota_corte() -> float:
            if len(mejores) < limite_soluciones:
                return math.inf
            return mejores[-1].metricas.penalizacion

        def bt(idx: int, usados: frozenset[tuple[str, int]]) -> None:
            nonlocal nodos_explorados, nodos_podados, nodos_locales
            if nodos_locales >= presupuesto:
                return
            nodos_explorados += 1
            nodos_locales += 1

            if idx == len(orden):
                met = evaluar_slots(usados, p)
                sol = SolucionHorario(asignacion=dict(sel), metricas=met)
                firma = sol.firma()
                if firma not in vistas:
                    vistas.add(firma)
                    mejores.append(sol)
                    mejores.sort(
                        key=lambda s: (s.metricas.penalizacion, s.metricas.ventanas, s.metricas.dias_activos, s.firma())
                    )
                    if len(mejores) > limite_soluciones:
                        descartada = mejores.pop()
                        vistas.discard(descartada.firma())
                return

            limite = cota_corte()
            if limite < math.inf:
                lb = _cota_inferior_admisible(usados, sufijo_slots[idx], p)
                if lb > limite + 1e-9:
                    nodos_podados += 1
                    return

            curso = orden[idx]
            # Ordenar opciones localmente por incremento de penalización (mejor primero)
            cands_factibles = [op for op in disp[curso] if op.slots.isdisjoint(usados)]
            cands_factibles.sort(key=lambda op: (evaluar_slots(usados | op.slots, p).penalizacion, op.nrcs))

            for op in cands_factibles:
                if nodos_locales >= presupuesto:
                    return
                sel[curso] = op
                bt(idx + 1, usados | op.slots)
                del sel[curso]

        bt(0, frozenset())
        return mejores

    soluciones: list[SolucionHorario] = []
    if not disjuntos:
        soluciones = buscar_top_k(opciones, max_horarios, max_nodos)
    else:
        nrcs_usados: set[str] = set()
        presupuesto_ronda = max(max_nodos // max(max_horarios, 1), 2_000)
        for _ in range(max_horarios):
            disp = {
                c: [op for op in opciones[c] if not any(s.nrc in nrcs_usados for s in op.secciones)] for c in cursos
            }
            if any(not disp[c] for c in cursos):
                break
            ronda = buscar_top_k(disp, 1, presupuesto_ronda)
            if not ronda:
                break
            soluciones.append(ronda[0])
            for op in ronda[0].asignacion.values():
                nrcs_usados.update(op.nrcs)

    ms = round((time.perf_counter() - t0) * 1000, 3)
    return ResultadoUCTP(
        soluciones=soluciones,
        conflictos_sala=conflictos_sala,
        conflictos_docente=conflictos_docente,
        vacantes_sin_tope=vac,
        nodos_explorados=nodos_explorados,
        nodos_podados=nodos_podados,
        algoritmo="branch_and_bound",
        tiempo_ms=ms,
    )


def resolver_recocido_simulado(
    secciones: list[SeccionNRC],
    prefs: PreferenciasUCTP | None = None,
    max_horarios: int = 5,
    iteraciones: int = 2_500,
    temp_inicial: float = 12.0,
    enfriamiento: float = 0.996,
    semilla: int = 42,
) -> ResultadoUCTP:
    """Resuelve UCTP mediante Simulated Annealing preservando estrictamente H1 = 0.

    Parte de soluciones iniciales factibles obtenidas por backtracking MRV y explora
    vecindarios de reasignación simple (1 curso) y perturbación por pares (2 cursos)
    aceptando mejoras siempre y empeoramientos con probabilidad ``exp(-delta / T)``.
    """
    t0 = time.perf_counter()
    p = prefs or PreferenciasUCTP()
    conflictos_sala, conflictos_docente = auditar_conflictos_oferta(secciones)
    opciones = opciones_por_curso(secciones)
    cursos = sorted((c for c, ops in opciones.items() if ops), key=lambda c: (len(opciones[c]), c))
    vac = vacantes_sin_tope(secciones, opciones)

    if not cursos:
        return ResultadoUCTP([], conflictos_sala, conflictos_docente, vac, 0, 0, "recocido_simulado", 0.0)

    rng = random.Random(semilla)
    contador = [0]
    inicial = _construir_solucion_aleatoria(cursos, opciones, rng, contador)
    if inicial is None:
        ms = round((time.perf_counter() - t0) * 1000, 3)
        return ResultadoUCTP([], conflictos_sala, conflictos_docente, vac, contador[0], 0, "recocido_simulado", ms)

    actual = dict(inicial)
    slots_actual = frozenset().union(*(op.slots for op in actual.values()))
    met_actual = evaluar_slots(slots_actual, p)

    mejores: dict[tuple[tuple[str, tuple[str, ...]], ...], SolucionHorario] = {}
    sol0 = SolucionHorario(asignacion=dict(actual), metricas=met_actual)
    mejores[sol0.firma()] = sol0

    cursos_variables = [c for c in cursos if len(opciones[c]) > 1]
    temp = temp_inicial

    for _ in range(iteraciones):
        if not cursos_variables:
            break
        contador[0] += 1
        # Movimiento de vecindario: 80% cambio de 1 curso, 20% intercambio simultáneo de 2 cursos
        if len(cursos_variables) >= 2 and rng.random() < 0.20:
            c1, c2 = rng.sample(cursos_variables, 2)
            base_slots = frozenset().union(*(op.slots for k, op in actual.items() if k not in (c1, c2)))
            op1 = rng.choice(opciones[c1])
            if not op1.slots.isdisjoint(base_slots):
                temp *= enfriamiento
                continue
            inter = base_slots | op1.slots
            op2 = rng.choice(opciones[c2])
            if not op2.slots.isdisjoint(inter):
                temp *= enfriamiento
                continue
            cand_slots = inter | op2.slots
            cambios = {c1: op1, c2: op2}
        else:
            c1 = rng.choice(cursos_variables)
            base_slots = frozenset().union(*(op.slots for k, op in actual.items() if k != c1))
            op1 = rng.choice(opciones[c1])
            if op1 == actual[c1] or not op1.slots.isdisjoint(base_slots):
                temp *= enfriamiento
                continue
            cand_slots = base_slots | op1.slots
            cambios = {c1: op1}

        met_cand = evaluar_slots(cand_slots, p)
        delta = met_cand.penalizacion - met_actual.penalizacion
        if delta <= 0 or (temp > 1e-4 and rng.random() < math.exp(-delta / temp)):
            actual.update(cambios)
            met_actual = met_cand
            sol_cand = SolucionHorario(asignacion=dict(actual), metricas=met_cand)
            mejores[sol_cand.firma()] = sol_cand
        temp *= enfriamiento

    ordenadas = sorted(
        mejores.values(),
        key=lambda s: (s.metricas.penalizacion, s.metricas.ventanas, s.metricas.dias_activos, s.firma()),
    )[:max_horarios]

    ms = round((time.perf_counter() - t0) * 1000, 3)
    return ResultadoUCTP(
        soluciones=ordenadas,
        conflictos_sala=conflictos_sala,
        conflictos_docente=conflictos_docente,
        vacantes_sin_tope=vac,
        nodos_explorados=contador[0],
        nodos_podados=0,
        algoritmo="recocido_simulado",
        tiempo_ms=ms,
    )


def optimizar_horarios(
    secciones: list[SeccionNRC],
    prefs: PreferenciasUCTP | None = None,
    algoritmo: str = "branch_and_bound",
    max_horarios: int = 5,
    disjuntos: bool = False,
) -> ResultadoUCTP:
    """Punto de entrada unificado para ejecutar el motor UCTP con la estrategia indicada.

    Args:
        secciones: Oferta de secciones (NRC) del período.
        prefs: Preferencias de jornada y pesos de restricciones blandas.
        algoritmo: ``"branch_and_bound"``, ``"recocido_simulado"`` o ``"aleatorio"``.
        max_horarios: Número máximo de horarios factibles a retornar.
        disjuntos: Si ``True`` intenta no repetir NRCs entre horarios consecutivos.

    Returns:
        ``ResultadoUCTP`` con las mejores soluciones, auditoría H2/H3 y vacantes sin tope.

    Raises:
        ValueError: Si el algoritmo especificado no es reconocido.
    """
    if algoritmo == "branch_and_bound":
        return resolver_branch_and_bound(secciones, prefs=prefs, max_horarios=max_horarios, disjuntos=disjuntos)
    if algoritmo == "recocido_simulado":
        return resolver_recocido_simulado(secciones, prefs=prefs, max_horarios=max_horarios)
    if algoritmo == "aleatorio":
        return resolver_aleatorio(secciones, prefs=prefs, max_horarios=max_horarios, disjuntos=disjuntos)
    raise ValueError(f"Algoritmo UCTP no soportado: {algoritmo!r}")
