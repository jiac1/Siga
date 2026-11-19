"""Evalúa precisión, exhaustividad, robustez estadística y generalización del motor de convalidación.

Ejecuta cinco análisis reproducibles sobre data/convalidacion/evaluacion/gold.json (n=112):
1. Comparación de 5 variantes:
   - ``base``: línea base original (solo similitud de contenidos).
   - ``char_ngram``: alternativa sub-léxica sin diccionario (TF-IDF de 3..5-gramas de caracteres + nivel).
   - ``lsa_svd``: alternativa semántica vectorial densa sin diccionario (Truncated SVD / LSA k=32 + nivel).
   - ``sin_conceptos``: ablación léxica pura (Dice-IDF nombres + contenidos + nivel, 0 conceptos manuales).
   - ``mejorado``: motor híbrido de producción (contenidos + Dice-IDF + 50 conceptos + nivel).
2. Intervalos de confianza Bootstrap no paramétrico al 95 % (B=2.000 réplicas, semilla=42).
3. Validación cruzada con separación estricta entre calibración y evaluación:
   - Leave-One-Pair-Out (LOPO) por par universitario con poda de conceptos exclusivos del fold de prueba.
   - 5-Fold Stratified Cross-Validation calibrando umbral tau* en entrenamiento y evaluando en test.
4. Análisis de sensibilidad al umbral de decisión tau en [0.25, 0.60].
"""

from __future__ import annotations

import argparse
import json
import math
import random
import re
import statistics
import sys
import time
import unicodedata
from collections import Counter
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "services" / "core"))

from convalidaciones.motor import (  # noqa: E402
    PENALIZACION_NIVEL,
    UMBRAL_CONVALIDA,
    AsignaturaDestino,
    Conceptos,
    IndiceCarrera,
    construir_idf_global,
    estado_de,
    evaluar_asignatura,
    nivel_de,
    normalizar_nombre,
    tokenizar,
)


def cargar_base_unab() -> dict[str, list[AsignaturaDestino]]:
    """Carga el catálogo oficial UNAB para convalidaciones."""
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
    """Convierte el nombre de carrera UNAB a su slug normalizado."""
    t = unicodedata.normalize("NFKD", nombre).encode("ascii", "ignore").decode()
    return "unab-" + re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")


def _char_ngrams(texto: str, ns: tuple[int, ...] = (3, 4, 5)) -> Counter[str]:
    limpio = f" {normalizar_nombre(texto)} "
    conteo: Counter[str] = Counter()
    for n in ns:
        for i in range(max(0, len(limpio) - n + 1)):
            conteo[limpio[i : i + n]] += 1
    return conteo


class IndiceCharNgram:
    """Alternativa sub-léxica moderna basada en TF-IDF de n-gramas de caracteres (3..5)."""

    def __init__(self, asignaturas: list[AsignaturaDestino], idf_char: dict[str, float]):
        self.idf = idf_char
        self.docs: list[tuple[AsignaturaDestino, dict[str, float]]] = []
        for a in asignaturas:
            texto = f"{a.nombre} {a.nombre} {a.nombre} {a.contenidos}"
            tf = _char_ngrams(texto)
            vec = {g: (1.0 + math.log(f)) * idf_char.get(g, 1.0) for g, f in tf.items()}
            norma = math.sqrt(sum(w * w for w in vec.values())) or 1.0
            self.docs.append((a, {g: w / norma for g, w in vec.items()}))

    def evaluar(self, nombre_origen: str) -> list[dict]:
        """Ordena asignaturas destino por similitud coseno de n-gramas + penalización de nivel."""
        tf = _char_ngrams(nombre_origen)
        vec_q = {g: (1.0 + math.log(f)) * self.idf.get(g, 1.0) for g, f in tf.items()}
        norma_q = math.sqrt(sum(w * w for w in vec_q.values())) or 1.0
        vec_q = {g: w / norma_q for g, w in vec_q.items()}
        n_orig = nivel_de(nombre_origen)

        cands = []
        for asig, vec_d in self.docs:
            chico, grande = (vec_q, vec_d) if len(vec_q) < len(vec_d) else (vec_d, vec_q)
            sim = sum(w * grande.get(g, 0.0) for g, w in chico.items())
            n_dest = nivel_de(asig.nombre)
            if n_orig is not None and n_dest is not None and n_orig != n_dest:
                sim *= PENALIZACION_NIVEL
            cands.append({"codigo": asig.codigo, "nombre": asig.nombre, "score": round(sim, 4)})
        cands.sort(key=lambda c: -c["score"])
        return cands


