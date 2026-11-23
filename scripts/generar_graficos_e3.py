"""Genera gráficos académicos de alta resolución (300 DPI) para el Informe Final E3.

Consume la salida JSON reproducible de ``scripts/evaluacion/evaluar_suite.py`` para
garantizar que cada cifra graficada corresponda exactamente a mediciones verificables.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts" / "evaluacion"))

import evaluar_suite  # noqa: E402

INK = "#191B16"
BRAND = "#1D6B55"
TEAL = "#0C8599"
BLUE = "#3F62E0"
AMBER = "#D89B1E"
CRIMSON = "#C73C2E"
SLATE = "#8E9189"
BG_PANEL = "#F6F6F2"

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "axes.edgecolor": "#DEDED7",
        "axes.linewidth": 0.8,
        "axes.facecolor": "#FFFFFF",
        "figure.facecolor": "#FFFFFF",
        "text.color": INK,
        "axes.labelcolor": INK,
        "xtick.color": INK,
        "ytick.color": INK,
    }
)


def _graficar_convalidacion(conv: dict, salida: Path) -> None:
    """Genera el gráfico comparativo del motor de convalidación IA (ablación, CV, IC95% y sensibilidad)."""
    det_path = salida.parent / "metricas_convalidacion_detalladas.json"
    if not det_path.exists():
        return
    det = json.loads(det_path.read_text(encoding="utf-8"))
    res = det["resumen"]
    cv = det["validacion_cruzada"]
    sens = det["sensibilidad_umbral"]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.6, 5.0), dpi=300)

    etiquetas = [
        "Base\n(Contenidos)",
        "LSA / SVD\nDenso (k=32)",
        "Char n-gram\n(3–5 gramas)",
        "Ablación\n(0 Conceptos)",
        "LOPO CV\n(Poda Conc.)",
        "LOPO CV\n(3 Pares)",
        "Híbrido\nProducción",
    ]
    f1_vals = [
        res["base"]["f1"],
        res["lsa_svd"]["f1"],
        res["char_ngram"]["f1"],
        res["sin_conceptos"]["f1"],
        cv["lopo_conceptos_podados"]["f1"],
        cv["lopo_global"]["f1"],
        res["mejorado"]["f1"],
    ]
    p_vals = [
        res["base"]["precision"],
        res["lsa_svd"]["precision"],
        res["char_ngram"]["precision"],
        res["sin_conceptos"]["precision"],
        cv["lopo_conceptos_podados"]["precision"],
        cv["lopo_global"]["precision"],
        res["mejorado"]["precision"],
    ]
    r_vals = [
        res["base"]["exhaustividad"],
        res["lsa_svd"]["exhaustividad"],
        res["char_ngram"]["exhaustividad"],
        res["sin_conceptos"]["exhaustividad"],
        cv["lopo_conceptos_podados"]["exhaustividad"],
        cv["lopo_global"]["exhaustividad"],
        res["mejorado"]["exhaustividad"],
    ]

    x = np.arange(len(etiquetas))
    w = 0.26
    ax1.bar(x - w, p_vals, w, label="Precisión", color=TEAL, edgecolor=INK, lw=0.6)
    ax1.bar(x, r_vals, w, label="Exhaustividad (Recall)", color=BLUE, edgecolor=INK, lw=0.6)
    b_f1 = ax1.bar(x + w, f1_vals, w, label="F1-Score (con IC 95%)", color=BRAND, edgecolor=INK, lw=0.6)
    ax1.axhline(0.90, color=CRIMSON, linestyle="--", linewidth=1.1, label="Compuerta CI (F1 ≥ 0,90)")

    # Barras de error IC95% Bootstrap para las 5 variantes principales
    claves_ic = ["base", "lsa_svd", "char_ngram", "sin_conceptos", None, None, "mejorado"]
    for idx, k_ic in enumerate(claves_ic):
        if k_ic is not None:
            lo, hi = res[k_ic]["ic95"]["f1"]
            val = f1_vals[idx]
            ax1.errorbar(
                x[idx] + w,
                val,
                yerr=[[max(0.0, val - lo)], [max(0.0, hi - val)]],
                fmt="none",
                ecolor=CRIMSON,
                elinewidth=1.3,
                capsize=3,
            )

    for idx, (bar, v) in enumerate(zip(b_f1, f1_vals, strict=True)):
        k_ic = claves_ic[idx]
        top_y = max(v, res[k_ic]["ic95"]["f1"][1]) if k_ic is not None else v
        ax1.text(
            bar.get_x() + bar.get_width() / 2,
            min(top_y + 0.022, 1.07),
            f"{v:.3f}",
            ha="center",
            va="bottom",
            fontsize=7.3,
            fontweight="bold",
            color=INK,
        )

    ax1.set_xticks(x)
    ax1.set_xticklabels(etiquetas, fontsize=7.6, color=INK)
    ax1.set_ylim(0, 1.16)
    ax1.set_ylabel("Puntaje (0 – 1)", fontsize=9.0, color=INK)
    ax1.set_title(
        "A. Comparativa Semántica, Ablación y Validación Cruzada (n = 112)",
        fontsize=10.1,
        fontweight="bold",
        color=INK,
        pad=10,
    )
    ax1.grid(axis="y", linestyle="--", alpha=0.45)
    ax1.legend(loc="upper left", fontsize=7.6, frameon=True, facecolor=BG_PANEL)

    taus = [s["umbral_tau"] for s in sens]
    ax2.plot(taus, [s["f1"] for s in sens], marker="o", lw=2.2, color=BRAND, label="F1 Híbrido (con conceptos)")
    ax2.plot(taus, [s["precision"] for s in sens], marker="s", lw=1.6, color=TEAL, label="Precisión Híbrido")
    ax2.plot(taus, [s["exhaustividad"] for s in sens], marker="^", lw=1.6, color=BLUE, label="Exhaustividad Híbrido")
    ax2.plot(taus, [s["especificidad"] for s in sens], marker="d", lw=1.6, color=AMBER, label="Especificidad (TN rate)")
    ax2.plot(
        taus,
        [s["f1_sin_conceptos"] for s in sens],
        marker="x",
        lw=1.6,
        linestyle=":",
        color=SLATE,
        label="F1 Ablación (sin conceptos)",
    )
    ax2.axvline(0.45, color=CRIMSON, linestyle="--", lw=1.2, label="Umbral operativo τ = 0,45")

    ax2.set_xlim(0.23, 0.62)
    ax2.set_ylim(0.25, 1.05)
    ax2.set_xlabel("Umbral de decisión τ (score mínimo para convalidar)", fontsize=8.8, color=INK)
    ax2.set_ylabel("Puntaje (0,25 – 1,00)", fontsize=9.0, color=INK)
    ax2.set_title(
        "B. Sensibilidad al Umbral τ y Estabilidad del Punto Operativo",
        fontsize=10.1,
        fontweight="bold",
        color=INK,
        pad=10,
    )
    ax2.grid(True, linestyle="--", alpha=0.45)
    ax2.legend(loc="lower left", fontsize=7.6, frameon=True, facecolor=BG_PANEL)

    fig.suptitle(
        "Evaluación Estadística del Motor de Convalidación: Alternativas Semánticas, Ablación, LOPO CV y Sensibilidad",
        fontsize=11.3,
        fontweight="bold",
        color=INK,
        y=0.99,
    )
    plt.tight_layout()
    plt.savefig(salida, dpi=300, bbox_inches="tight")
    plt.close()


def _graficar_curricular_analytics(ca: dict, salida: Path) -> None:
    """Genera el gráfico de Curricular Analytics sobre las 10 mallas UNAB (2 paneles)."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.6, 5.2), dpi=300)

    mallas = sorted(ca["mallas"], key=lambda m: m["complejidad_total"])
    nombres = [
        m["nombre"]
        .replace("Ingeniería Civil ", "Ing. Civil ")
        .replace("Ingeniería en ", "Ing. ")
        .replace("Ingeniería ", "Ing. ")
        for m in mallas
    ]
    c_vals = [m["complejidad_total"] for m in mallas]
    colores = [CRIMSON if m["slug"] == "civil-informatica" else BLUE for m in mallas]

    y = np.arange(len(mallas))
    bars = ax1.barh(y, c_vals, color=colores, edgecolor=INK, linewidth=0.6, height=0.65)
    for bar, val in zip(bars, c_vals, strict=True):
        ax1.text(
            val + 14,
            bar.get_y() + bar.get_height() / 2,
            f"{val}",
            va="center",
            fontsize=8.3,
            fontweight="bold",
            color=INK,
        )

    ax1.set_yticks(y)
    ax1.set_yticklabels(nombres, fontsize=8.3, color=INK)
    ax1.set_xlim(0, max(c_vals) * 1.15)
    ax1.set_xlabel("Complejidad Estructural Total C(G) = Σ (b(v) + d(v))", fontsize=8.8, color=INK)
    ax1.set_title("A. Complejidad Estructural de 10 Mallas UNAB", fontsize=10.3, fontweight="bold", color=INK, pad=10)
    ax1.grid(axis="x", linestyle="--", alpha=0.45)

    abrev = {
        "TDFI102": "Intro. a la Programación",
        "PTEC101": "Algoritmos y Est. de Datos",
        "FMMP012": "Intro. a las Matemáticas",
        "FMMP112": "Cálculo Diferencial",
        "CINF101": "Análisis y Diseño de Alg.",
        "PTEC102": "Paradigmas de Programación",
        "FMMP212": "Cálculo Integral",
        "CINF103": "Fundamentos de IA",
    }
    top8 = ca["top_civil_informatica"][:8][::-1]
    labels_t = [f"{r['codigo']} (S{r['semestre']})\n{abrev.get(r['codigo'], r['nombre'][:26])}" for r in top8]
    b_vals = np.array([r["factor_bloqueo"] for r in top8])
    d_vals = np.array([r["factor_retraso"] for r in top8])
    y2 = np.arange(len(top8))

    ax2.barh(y2, b_vals, color=BRAND, edgecolor=INK, lw=0.6, height=0.62, label="Factor de Bloqueo b(v)")
    ax2.barh(y2, d_vals, left=b_vals, color=TEAL, edgecolor=INK, lw=0.6, height=0.62, label="Factor de Retraso d(v)")

    for i, (bv, dv) in enumerate(zip(b_vals, d_vals, strict=True)):
        ax2.text(bv + dv + 0.6, i, f"c={bv + dv}", va="center", fontsize=8.2, fontweight="bold", color=INK)

    ax2.set_yticks(y2)
    ax2.set_yticklabels(labels_t, fontsize=7.8, color=INK)
    ax2.set_xlim(0, max(b_vals + d_vals) + 6)
    ax2.set_xlabel("Contribución a Complejidad Curricular c(v)", fontsize=8.8, color=INK)
    ax2.set_title(
        "B. Top-8 Cuellos de Botella · Ing. Civil Informática", fontsize=10.3, fontweight="bold", color=INK, pad=10
    )
    ax2.grid(axis="x", linestyle="--", alpha=0.45)
    ax2.legend(loc="lower right", fontsize=8, frameon=True, facecolor=BG_PANEL)

    fig.suptitle(
        "Diagnóstico Curricular Analytics (DAG) en la Facultad de Ingeniería UNAB (0 Ciclos Detectados)",
        fontsize=11.6,
        fontweight="bold",
        color=INK,
        y=0.99,
    )
    plt.tight_layout()
    plt.savefig(salida, dpi=300, bbox_inches="tight")
    plt.close()


