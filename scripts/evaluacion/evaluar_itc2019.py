"""Evalúa el motor UCTP de SIGA-DSS sobre instancias oficiales de ITC-2019.

Carga conjuntos reales de la International Timetabling Competition 2019 (ITC-2019,
formato XML comprimido en ``data/benchmarks/itc2019/``), extrae perfiles reales de
inscripción estudiantil y compara las tres estrategias del motor UCTP
(``aleatorio``, ``branch_and_bound`` y ``recocido_simulado``) en términos de
factibilidad (H1 = 0), función objetivo f(x), ventanas horarias, nodos y tiempo.

Uso:
  python scripts/evaluacion/evaluar_itc2019.py [--max-perfiles 30] [--json salida.json]
"""

from __future__ import annotations

import argparse
import gzip
import json
import statistics
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "services" / "core"))

from horarios.motor import (  # noqa: E402
    DIAS_ORDEN,
    BloqueHorario,
    PreferenciasUCTP,
    SeccionNRC,
    resolver_aleatorio,
    resolver_branch_and_bound,
    resolver_recocido_simulado,
)

INSTANCIAS_ITC2019 = (
    ("muni-fi-spr16_reduced.xml.gz", "Masaryk Univ. · Informática (muni-fi-spr16)"),
    ("muni-fsps-spr17_reduced.xml.gz", "Masaryk Univ. · Cs. Deporte (muni-fsps-spr17)"),
    ("yach-fal17_reduced.xml.gz", "Yachay Tech · Pregrado (yach-fal17)"),
)


