"""Casos de uso de convalidación sobre el catálogo persistido en core."""

from __future__ import annotations

import threading
from functools import lru_cache
from pathlib import Path

from django.conf import settings
from django.db.models import Count, Max

from catalogo.models import Asignatura, Carrera

from .models import Equivalencia
from .motor import AsignaturaDestino, Conceptos, IndiceCarrera, construir_idf_global, evaluar_asignatura

TOP_SUGERENCIAS = 3

_lock = threading.Lock()
_cache: dict = {"firma": None, "idf": None, "indices": {}}


@lru_cache(maxsize=1)
def conceptos() -> Conceptos:
    return Conceptos.desde_archivo(Path(settings.DATA_DIR) / "convalidacion" / "conceptos.json")


def _qs_destino():
    return Asignatura.objects.filter(carrera__universidad__es_destino=True, generica=False)


def _firma():
    agg = _qs_destino().aggregate(n=Count("id"), m=Max("id"))
    return (agg["n"], agg["m"])


def _a_destino(a: Asignatura) -> AsignaturaDestino:
    return AsignaturaDestino(
        codigo=a.codigo or f"id{a.pk}",
        nombre=a.nombre,
        contenidos=a.contenidos,
        aprendizajes=a.aprendizajes or [],
        semestre=a.semestre,
        creditos=a.creditos,
    )


def indice_para(carrera: Carrera) -> IndiceCarrera:
    """Índice de la carrera destino; se reconstruye solo si el catálogo UNAB cambió."""
    with _lock:
        firma = _firma()
        if _cache["firma"] != firma:
            base: dict[str, list[AsignaturaDestino]] = {}
            for a in _qs_destino().select_related("carrera"):
                base.setdefault(a.carrera.slug, []).append(_a_destino(a))
            _cache.update(firma=firma, idf=construir_idf_global(base), indices={})
        if carrera.slug not in _cache["indices"]:
            asignaturas = [_a_destino(a) for a in _qs_destino().filter(carrera=carrera)]
            _cache["indices"][carrera.slug] = IndiceCarrera(asignaturas, _cache["idf"])
        return _cache["indices"][carrera.slug]


def _precedente(asignatura_origen_id: int | None, carrera_destino: Carrera):
    if not asignatura_origen_id:
        return None
    eq = (
        Equivalencia.objects.filter(
            origen_id=asignatura_origen_id, destino__carrera=carrera_destino, estado=Equivalencia.Estado.APROBADA
        )
        .select_related("destino")
        .first()
    )
    if eq is None:
        return None
    d = eq.destino
    return {
        "codigo": d.codigo,
        "nombre": d.nombre,
        "semestre": d.semestre,
        "creditos": d.creditos,
        "score": 1.0,
        "estado": "convalidable",
        "fuente": "precedente",
        "destino_id": d.pk,
    }


def sugerir(carrera_destino: Carrera, items: list[dict]) -> list[dict]:
    """Para cada asignatura de origen devuelve las mejores coincidencias UNAB.

    items: [{"nombre": str, "texto": str opcional, "asignatura_origen_id": int opcional}]

    Con `texto` (programa completo) manda el motor por contenidos; sin texto
    (solo nombre, como en el catálogo de mallas) se combina con conceptos
    curados y similitud de nombres. Un precedente aprobado tiene prioridad.
    """
    indice = indice_para(carrera_destino)
    dicc = conceptos()
    por_codigo = {a.codigo: a.pk for a in _qs_destino().filter(carrera=carrera_destino)}
    conceptos_destino = {d.asig.codigo: dicc.de(d.asig.nombre) for d in indice.docs}
    salida = []
    for item in items:
        nombre = (item.get("nombre") or "").strip()
        candidatos = evaluar_asignatura(indice, dicc, nombre, item.get("texto") or "", conceptos_destino)
        for c in candidatos[:TOP_SUGERENCIAS]:
            c["fuente"] = "motor"
            c["destino_id"] = por_codigo.get(c["codigo"])
        top = candidatos[:TOP_SUGERENCIAS]
        prec = _precedente(item.get("asignatura_origen_id"), carrera_destino)
        if prec:
            top = [prec] + [c for c in top if c["codigo"] != prec["codigo"]][: TOP_SUGERENCIAS - 1]
        salida.append(
            {
                "nombre": nombre,
                "asignatura_origen_id": item.get("asignatura_origen_id"),
                "mejor": top[0] if top else None,
                "candidatos": top,
            }
        )
    return salida