class IndiceLSA:
    """Alternativa semántica densa vía Latent Semantic Analysis (Truncated SVD k=32)."""

    def __init__(self, base: dict[str, list[AsignaturaDestino]], k: int = 32):
        vistos = set()
        docs_unicos: list[AsignaturaDestino] = []
        for lista in base.values():
            for a in lista:
                if a.codigo not in vistos:
                    vistos.add(a.codigo)
                    docs_unicos.append(a)

        vocab: dict[str, int] = {}
        tfs_docs: list[dict[str, int]] = []
        df: Counter[str] = Counter()
        for a in docs_unicos:
            toks = tokenizar(f"{a.nombre} {a.nombre} {a.nombre} {a.contenidos} {' '.join(a.aprendizajes or [])}")
            tf: Counter[str] = Counter(toks)
            tfs_docs.append(dict(tf))
            for t in tf:
                df[t] += 1
                if t not in vocab:
                    vocab[t] = len(vocab)

        self.vocab = vocab
        n_docs = len(docs_unicos)
        self.idf = {t: math.log((n_docs + 1) / (d + 1)) + 1.0 for t, d in df.items()}

        mat = np.zeros((len(vocab), n_docs), dtype=np.float64)
        for j, tf in enumerate(tfs_docs):
            for t, f in tf.items():
                mat[vocab[t], j] = (1.0 + math.log(f)) * self.idf[t]
            col_norm = np.linalg.norm(mat[:, j])
            if col_norm > 0:
                mat[:, j] /= col_norm

        u, s, _ = np.linalg.svd(mat, full_matrices=False)
        k_eff = min(k, len(s))
        self.proyeccion = u[:, :k_eff]  # (V, k)
        self.emb_codigo: dict[str, np.ndarray] = {}
        for j, a in enumerate(docs_unicos):
            v_lat = mat[:, j] @ self.proyeccion
            norma = float(np.linalg.norm(v_lat)) or 1.0
            self.emb_codigo[a.codigo] = v_lat / norma

    def evaluar(self, asignaturas: list[AsignaturaDestino], nombre_origen: str) -> list[dict]:
        """Evalúa similitud coseno en el espacio latente SVD de 32 dimensiones."""
        toks = tokenizar(nombre_origen)
        vec = np.zeros(len(self.vocab), dtype=np.float64)
        tf = Counter(toks)
        for t, f in tf.items():
            idx = self.vocab.get(t)
            if idx is not None:
                vec[idx] = (1.0 + math.log(f)) * self.idf.get(t, 1.0)
        q_lat = vec @ self.proyeccion
        q_norm = float(np.linalg.norm(q_lat))
        if q_norm > 0:
            q_lat = q_lat / q_norm

        n_orig = nivel_de(nombre_origen)
        cands = []
        for a in asignaturas:
            d_lat = self.emb_codigo[a.codigo]
            sim = float(np.dot(q_lat, d_lat)) if q_norm > 0 else 0.0
            sim = max(0.0, sim)
            n_dest = nivel_de(a.nombre)
            if n_orig is not None and n_dest is not None and n_orig != n_dest:
                sim *= PENALIZACION_NIVEL
            cands.append({"codigo": a.codigo, "nombre": a.nombre, "score": round(sim, 4)})
        cands.sort(key=lambda c: -c["score"])
        return cands


def construir_idf_char_global(base: dict[str, list[AsignaturaDestino]]) -> dict[str, float]:
    """Calcula IDF global de n-gramas de caracteres (3..5) sobre el catálogo UNAB."""
    vistos = set()
    df: Counter[str] = Counter()
    n_docs = 0
    for lista in base.values():
        for a in lista:
            if a.codigo in vistos:
                continue
            vistos.add(a.codigo)
            n_docs += 1
            for g in set(_char_ngrams(f"{a.nombre} {a.contenidos}")):
                df[g] += 1
    return {g: math.log((n_docs + 1) / (d + 1)) + 1.0 for g, d in df.items()}


def evaluar_filas_con_umbral(filas_crudas: list[dict], umbral: float) -> list[dict]:
    """Aplica un umbral de decisión ``umbral`` sobre filas con ``mejor_codigo`` y ``score``."""
    evaluadas = []
    for f in filas_crudas:
        pred = f["mejor_codigo"] if (f["score"] is not None and f["score"] >= umbral) else None
        aceptables = f["aceptables"]
        ok = (pred in aceptables) if aceptables else (pred is None)
        evaluadas.append(
            {
                "caso": f["caso"],
                "origen": f["origen"],
                "gold": f["gold"],
                "pred": pred,
                "score": f["score"],
                "ok": ok,
                "top3": f["top3"],
            }
        )
    return evaluadas


