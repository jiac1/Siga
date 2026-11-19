"""Evaluación técnica integral y reproducible de SIGA-DSS / Suite UNAB (E3).

Ejecuta y registra métricas verificables reales de todos los módulos:
  1. Curricular Analytics (DAG) sobre las 10 mallas oficiales de Ingeniería UNAB.
  2. Motor híbrido de convalidación (Base vs. Mejorado y desglose por par).
  3. Motor combinatorio UCTP (Aleatorio vs. Branch-and-Bound vs. Simulated Annealing).
  4. Eficiencia operativa (SSO HS256, Mapa de Calor, Estrés de Malla y validación DAG).

Uso:
  python scripts/evaluacion/evaluar_suite.py [--json salida.json]
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "packages" / "suite-sso" / "src"))
sys.path.insert(0, str(RAIZ / "services" / "core"))
sys.path.insert(0, str(RAIZ / "services" / "estres-malla"))
sys.path.insert(0, str(RAIZ / "services" / "mapa-calor"))
sys.path.insert(0, str(RAIZ / "scripts" / "evaluacion"))

import evaluar_motor  # noqa: E402
import evaluar_uctp  # noqa: E402
from heatmap.procesador import procesar_archivo  # noqa: E402
from horarios.motor import (  # noqa: E402
    opciones_por_curso,
    resolver_aleatorio,
    resolver_branch_and_bound,
    resolver_recocido_simulado,
)
from malla.engine import calcular_metricas_grafo, malla_desde_catalogo, procesar as procesar_estres  # noqa: E402
from suite_sso import SuiteIdentity, emitir_token, verificar_token  # noqa: E402


def evaluar_curricular_analytics() -> dict:
    """Evalúa métricas DAG (Heileman et al., 2018) sobre las 10 mallas UNAB."""
    t0 = time.perf_counter()
    mallas_dir = RAIZ / "services" / "portal" / "shared" / "mallas"
    indice = json.loads((mallas_dir / "index.json").read_text(encoding="utf-8"))

    resumen_mallas: list[dict] = []
    top_icinf: list[dict] = []

    for item in indice:
        slug = item["slug"]
        data = json.loads((mallas_dir / f"{slug}.json").read_text(encoding="utf-8"))
        df_malla = malla_desde_catalogo(data["cursos"])
        dag = calcular_metricas_grafo(df_malla)
        por_cod = dag["por_codigo"]
        nombres = {c["codigo"]: c["nombre"] for c in data["cursos"]}
        semestres = {c["codigo"]: c["semestre"] for c in data["cursos"]}

        mas_critico = max(por_cod.items(), key=lambda kv: (kv[1]["complejidad"], kv[1]["factor_bloqueo"]))
        resumen_mallas.append(
            {
                "slug": slug,
                "nombre": data["nombre"],
                "n_cursos": len(data["cursos"]),
                "n_aristas": dag["n_aristas"],
                "n_semestres": data["nSemestres"],
                "tiene_ciclos": dag["tiene_ciclos"],
                "complejidad_total": dag["complejidad_total"],
                "complejidad_promedio": round(dag["complejidad_total"] / len(data["cursos"]), 2),
                "curso_mas_critico": {
                    "codigo": mas_critico[0],
                    "nombre": nombres.get(mas_critico[0], ""),
                    "semestre": semestres.get(mas_critico[0]),
                    **mas_critico[1],
                },
            }
        )

        if slug == "civil-informatica":
            ordenados = sorted(
                por_cod.items(),
                key=lambda kv: (-kv[1]["complejidad"], -kv[1]["factor_bloqueo"], kv[0]),
            )
            for cod, met in ordenados[:10]:
                top_icinf.append(
                    {
                        "codigo": cod,
                        "nombre": nombres.get(cod, ""),
                        "semestre": semestres.get(cod),
                        **met,
                    }
                )

    ms = round((time.perf_counter() - t0) * 1000, 2)
    return {"tiempo_total_ms": ms, "mallas": resumen_mallas, "top_civil_informatica": top_icinf}


def evaluar_convalidacion() -> dict:
    """Evalúa el motor de convalidación globalmente y desglosado por cada par universitario."""
    base = evaluar_motor.cargar_base_unab()
    por_slug = {evaluar_motor.slug_unab(k): v for k, v in base.items()}
    idf = evaluar_motor.construir_idf_global(base)
    conceptos = evaluar_motor.Conceptos.desde_archivo(RAIZ / "data" / "convalidacion" / "conceptos.json")
    gold = json.loads((RAIZ / "data" / "convalidacion" / "evaluacion" / "gold.json").read_text(encoding="utf-8"))

    resultados = {"base": [], "mejorado": []}
    por_par: dict[str, dict[str, list[dict]]] = {}

    t0 = time.perf_counter()
    for caso in gold["casos"]:
        par = f"{caso['origen']}→{caso['destino']}"
        por_par[par] = {"base": [], "mejorado": []}
        indice = evaluar_motor.IndiceCarrera(por_slug[caso["destino"]], idf)
        for nombre, etiqueta in caso["etiquetas"].items():
            aceptables = set(etiqueta) if isinstance(etiqueta, list) else ({etiqueta} if etiqueta else set())
            gold_val = etiqueta if etiqueta else None
            variantes = {
                "base": [dict(c, estado=evaluar_motor.estado_de(c["score"])) for c in indice.evaluar(nombre)],
                "mejorado": evaluar_motor.evaluar_asignatura(indice, conceptos, nombre),
            }
            for variante, cands in variantes.items():
                mejor = cands[0] if cands else None
                pred = mejor["codigo"] if mejor and mejor["estado"] == "convalidable" else None
                ok = (pred in aceptables) if aceptables else pred is None
                fila = {
                    "caso": par,
                    "origen": nombre,
                    "gold": gold_val,
                    "pred": pred,
                    "score": mejor["score"] if mejor else None,
                    "ok": ok,
                    "top3": bool(aceptables & {c["codigo"] for c in cands[:3]}),
                }
                resultados[variante].append(fila)
                por_par[par][variante].append(fila)
    ms_total = round((time.perf_counter() - t0) * 1000, 1)

    # Medición aislada solo del motor mejorado (latencia productiva)
    t1 = time.perf_counter()
    for caso in gold["casos"]:
        indice = evaluar_motor.IndiceCarrera(por_slug[caso["destino"]], idf)
        conceptos_dest = {d.asig.codigo: conceptos.de(d.asig.nombre) for d in indice.docs}
        for nombre in caso["etiquetas"]:
            evaluar_motor.evaluar_asignatura(indice, conceptos, nombre, "", conceptos_dest)
    ms_mejorado = round((time.perf_counter() - t1) * 1000, 1)

    return {
        "conceptos_version": conceptos.version,
        "tiempo_ambas_variantes_ms": ms_total,
        "tiempo_solo_mejorado_ms": ms_mejorado,
        "global": {v: evaluar_motor.metricas(f) for v, f in resultados.items()},
        "por_par": {par: {v: evaluar_motor.metricas(f) for v, f in d.items()} for par, d in por_par.items()},
        "errores_mejorado": [f for f in resultados["mejorado"] if not f["ok"]],
    }


def evaluar_uctp_completo() -> list[dict]:
    """Ejecuta el benchmark UCTP y retorna las métricas por instancia y algoritmo."""
    salida: list[dict] = []
    for nombre, secciones, prefs in evaluar_uctp.construir_benchmark():
        ops = opciones_por_curso(secciones)
        espacio = 1
        for lista in ops.values():
            espacio *= max(len(lista), 1)
        r_base = resolver_aleatorio(secciones, prefs=prefs, max_horarios=5, semilla=42)
        r_bb = resolver_branch_and_bound(secciones, prefs=prefs, max_horarios=5, max_nodos=80_000)
        r_sa = resolver_recocido_simulado(secciones, prefs=prefs, max_horarios=5, iteraciones=2_500, semilla=42)
        fila = {
            "instancia": nombre,
            "espacio_combinatorio": espacio,
            "n_secciones": len(secciones),
            "conflictos_sala": len(r_bb.conflictos_sala),
            "conflictos_docente": len(r_bb.conflictos_docente),
            "resultados": {},
        }
        for r in (r_base, r_bb, r_sa):
            mejor = r.soluciones[0] if r.soluciones else None
            fila["resultados"][r.algoritmo] = {
                "factibles": len(r.soluciones),
                "penalizacion": mejor.metricas.penalizacion if mejor else None,
                "ventanas": mejor.metricas.ventanas if mejor else None,
                "dias_activos": mejor.metricas.dias_activos if mejor else None,
                "exceso_carga": mejor.metricas.exceso_carga_diaria if mejor else None,
                "nodos_explorados": r.nodos_explorados,
                "nodos_podados": r.nodos_podados,
                "tiempo_ms": r.tiempo_ms,
            }
        salida.append(fila)
    return salida


def evaluar_eficiencia_servicios() -> dict:
    """Mide tiempos de ejecución reales de SSO, Mapa de Calor y Estrés de Malla."""
    secreto = "benchmark-suite-unab-secreto-seguro-32-caracteres"
    ident = SuiteIdentity(
        sub="42",
        email="estudiante@unab.cl",
        nombre="Estudiante Prueba",
        organizacion="unab",
        roles=("estudiante",),
        modulos=("malla", "horarios", "convalidacion"),
    )
    n_iter = 1000
    t0 = time.perf_counter()
    for _ in range(n_iter):
        tok = emitir_token(ident, secreto=secreto)
        verificar_token(tok, secreto=secreto)
    sso_us_por_ciclo = round(((time.perf_counter() - t0) * 1_000_000) / n_iter, 1)

    t1 = time.perf_counter()
    with (RAIZ / "services" / "mapa-calor" / "ejemplos" / "mapa_calor_prueba.xlsx").open("rb") as f:
        res_mc = procesar_archivo(f)
    mc_ms = round((time.perf_counter() - t1) * 1000, 1)

    t2 = time.perf_counter()
    res_em = procesar_estres(
        RAIZ / "services" / "estres-malla" / "ejemplos" / "malla.xlsx",
        RAIZ / "services" / "estres-malla" / "ejemplos" / "actas.xlsx",
    )
    em_ms = round((time.perf_counter() - t2) * 1000, 1)

    df_em = res_em["df"]
    top_estres = (
        df_em[~df_em["es_estimado"]]
        .sort_values("indice_estres", ascending=False)
        .head(6)[
            [
                "codigo",
                "nombre",
                "semestre",
                "pct_aprob",
                "factor_bloqueo",
                "factor_retraso",
                "complejidad",
                "indice_estres",
            ]
        ]
        .to_dict(orient="records")
    )

    return {
        "sso_hs256": {"iteraciones": n_iter, "us_por_emision_y_verificacion": sso_us_por_ciclo},
        "mapa_calor": {"tiempo_ms": mc_ms, **res_mc["stats"]},
        "estres_malla": {
            "tiempo_ms": em_ms,
            "n_asignaturas": res_em["n_asignaturas"],
            "n_con_datos": res_em["n_con_datos"],
            "n_criticas": res_em["n_criticas"],
            "pct_promedio": res_em["pct_promedio"],
            "complejidad_total": res_em["complejidad_total"],
            "n_aristas": res_em["n_aristas"],
            "tiene_ciclos": res_em["tiene_ciclos"],
            "top_estres_combinado": top_estres,
        },
    }


def main() -> None:
    """Ejecuta la evaluación completa e imprime un resumen estructurado."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    ap = argparse.ArgumentParser()
    ap.add_argument("--json", help="Guardar el reporte completo en JSON")
    args = ap.parse_args()

    reporte = {
        "curricular_analytics": evaluar_curricular_analytics(),
        "convalidacion": evaluar_convalidacion(),
        "uctp": evaluar_uctp_completo(),
        "eficiencia_servicios": evaluar_eficiencia_servicios(),
    }

    if args.json:
        Path(args.json).write_text(json.dumps(reporte, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(reporte, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