def _slot_itc_a_modulo(slot_5min: int) -> int:
    """Mapea un slot de 5 minutos (ITC-2019) a módulos académicos discretos M1..M20."""
    # M1..M14 cubren 07:00..18:40 (slots 84..223); M15..M20 cubren 18:40..23:40
    if slot_5min < 224:
        return max(1, min(14, (slot_5min - 84) // 10 + 1))
    return max(15, min(20, 15 + (slot_5min - 224) // 10))


def _cargar_instancia_itc2019(ruta_gz: Path) -> tuple[dict[str, list[SeccionNRC]], list[list[str]], dict]:
    """Parsea un XML comprimido de ITC-2019 y construye secciones + perfiles de estudiantes."""
    with gzip.open(ruta_gz, "rb") as f:
        root = ET.parse(f).getroot()

    secciones_por_curso: dict[str, list[SeccionNRC]] = {}
    total_clases = 0

    for course_el in root.findall("./courses/course"):
        cid = course_el.attrib["id"]
        cfg = course_el.find("./config")
        if cfg is None:
            continue
        secs_curso: list[SeccionNRC] = []
        for sub_idx, sub_el in enumerate(cfg.findall("./subpart")):
            act = f"S{sub_idx + 1}"
            for cls_el in sub_el.findall("./class"):
                total_clases += 1
                cls_id = cls_el.attrib["id"]
                limit = int(cls_el.attrib.get("limit", "30"))

                rooms = sorted(
                    cls_el.findall("./room"),
                    key=lambda r: (int(r.attrib.get("penalty", "0")), r.attrib["id"]),
                )
                rid = rooms[0].attrib["id"] if rooms else ""
                times = sorted(
                    cls_el.findall("./time"),
                    key=lambda t: (
                        int(t.attrib.get("penalty", "0")),
                        int(t.attrib["start"]),
                        t.attrib["days"],
                    ),
                )
                for t_idx, t_el in enumerate(times[:3]):
                    days_mask = t_el.attrib["days"]
                    start = int(t_el.attrib["start"])
                    length = int(t_el.attrib["length"])
                    end_excl = max(start + 1, start + length)

                    bloques: list[BloqueHorario] = []
                    for d_idx, flag in enumerate(days_mask[:6]):
                        if flag != "1":
                            continue
                        dia = DIAS_ORDEN[d_idx]
                        for mod in sorted({_slot_itc_a_modulo(s) for s in range(start, end_excl, 5)}):
                            bloques.append(BloqueHorario(dia=dia, modulo=mod, sala=rid, edificio="ITC" if rid else ""))
                    if bloques:
                        secs_curso.append(
                            SeccionNRC(
                                nrc=f"{cid}-{cls_id}-t{t_idx}",
                                curso=f"C{cid}",
                                actividad=act,
                                bloques=tuple(bloques),
                                cupos=limit,
                            )
                        )
        if secs_curso:
            secciones_por_curso[f"C{cid}"] = secs_curso

    perfiles_vistos: set[tuple[str, ...]] = set()
    perfiles: list[list[str]] = []
    students = root.findall("./students/student")
    for st_el in students:
        cursos = sorted(
            {f"C{c.attrib['id']}" for c in st_el.findall("./course") if f"C{c.attrib['id']}" in secciones_por_curso}
        )
        if 3 <= len(cursos) <= 8:
            clave = tuple(cursos)
            if clave not in perfiles_vistos:
                perfiles_vistos.add(clave)
                perfiles.append(cursos)

    meta = {
        "nombre_xml": root.attrib.get("name", ruta_gz.stem),
        "n_cursos_xml": len(root.findall("./courses/course")),
        "n_clases_xml": total_clases,
        "n_salas_xml": len(root.findall("./rooms/room")),
        "n_estudiantes_xml": len(students),
        "perfiles_unicos_3a8": len(perfiles),
    }
    return secciones_por_curso, perfiles, meta


def evaluar_dataset(ruta_gz: Path, etiqueta: str, max_perfiles: int) -> dict:
    """Evalúa los 3 algoritmos sobre hasta ``max_perfiles`` perfiles reales del dataset."""
    secs_por_curso, perfiles, meta = _cargar_instancia_itc2019(ruta_gz)
    muestra = perfiles[:max_perfiles]
    prefs = PreferenciasUCTP(jornada="cualquiera")

    acum = {
        alg: {"evaluados": 0, "factibles": 0, "f": [], "ventanas": [], "dias": [], "ms": [], "nodos": [], "podados": []}
        for alg in ("aleatorio", "branch_and_bound", "recocido_simulado")
    }

    for cursos in muestra:
        secciones = [s for c in cursos for s in secs_por_curso[c]]
        r_base = resolver_aleatorio(secciones, prefs=prefs, max_horarios=3, semilla=42)
        r_bb = resolver_branch_and_bound(secciones, prefs=prefs, max_horarios=3, max_nodos=20_000)
        r_sa = resolver_recocido_simulado(secciones, prefs=prefs, max_horarios=3, iteraciones=1_200, semilla=42)

        for r in (r_base, r_bb, r_sa):
            d = acum[r.algoritmo]
            d["evaluados"] += 1
            d["ms"].append(r.tiempo_ms)
            d["nodos"].append(r.nodos_explorados)
            d["podados"].append(r.nodos_podados)
            if r.soluciones:
                d["factibles"] += 1
                m = r.soluciones[0].metricas
                d["f"].append(m.penalizacion)
                d["ventanas"].append(m.ventanas)
                d["dias"].append(m.dias_activos)

    resumen = {}
    for alg, d in acum.items():
        resumen[alg] = {
            "evaluados": d["evaluados"],
            "factibles": d["factibles"],
            "tasa_factibilidad_pct": round(100.0 * d["factibles"] / d["evaluados"], 1) if d["evaluados"] else 0.0,
            "f_promedio": round(statistics.mean(d["f"]), 2) if d["f"] else None,
            "ventanas_promedio": round(statistics.mean(d["ventanas"]), 2) if d["ventanas"] else None,
            "dias_promedio": round(statistics.mean(d["dias"]), 2) if d["dias"] else None,
            "tiempo_promedio_ms": round(statistics.mean(d["ms"]), 2) if d["ms"] else 0.0,
            "nodos_promedio": round(statistics.mean(d["nodos"]), 1) if d["nodos"] else 0.0,
            "podados_promedio": round(statistics.mean(d["podados"]), 1) if d["podados"] else 0.0,
        }

    # Reducción porcentual emparejada en perfiles donde ambos hallaron solución factible
    f_base = resumen["aleatorio"]["f_promedio"]
    f_bb = resumen["branch_and_bound"]["f_promedio"]
    w_base = resumen["aleatorio"]["ventanas_promedio"]
    w_bb = resumen["branch_and_bound"]["ventanas_promedio"]

    return {
        "etiqueta": etiqueta,
        "meta": meta,
        "muestra_perfiles": len(muestra),
        "reduccion_f_bb_pct": round(100.0 * (f_base - f_bb) / f_base, 1) if f_base and f_bb is not None else None,
        "reduccion_ventanas_bb_pct": round(100.0 * (w_base - w_bb) / w_base, 1)
        if w_base and w_bb is not None
        else None,
        "resultados": resumen,
    }


def main() -> None:
    """Ejecuta la evaluación sobre los datasets ITC-2019 e imprime la tabla comparativa."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    ap = argparse.ArgumentParser()
    ap.add_argument("--max-perfiles", type=int, default=30, help="Máximo de perfiles estudiantiles por dataset")
    ap.add_argument("--json", help="Guardar salida JSON detallada")
    args = ap.parse_args()

    bench_dir = RAIZ / "data" / "benchmarks" / "itc2019"
    reporte = []

    print(f"{'Dataset ITC-2019':42} {'Algoritmo':18} {'Fact.':>7} {'f(x) prom':>10} {'Vent. prom':>10} {'ms prom':>9}")
    print("-" * 102)

    for archivo, etiqueta in INSTANCIAS_ITC2019:
        res = evaluar_dataset(bench_dir / archivo, etiqueta, args.max_perfiles)
        reporte.append(res)
        for alg in ("aleatorio", "branch_and_bound", "recocido_simulado"):
            r = res["resultados"][alg]
            f_txt = f"{r['f_promedio']:.2f}" if r["f_promedio"] is not None else "—"
            w_txt = f"{r['ventanas_promedio']:.2f}" if r["ventanas_promedio"] is not None else "—"
            print(
                f"{etiqueta:42} {alg:18} "
                f"{r['factibles']:2d}/{r['evaluados']:<4d} "
                f"{f_txt:>10} {w_txt:>10} {r['tiempo_promedio_ms']:9.2f}"
            )

    if args.json:
        Path(args.json).write_text(json.dumps(reporte, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