def _graficar_uctp(uctp: list[dict], salida: Path) -> None:
    """Genera el gráfico comparativo del benchmark UCTP (2 paneles)."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.2, 4.8), dpi=300)

    etiquetas = [
        "Pequeña\n(4 ramos\n256 comb.)",
        "Mediana\n(5 ramos\n7.040 comb.)",
        "Grande\n(6 ramos\n202.500 comb.)",
        "Auditada\n(5 ramos\n+ H2/H3)",
    ]
    x = np.arange(len(uctp))
    w = 0.26

    algs = [
        ("aleatorio", "Línea base aleatoria", SLATE),
        ("branch_and_bound", "Branch & Bound exacto", BRAND),
        ("recocido_simulado", "Recocido Simulado (SA)", TEAL),
    ]

    for idx, (clave, label, col) in enumerate(algs):
        vals = [inst["resultados"][clave]["penalizacion"] for inst in uctp]
        bars = ax1.bar(x + (idx - 1) * w, vals, w, label=label, color=col, edgecolor=INK, lw=0.6)
        for bar, v in zip(bars, vals, strict=True):
            ax1.text(
                bar.get_x() + bar.get_width() / 2,
                v + 1.2,
                f"{v:.0f}",
                ha="center",
                va="bottom",
                fontsize=7.8,
                fontweight="bold",
                color=INK,
            )

    ax1.set_xticks(x)
    ax1.set_xticklabels(etiquetas, fontsize=8.3, color=INK)
    ax1.set_ylabel("Penalización blanda f(x)  (menor es mejor)", fontsize=8.8, color=INK)
    ax1.set_ylim(0, 90)
    ax1.set_title("A. Función Objetivo Compuesta f(x)", fontsize=10.3, fontweight="bold", color=INK, pad=10)
    ax1.grid(axis="y", linestyle="--", alpha=0.45)
    ax1.legend(loc="upper right", fontsize=8, frameon=True, facecolor=BG_PANEL)

    for idx, (clave, label, col) in enumerate(algs):
        vals = [inst["resultados"][clave]["ventanas"] for inst in uctp]
        bars = ax2.bar(x + (idx - 1) * w, vals, w, label=label, color=col, edgecolor=INK, lw=0.6)
        for bar, v in zip(bars, vals, strict=True):
            ax2.text(
                bar.get_x() + bar.get_width() / 2,
                v + 0.35,
                f"{v}",
                ha="center",
                va="bottom",
                fontsize=8,
                fontweight="bold",
                color=INK,
            )

    ax2.set_xticks(x)
    ax2.set_xticklabels(etiquetas, fontsize=8.3, color=INK)
    ax2.set_ylabel("Ventanas horarias (módulos libres intermedios)", fontsize=8.8, color=INK)
    ax2.set_ylim(0, 19)
    ax2.set_title("B. Reducción de Ventanas Horarias (H1 = 0)", fontsize=10.3, fontweight="bold", color=INK, pad=10)
    ax2.grid(axis="y", linestyle="--", alpha=0.45)
    ax2.legend(loc="upper right", fontsize=8, frameon=True, facecolor=BG_PANEL)

    fig.suptitle(
        "Benchmark del Motor Combinatorio UCTP: Línea Base vs. Branch-and-Bound vs. Simulated Annealing",
        fontsize=11.5,
        fontweight="bold",
        color=INK,
        y=0.99,
    )
    plt.tight_layout()
    plt.savefig(salida, dpi=300, bbox_inches="tight")
    plt.close()


def _graficar_itc2019(itc: list[dict], salida: Path) -> None:
    """Genera el gráfico comparativo sobre los benchmarks estándar ITC-2019 (2 paneles)."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.2, 4.8), dpi=300)

    etiquetas = []
    for ds in itc:
        res_bb = ds["resultados"]["branch_and_bound"]
        etiqueta_corta = (
            ds["etiqueta"].replace("Masaryk Univ. · ", "Masaryk\n").replace("Yachay Tech · ", "Yachay Tech\n")
        )
        etiquetas.append(f"{etiqueta_corta}\n({res_bb['factibles']}/{res_bb['evaluados']} fact.)")

    x = np.arange(len(itc))
    w = 0.26
    algs = [
        ("aleatorio", "Línea base aleatoria", SLATE),
        ("branch_and_bound", "Branch & Bound exacto", BRAND),
        ("recocido_simulado", "Recocido Simulado (SA)", TEAL),
    ]

    max_f = max((ds["resultados"][clave]["f_promedio"] or 0.0) for ds in itc for clave, _, _ in algs)
    max_w = max((ds["resultados"][clave]["ventanas_promedio"] or 0.0) for ds in itc for clave, _, _ in algs)

    for idx, (clave, label, col) in enumerate(algs):
        vals = [ds["resultados"][clave]["f_promedio"] or 0.0 for ds in itc]
        bars = ax1.bar(x + (idx - 1) * w, vals, w, label=label, color=col, edgecolor=INK, lw=0.6)
        for bar, v in zip(bars, vals, strict=True):
            ax1.text(
                bar.get_x() + bar.get_width() / 2,
                v + max_f * 0.018,
                f"{v:.1f}",
                ha="center",
                va="bottom",
                fontsize=7.8,
                fontweight="bold",
                color=INK,
            )

    ax1.set_xticks(x)
    ax1.set_xticklabels(etiquetas, fontsize=8.3, color=INK)
    ax1.set_ylabel("Penalización blanda promedio f(x)  (menor es mejor)", fontsize=8.8, color=INK)
    ax1.set_ylim(0, max_f * 1.18)
    ax1.set_title("A. Función Objetivo Compuesta f(x) · ITC-2019", fontsize=10.3, fontweight="bold", color=INK, pad=10)
    ax1.grid(axis="y", linestyle="--", alpha=0.45)
    ax1.legend(loc="upper left", fontsize=8, frameon=True, facecolor=BG_PANEL)

    for idx, (clave, label, col) in enumerate(algs):
        vals = [ds["resultados"][clave]["ventanas_promedio"] or 0.0 for ds in itc]
        bars = ax2.bar(x + (idx - 1) * w, vals, w, label=label, color=col, edgecolor=INK, lw=0.6)
        for bar, v in zip(bars, vals, strict=True):
            ax2.text(
                bar.get_x() + bar.get_width() / 2,
                v + max_w * 0.018,
                f"{v:.2f}",
                ha="center",
                va="bottom",
                fontsize=7.8,
                fontweight="bold",
                color=INK,
            )

    ax2.set_xticks(x)
    ax2.set_xticklabels(etiquetas, fontsize=8.3, color=INK)
    ax2.set_ylabel("Ventanas horarias promedio (H1 = 0)", fontsize=8.8, color=INK)
    ax2.set_ylim(0, max_w * 1.18)
    ax2.set_title("B. Reducción de Ventanas Horarias · ITC-2019", fontsize=10.3, fontweight="bold", color=INK, pad=10)
    ax2.grid(axis="y", linestyle="--", alpha=0.45)
    ax2.legend(loc="upper left", fontsize=8, frameon=True, facecolor=BG_PANEL)

    fig.suptitle(
        "Evaluación Externa UCTP sobre Benchmarks Estándar ITC-2019 (Perfiles Estudiantiles Reales)",
        fontsize=11.4,
        fontweight="bold",
        color=INK,
        y=0.99,
    )
    plt.tight_layout()
    plt.savefig(salida, dpi=300, bbox_inches="tight")
    plt.close()


