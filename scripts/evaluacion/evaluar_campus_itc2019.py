"""Evaluación del solver global de asignación de campus sobre datasets ITC-2019.

Carga todas las salas, clases, dominios ``(tiempo, sala)``, restricciones duras
``NotOverlap``/``SameAttendees`` y la co-inscripción de todos los estudiantes reales de
cada XML oficial ITC-2019, comparando la línea base aleatoria contra el solver global
(Constructivo MRV + Simulated Annealing).
"""

from __future__ import annotations

import argparse
import gzip
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "services" / "core"))

from horarios.campus import (  # noqa: E402
    CandidatoSala,
    CandidatoTemporal,
    ClaseCampus,
    RestriccionDistribucion,
    SalaCampus,
    resolver_campus_aleatorio,
    resolver_campus_global,
)
from horarios.motor import DIAS_ORDEN  # noqa: E402

INSTANCIAS_ITC2019 = [
    ("muni-fi-spr16_reduced.xml.gz", "Masaryk Univ. · Informática (muni-fi-spr16)"),
    ("muni-fsps-spr17_reduced.xml.gz", "Masaryk Univ. · Cs. Deporte (muni-fsps-spr17)"),
    ("yach-fal17_reduced.xml.gz", "Yachay Tech · Pregrado (yach-fal17)"),
]


def _slot_itc_a_modulo(slot: int) -> int:
    mod = ((slot - 96) // 12) + 1
    return max(1, min(20, mod))


def _cargar_campus_itc2019(
    ruta_gz: Path,
) -> tuple[list[ClaseCampus], list[SalaCampus], list[list[str]], list[RestriccionDistribucion]]:
    """Parsea un XML ITC-2019 completo a estructuras de asignación global de campus."""
    with gzip.open(ruta_gz, "rb") as f:
        root = ET.parse(f).getroot()

    salas: list[SalaCampus] = []
    for r_el in root.findall("./rooms/room"):
        salas.append(SalaCampus(id_sala=r_el.attrib["id"], capacidad=int(r_el.attrib.get("capacity", "30"))))

    clases: list[ClaseCampus] = []
    for course_el in root.findall("./courses/course"):
        cid = f"C{course_el.attrib['id']}"
        cfg = course_el.find("./config")
        if cfg is None:
            continue
        for sub_idx, sub_el in enumerate(cfg.findall("./subpart")):
            act = f"S{sub_idx + 1}"
            for cls_el in sub_el.findall("./class"):
                cls_id = cls_el.attrib["id"]
                limit = int(cls_el.attrib.get("limit", "30"))

                tiempos_vistos: dict[tuple[tuple[str, int], ...], int] = {}
                for t_el in cls_el.findall("./time"):
                    pen = int(t_el.attrib.get("penalty", "0"))
                    start = int(t_el.attrib["start"])
                    end_excl = max(start + 1, start + int(t_el.attrib["length"]))
                    slots_tuple = tuple(
                        sorted(
                            {
                                (DIAS_ORDEN[d_idx], _slot_itc_a_modulo(s))
                                for d_idx, flag in enumerate(t_el.attrib["days"][:6])
                                if flag == "1"
                                for s in range(start, end_excl, 5)
                            }
                        )
                    )
                    if slots_tuple and (slots_tuple not in tiempos_vistos or pen < tiempos_vistos[slots_tuple]):
                        tiempos_vistos[slots_tuple] = pen

                cands_tiempo = tuple(
                    CandidatoTemporal(slots=sl, penalizacion=pen)
                    for sl, pen in sorted(tiempos_vistos.items(), key=lambda x: x[1])
                )
                cands_sala = tuple(
                    sorted(
                        (
                            CandidatoSala(id_sala=r.attrib["id"], penalizacion=int(r.attrib.get("penalty", "0")))
                            for r in cls_el.findall("./room")
                        ),
                        key=lambda x: x.penalizacion,
                    )
                )
                if cands_tiempo:
                    clases.append(
                        ClaseCampus(
                            id_clase=cls_id,
                            curso=cid,
                            actividad=act,
                            cupo=limit,
                            candidatos_tiempo=cands_tiempo,
                            candidatos_sala=cands_sala,
                        )
                    )

    perfiles = [
        [f"C{c.attrib['id']}" for c in st_el.findall("./course")] for st_el in root.findall("./students/student")
    ]

    restricciones: list[RestriccionDistribucion] = []
    for d_el in root.findall("./distributions/distribution"):
        tipo = d_el.attrib.get("type", "")
        if tipo in ("NotOverlap", "SameAttendees") and d_el.attrib.get("required") == "true":
            ids = tuple(c.attrib["id"] for c in d_el.findall("./class"))
            if len(ids) >= 2:
                restricciones.append(RestriccionDistribucion(tipo=tipo, clases=ids, requerida=True))

    return clases, salas, perfiles, restricciones


def main() -> None:
    """Ejecuta el benchmark de asignación global de campus sobre los 3 XML ITC-2019."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    ap = argparse.ArgumentParser()
    ap.add_argument("--iteraciones", type=int, default=2_500, help="Iteraciones de Simulated Annealing global")
    ap.add_argument("--json", help="Guardar resultados JSON")
    args = ap.parse_args()

    bench_dir = RAIZ / "data" / "benchmarks" / "itc2019"
    salida = []

    print(
        f"{'Campus ITC-2019':42} {'Algoritmo':18} {'Asignadas':>11} {'H2':>4} {'Cap':>4} "
        f"{'Dist':>5} {'Conf.Est':>9} {'Obj.Total':>10} {'ms':>8}"
    )
    print("-" * 120)

    for archivo, etiqueta in INSTANCIAS_ITC2019:
        clases, salas, perfiles, restricciones = _cargar_campus_itc2019(bench_dir / archivo)
        base = resolver_campus_aleatorio(clases, salas, perfiles_estudiantes=perfiles, restricciones=restricciones)
        opt = resolver_campus_global(
            clases,
            salas,
            perfiles_estudiantes=perfiles,
            restricciones=restricciones,
            iteraciones=args.iteraciones,
        )

        for r in (base, opt):
            m = r.metricas
            print(
                f"{etiqueta:42} {r.algoritmo:18} "
                f"{m.clases_asignadas:4d}/{m.total_clases:<6d} "
                f"{m.conflictos_sala_h2:4d} {m.conflictos_capacidad:4d} "
                f"{m.conflictos_distribucion_dura:5d} {m.conflictos_estudiantes:9d} "
                f"{m.penalizacion_total:10.1f} {r.tiempo_ms:8.1f}"
            )

        salida.append(
            {
                "etiqueta": etiqueta,
                "n_clases": len(clases),
                "n_salas": len(salas),
                "n_estudiantes": len(perfiles),
                "n_restricciones_duras": len(restricciones),
                "campus_aleatorio": {
                    **base.metricas.__dict__,
                    "tiempo_ms": base.tiempo_ms,
                },
                "campus_global_sa": {
                    **opt.metricas.__dict__,
                    "tiempo_ms": opt.tiempo_ms,
                },
            }
        )

    if args.json:
        Path(args.json).write_text(json.dumps(salida, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