def metricas(filas: list[dict]) -> dict:
    """Calcula precisión, exhaustividad, F1, especificidad y Top-3 sobre una lista de predicciones."""
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
        "negativos": negativos,
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": positivos - tp,
        "precision": round(p, 3),
        "exhaustividad": round(r, 3),
        "f1": round(2 * p * r / (p + r), 3) if p + r else 0.0,
        "especificidad": round(tn / negativos, 3) if negativos else None,
        "acierto_top3": round(top3 / positivos, 3) if positivos else None,
    }


def bootstrap_ic95(filas: list[dict], n_boot: int = 2_000, semilla: int = 42) -> dict[str, list[float]]:
    """Calcula intervalos de confianza Bootstrap percentil al 95 % (B=2.000)."""
    rng = random.Random(semilla)
    n = len(filas)
    muestras: dict[str, list[float]] = {
        "precision": [],
        "exhaustividad": [],
        "f1": [],
        "especificidad": [],
        "acierto_top3": [],
    }
    for _ in range(n_boot):
        replica = [filas[rng.randrange(n)] for _ in range(n)]
        m = metricas(replica)
        for k in muestras:
            if m[k] is not None:
                muestras[k].append(float(m[k]))

    ic: dict[str, list[float]] = {}
    for k, vals in muestras.items():
        vals.sort()
        lo = vals[int(0.025 * len(vals))]
        hi = vals[int(0.975 * len(vals))]
        ic[k] = [round(lo, 3), round(hi, 3)]
    return ic


def calibrar_umbral(filas_train: list[dict], grilla: list[float] | None = None) -> float:
    """Selecciona en entrenamiento el umbral tau que maximiza F1 (desempatando por especificidad)."""
    if grilla is None:
        grilla = [round(0.18 + 0.02 * i, 2) for i in range(25)]
    mejor_tau = UMBRAL_CONVALIDA
    mejor_par = (-1.0, -1.0)
    for tau in grilla:
        m = metricas(evaluar_filas_con_umbral(filas_train, tau))
        par = (m["f1"], m["especificidad"] or 0.0)
        if par > mejor_par:
            mejor_par = par
            mejor_tau = tau
    return mejor_tau


