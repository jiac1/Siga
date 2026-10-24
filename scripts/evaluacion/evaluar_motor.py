"""Evalúa precisión y exhaustividad del motor de convalidación (modo catálogo).

Compara dos variantes sobre data/convalidacion/evaluacion/gold.json:
  base       motor original del cliente (solo similitud de contenidos)
  mejorado   motor de producción: contenidos + conceptos curados + nombres + nivel

Una predicción es la mejor coincidencia UNAB si su estado es "convalidable"
(si no, la predicción es "sin equivalente").

Uso:  python scripts/evaluacion/evaluar_motor.py [--json salida.json]
No requiere Django ni base de datos: usa los mismos JSON que carga core.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "services" / "core"))

from convalidaciones.motor import (  # noqa: E402
    AsignaturaDestino,
    Conceptos,
    IndiceCarrera,
    construir_idf_global,
    estado_de,
    evaluar_asignatura,
)


def cargar_base_unab():
    crudo = json.loads((RAIZ / "data" / "unab" / "base-convalidacion.json").read_text(encoding="utf-8"))
    return {
        nombre: [
            AsignaturaDestino(
                codigo=a["codigo"],
                nombre=a["nombre"],
                contenidos=a.get("contenidos", ""),
                aprendizajes=a.get("aprendizajes", []),
                semestre=a.get("semestre"),
            )
            for a in lista
        ]
        for nombre, lista in crudo.items()
    }


def slug_unab(nombre: str) -> str:
    import re
    import unicodedata

    t = unicodedata.normalize("NFKD", nombre).encode("ascii", "ignore").decode()
    return "unab-" + re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")


def metricas(filas):
    tp = sum(f["ok"] and f["gold"] is not None for f in filas)
    fp = sum(f["pred"] is not None and not f["ok"] for f in filas)
    positivos = sum(f["gold"] is not None for f in filas)
    tn = sum(f["gold"] is None and f["pred"] is None for f in filas)
    negativos = sum(f["gold"] is None for f in filas)
    top3 = sum(f["top3"] for f in filas if f["gold"] is not None)
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / positivos if positivos else 0.0
    return {
        "n": len(filas),
        "positivos": positivos,
        "tp": tp,
        "fp": fp,
        "precision": round(p, 3),
        "exhaustividad": round(r, 3),
        "f1": round(2 * p * r / (p + r), 3) if p + r else 0.0,
        "especificidad": round(tn / negativos, 3) if negativos else None,
        "acierto_top3": round(top3 / positivos, 3) if positivos else None,
    }


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # consola de Windows
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", help="guardar resultados detallados en este archivo")
    ap.add_argument("--min-f1", type=float, default=0.90, help="F1 mínimo requerido para la variante mejorada")
    args = ap.parse_args()

    base = cargar_base_unab()
    por_slug = {slug_unab(k): v for k, v in base.items()}
    idf = construir_idf_global(base)
    conceptos = Conceptos.desde_archivo(RAIZ / "data" / "convalidacion" / "conceptos.json")
    gold = json.loads((RAIZ / "data" / "convalidacion" / "evaluacion" / "gold.json").read_text(encoding="utf-8"))

    resultados = {"base": [], "mejorado": []}
    t0 = time.perf_counter()
    for caso in gold["casos"]:
        indice = IndiceCarrera(por_slug[caso["destino"]], idf)
        for nombre, etiqueta in caso["etiquetas"].items():
            aceptables = set(etiqueta) if isinstance(etiqueta, list) else ({etiqueta} if etiqueta else set())
            gold_val = etiqueta if etiqueta else None
            variantes = {
                "base": [dict(c, estado=estado_de(c["score"])) for c in indice.evaluar(nombre)],
                "mejorado": evaluar_asignatura(indice, conceptos, nombre),
            }
            for variante, cands in variantes.items():
                mejor = cands[0] if cands else None
                pred = mejor["codigo"] if mejor and mejor["estado"] == "convalidable" else None
                ok = (pred in aceptables) if aceptables else pred is None
                resultados[variante].append(
                    {
                        "caso": f"{caso['origen']}→{caso['destino']}",
                        "origen": nombre,
                        "gold": gold_val,
                        "pred": pred,
                        "score": mejor["score"] if mejor else None,
                        "ok": ok,
                        "top3": bool(aceptables & {c["codigo"] for c in cands[:3]}),
                    }
                )
    ms = (time.perf_counter() - t0) * 1000

    resumen = {v: metricas(f) for v, f in resultados.items()}
    n_items = len(resultados["base"])
    print(
        f"Conjunto: {n_items} asignaturas etiquetadas en {len(gold['casos'])} pares de mallas "
        f"(conceptos v{conceptos.version}); tiempo total {ms:.0f} ms (ambas variantes)\n"
    )
    print(f"{'variante':10} {'precisión':>9} {'exhaust.':>9} {'F1':>6} {'especif.':>9} {'top-3':>6}")
    for v, m in resumen.items():
        print(
            f"{v:10} {m['precision']:9.3f} {m['exhaustividad']:9.3f} {m['f1']:6.3f} "
            f"{m['especificidad']:9.3f} {m['acierto_top3']:6.3f}"
        )
    errores = [f for f in resultados["mejorado"] if not f["ok"]]
    if errores:
        print("\nErrores del motor mejorado:")
        for f in errores:
            print(f"  [{f['caso']}] {f['origen']}: esperado {f['gold']}, predicho {f['pred']} ({f['score']})")
    if args.json:
        Path(args.json).write_text(
            json.dumps({"resumen": resumen, "detalle": resultados, "ms": ms}, ensure_ascii=False, indent=1),
            encoding="utf-8",
        )
    f1_mejorado = resumen["mejorado"]["f1"]
    if f1_mejorado < args.min_f1:
        print(
            f"\nERROR: Desempeño insuficiente del motor de convalidación: "
            f"F1={f1_mejorado:.3f} (umbral mínimo requerido: {args.min_f1:.3f})",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