def main() -> None:
    """Ejecuta la evaluación vigente y renderiza las figuras E3 en ``docs/img/``."""
    out_dir = RAIZ / "docs" / "img"
    out_dir.mkdir(parents=True, exist_ok=True)

    datos = {
        "curricular_analytics": evaluar_suite.evaluar_curricular_analytics(),
        "convalidacion": evaluar_suite.evaluar_convalidacion(),
        "uctp": evaluar_suite.evaluar_uctp_completo(),
        "eficiencia_servicios": evaluar_suite.evaluar_eficiencia_servicios(),
    }

    _graficar_convalidacion(datos["convalidacion"], out_dir / "fig_eval_convalidacion.png")
    _graficar_curricular_analytics(datos["curricular_analytics"], out_dir / "fig_curricular_analytics.png")
    _graficar_uctp(datos["uctp"], out_dir / "fig_benchmark_uctp.png")

    itc_json = out_dir / "metricas_itc2019.json"
    if itc_json.exists():
        itc_datos = json.loads(itc_json.read_text(encoding="utf-8"))
        _graficar_itc2019(itc_datos, out_dir / "fig_benchmark_itc2019.png")

    (out_dir / "metricas_verificadas_e3.json").write_text(
        json.dumps(datos, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print("Gráficos E3 generados en docs/img/")


if __name__ == "__main__":
    main()