def main() -> None:
    """Ejecuta la evaluación integral del motor de convalidación e imprime resultados."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", help="guardar resultados detallados en este archivo")
    ap.add_argument("--min-f1", type=float, default=0.90, help="F1 mínimo requerido para la variante mejorada")
    args = ap.parse_args()

    base = cargar_base_unab()
    por_slug = {slug_unab(k): v for k, v in base.items()}
    idf = construir_idf_global(base)
    idf_char = construir_idf_char_global(base)
    lsa_global = IndiceLSA(base, k=32)

    conceptos_raw = json.loads((RAIZ / "data" / "convalidacion" / "conceptos.json").read_text(encoding="utf-8"))
    conceptos = Conceptos(conceptos_raw)
    conceptos_vacios = Conceptos({"_version": "ablacion-0", "conceptos": {}})
    gold = json.loads((RAIZ / "data" / "convalidacion" / "evaluacion" / "gold.json").read_text(encoding="utf-8"))

    filas_crudas: dict[str, list[dict]] = {
        "base": [],
        "char_ngram": [],
        "lsa_svd": [],
        "sin_conceptos": [],
        "mejorado": [],
    }

    t0 = time.perf_counter()
    for caso in gold["casos"]:
        asigs_dest = por_slug[caso["destino"]]
        indice = IndiceCarrera(asigs_dest, idf)
        indice_char = IndiceCharNgram(asigs_dest, idf_char)
        par_id = f"{caso['origen']}→{caso['destino']}"

        for nombre, etiqueta in caso["etiquetas"].items():
            aceptables = set(etiqueta) if isinstance(etiqueta, list) else ({etiqueta} if etiqueta else set())
            gold_val = etiqueta if etiqueta else None

            cands_por_var = {
                "base": [dict(c, estado=estado_de(c["score"])) for c in indice.evaluar(nombre)],
                "char_ngram": indice_char.evaluar(nombre),
                "lsa_svd": lsa_global.evaluar(asigs_dest, nombre),
                "sin_conceptos": evaluar_asignatura(indice, conceptos_vacios, nombre),
                "mejorado": evaluar_asignatura(indice, conceptos, nombre),
            }
            for var, cands in cands_por_var.items():
                mejor = cands[0] if cands else None
                filas_crudas[var].append(
                    {
                        "caso": par_id,
                        "origen": nombre,
                        "gold": gold_val,
                        "aceptables": aceptables,
                        "mejor_codigo": mejor["codigo"] if mejor else None,
                        "score": mejor["score"] if mejor else None,
                        "top3": bool(aceptables & {c["codigo"] for c in cands[:3]}),
                    }
                )
    ms = (time.perf_counter() - t0) * 1000.0

    # Umbrales de operación: 0.45 estándar para base/sin_conceptos/mejorado; calibrado CV para baselines densos
    umbrales_var = {
        "base": UMBRAL_CONVALIDA,
        "char_ngram": calibrar_umbral(filas_crudas["char_ngram"]),
        "lsa_svd": calibrar_umbral(filas_crudas["lsa_svd"]),
        "sin_conceptos": UMBRAL_CONVALIDA,
        "mejorado": UMBRAL_CONVALIDA,
    }

    resultados = {v: evaluar_filas_con_umbral(filas_crudas[v], umbrales_var[v]) for v in filas_crudas}
    resumen = {}
    for v, filas in resultados.items():
        m = metricas(filas)
        m["umbral"] = umbrales_var[v]
        m["ic95"] = bootstrap_ic95(filas)
        resumen[v] = m

    # 3. Validación cruzada Leave-One-Pair-Out (LOPO) con poda de conceptos exclusivos del par de prueba
    pares_unicos = [f"{c['origen']}→{c['destino']}" for c in gold["casos"]]
    lopo_folds = []
    lopo_preds_test: list[dict] = []
    lopo_poda_preds_test: list[dict] = []

    for caso_test in gold["casos"]:
        par_test = f"{caso_test['origen']}→{caso_test['destino']}"
        train_rows = [r for r in filas_crudas["mejorado"] if r["caso"] != par_test]
        test_rows = [r for r in filas_crudas["mejorado"] if r["caso"] == par_test]
        tau_star = calibrar_umbral(train_rows)
        eval_test = evaluar_filas_con_umbral(test_rows, tau_star)
        lopo_preds_test.extend(eval_test)

        # Podar conceptos: conservar solo conceptos que se activan en los nombres de los 2 pares de entrenamiento
        conceptos_activos_train: set[str] = set()
        for c_tr in gold["casos"]:
            if f"{c_tr['origen']}→{c_tr['destino']}" == par_test:
                continue
            for nom_tr in c_tr["etiquetas"]:
                conceptos_activos_train.update(conceptos.de(nom_tr))
        conceptos_podados = Conceptos(
            {
                "_version": "lopo-pruned",
                "conceptos": {k: v for k, v in conceptos_raw["conceptos"].items() if k in conceptos_activos_train},
            }
        )
        ind_test = IndiceCarrera(por_slug[caso_test["destino"]], idf)
        crudos_podados = []
        for nombre, etiqueta in caso_test["etiquetas"].items():
            aceptables = set(etiqueta) if isinstance(etiqueta, list) else ({etiqueta} if etiqueta else set())
            cands = evaluar_asignatura(ind_test, conceptos_podados, nombre)
            mejor = cands[0] if cands else None
            crudos_podados.append(
                {
                    "caso": par_test,
                    "origen": nombre,
                    "gold": etiqueta if etiqueta else None,
                    "aceptables": aceptables,
                    "mejor_codigo": mejor["codigo"] if mejor else None,
                    "score": mejor["score"] if mejor else None,
                    "top3": bool(aceptables & {c["codigo"] for c in cands[:3]}),
                }
            )
        eval_podado = evaluar_filas_con_umbral(crudos_podados, tau_star)
        lopo_poda_preds_test.extend(eval_podado)

        m_fold = metricas(eval_test)
        m_poda = metricas(eval_podado)
        lopo_folds.append(
            {
                "par_test": par_test,
                "n_test": len(test_rows),
                "tau_calibrado_en_train": tau_star,
                "conceptos_activos_train": len(conceptos_activos_train),
                "f1_test": m_fold["f1"],
                "precision_test": m_fold["precision"],
                "exhaustividad_test": m_fold["exhaustividad"],
                "f1_test_conceptos_podados": m_poda["f1"],
                "precision_podados": m_poda["precision"],
                "exhaustividad_podados": m_poda["exhaustividad"],
            }
        )

    # 5-Fold Stratified Cross-Validation
    pos_rows = [r for r in filas_crudas["mejorado"] if r["gold"] is not None]
    neg_rows = [r for r in filas_crudas["mejorado"] if r["gold"] is None]
    rng_cv = random.Random(42)
    rng_cv.shuffle(pos_rows)
    rng_cv.shuffle(neg_rows)
    folds_5: list[list[dict]] = [[] for _ in range(5)]
    for idx, r in enumerate(pos_rows + neg_rows):
        folds_5[idx % 5].append(r)

    cv5_preds: list[dict] = []
    cv5_f1s: list[float] = []
    for k_idx in range(5):
        te = folds_5[k_idx]
        tr = [r for i, f in enumerate(folds_5) if i != k_idx for r in f]
        tau_k = calibrar_umbral(tr)
        ev_k = evaluar_filas_con_umbral(te, tau_k)
        cv5_preds.extend(ev_k)
        cv5_f1s.append(metricas(ev_k)["f1"])

    # 4. Sensibilidad al umbral tau
    sensibilidad = []
    for tau in (0.25, 0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60):
        m_mej = metricas(evaluar_filas_con_umbral(filas_crudas["mejorado"], tau))
        m_sin = metricas(evaluar_filas_con_umbral(filas_crudas["sin_conceptos"], tau))
        sensibilidad.append(
            {
                "umbral_tau": tau,
                "precision": m_mej["precision"],
                "exhaustividad": m_mej["exhaustividad"],
                "f1": m_mej["f1"],
                "especificidad": m_mej["especificidad"],
                "f1_sin_conceptos": m_sin["f1"],
            }
        )

    n_items = len(resultados["base"])
    print(
        f"Conjunto: {n_items} asignaturas etiquetadas en {len(pares_unicos)} pares de mallas "
        f"(conceptos v{conceptos.version}); tiempo total {ms:.0f} ms\n"
    )
    print(
        f"{'variante':14} {'tau':>5} {'precisión':>9} {'exhaust.':>9} "
        f"{'F1':>6} {'IC95% F1':>15} {'especif.':>9} {'top-3':>6}"
    )
    for v, m in resumen.items():
        ic_f1 = f"[{m['ic95']['f1'][0]:.3f}, {m['ic95']['f1'][1]:.3f}]"
        print(
            f"{v:14} {m['umbral']:5.2f} {m['precision']:9.3f} {m['exhaustividad']:9.3f} "
            f"{m['f1']:6.3f} {ic_f1:>15} {m['especificidad']:9.3f} {m['acierto_top3']:6.3f}"
        )

    m_lopo = metricas(lopo_preds_test)
    m_lopo_poda = metricas(lopo_poda_preds_test)
    m_cv5 = metricas(cv5_preds)
    print(
        f"\nValidación Cruzada Out-of-Sample:"
        f"\n  - LOPO (3 pares, tau* calibrado en 2 pares): F1={m_lopo['f1']:.3f} "
        f"(P={m_lopo['precision']:.3f}, R={m_lopo['exhaustividad']:.3f})"
        f"\n  - LOPO con poda de conceptos exclusivos:     F1={m_lopo_poda['f1']:.3f} "
        f"(P={m_lopo_poda['precision']:.3f}, R={m_lopo_poda['exhaustividad']:.3f})"
        f"\n  - 5-Fold Stratified CV (n=112):              F1={m_cv5['f1']:.3f} "
        f"(media folds={statistics.mean(cv5_f1s):.3f} ± {statistics.stdev(cv5_f1s):.3f})"
    )

    errores = [f for f in resultados["mejorado"] if not f["ok"]]
    if errores:
        print("\nErrores del motor mejorado:")
        for f in errores:
            print(f"  [{f['caso']}] {f['origen']}: esperado {f['gold']}, predicho {f['pred']} ({f['score']})")

    salida_json = {
        "resumen": resumen,
        "validacion_cruzada": {
            "lopo_global": m_lopo,
            "lopo_conceptos_podados": m_lopo_poda,
            "lopo_por_par": lopo_folds,
            "cv5_global": m_cv5,
            "cv5_f1_media": round(statistics.mean(cv5_f1s), 3),
            "cv5_f1_std": round(statistics.stdev(cv5_f1s), 3),
        },
        "sensibilidad_umbral": sensibilidad,
        "detalle": {k: resultados[k] for k in ("base", "mejorado")},
        "ms": round(ms, 2),
    }

    if args.json:
        Path(args.json).write_text(json.dumps(salida_json, ensure_ascii=False, indent=2), encoding="utf-8")

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
