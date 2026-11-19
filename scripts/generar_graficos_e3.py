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

NAVY = "#0F2043"
BLUE = "#1E40AF"
TEAL = "#0D9488"
AMBER = "#D97706"
CRIMSON = "#BE123C"
SLATE = "#64748B"
BG_PANEL = "#F8FAFC"

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "axes.edgecolor": "#CBD5E1",
        "axes.linewidth": 0.8,
        "axes.facecolor": "#FFFFFF",
        "figure.facecolor": "#FFFFFF",
    }
)


def _graficar_convalidacion(conv: dict, salida: Path) -> None:
    """Genera el gráfico comparativo del motor de convalidación IA (2 paneles)."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.2, 4.8), dpi=300)

    metricas = ["Precisión", "Exhaust.\n(Recall)", "F1-Score", "Especif.", "Top-3"]
    claves = ["precision", "exhaustividad", "f1", "especificidad", "acierto_top3"]
    vals_base = [conv["global"]["base"][k] for k in claves]
    vals_mej = [conv["global"]["mejorado"][k] for k in claves]

    x = np.arange(len(metricas))
    w = 0.36
    b1 = ax1.bar(x - w / 2, vals_base, w, label="Línea base (solo contenido)", color=SLATE, edgecolor=NAVY, lw=0.6)
    b2 = ax1.bar(x + w / 2, vals_mej, w, label="Motor híbrido mejorado", color=BLUE, edgecolor=NAVY, lw=0.6)
    ax1.axhline(0.90, color=CRIMSON, linestyle="--", linewidth=1.2, label="Umbral CI (F1 ≥ 0,90)")

    for bars in (b1, b2):
        for bar in bars:
            h = bar.get_height()
            ax1.text(
                bar.get_x() + bar.get_width() / 2,
                min(h + 0.025, 1.04),
                f"{h:.3f}",
                ha="center",
                va="bottom",
                fontsize=7.8,
                fontweight="bold",
                color=NAVY,
            )

    ax1.set_xticks(x)
    ax1.set_xticklabels(metricas, fontsize=8.8, color=NAVY)
    ax1.set_ylim(0, 1.18)
    ax1.set_ylabel("Puntaje (0 – 1)", fontsize=9.2, color=NAVY)
    ax1.set_title("A. Desempeño Global (n = 112 asignaturas)", fontsize=10.5, fontweight="bold", color=NAVY, pad=28)
    ax1.grid(axis="y", linestyle="--", alpha=0.45)
    ax1.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, 1.13),
        ncol=3,
        fontsize=7.6,
        frameon=True,
        facecolor=BG_PANEL,
    )

    pares = list(conv["por_par"].keys())
    etiquetas_par = [
        "USACH Inf\n→ UNAB Inf\n(n=38)",
        "UCHILE Comp\n→ UNAB Inf\n(n=32)",
        "USACH Ind\n→ UNAB Ind\n(n=42)",
    ]
    p_vals = [conv["por_par"][p]["mejorado"]["precision"] for p in pares]
    r_vals = [conv["por_par"][p]["mejorado"]["exhaustividad"] for p in pares]
    f1_vals = [conv["por_par"][p]["mejorado"]["f1"] for p in pares]

    x2 = np.arange(len(pares))
    w2 = 0.25
    g1 = ax2.bar(x2 - w2, p_vals, w2, label="Precisión", color=TEAL, edgecolor=NAVY, lw=0.6)
    g2 = ax2.bar(x2, r_vals, w2, label="Exhaustividad", color=BLUE, edgecolor=NAVY, lw=0.6)
    g3 = ax2.bar(x2 + w2, f1_vals, w2, label="F1-Score", color=NAVY, edgecolor=NAVY, lw=0.6)
    ax2.axhline(0.90, color=CRIMSON, linestyle="--", linewidth=1.2)

    for bars in (g1, g2, g3):
        for bar in bars:
            h = bar.get_height()
            ax2.text(
                bar.get_x() + bar.get_width() / 2,
                h + 0.015,
                f"{h:.2f}",
                ha="center",
                va="bottom",
                fontsize=7.5,
                fontweight="bold",
                color=NAVY,
            )

    ax2.set_xticks(x2)
    ax2.set_xticklabels(etiquetas_par, fontsize=8.5, color=NAVY)
    ax2.set_ylim(0.75, 1.08)
    ax2.set_ylabel("Puntaje (0,75 – 1,00)", fontsize=9.2, color=NAVY)
    ax2.set_title("B. Motor Mejorado por Par de Carreras", fontsize=10.5, fontweight="bold", color=NAVY, pad=28)
    ax2.grid(axis="y", linestyle="--", alpha=0.45)
    ax2.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, 1.13),
        ncol=3,
        fontsize=7.8,
        frameon=True,
        facecolor=BG_PANEL,
    )

    fig.suptitle(
        "Evaluación del Motor Híbrido de Convalidación sobre Gold Standard (112 Asignaturas)",
        fontsize=11.8,
        fontweight="bold",
        color=NAVY,
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
    bars = ax1.barh(y, c_vals, color=colores, edgecolor=NAVY, linewidth=0.6, height=0.65)
    for bar, val in zip(bars, c_vals, strict=True):
        ax1.text(
            val + 14,
            bar.get_y() + bar.get_height() / 2,
            f"{val}",
            va="center",
            fontsize=8.3,
            fontweight="bold",
            color=NAVY,
        )

    ax1.set_yticks(y)
    ax1.set_yticklabels(nombres, fontsize=8.3, color=NAVY)
    ax1.set_xlim(0, max(c_vals) * 1.15)
    ax1.set_xlabel("Complejidad Estructural Total C(G) = Σ (b(v) + d(v))", fontsize=8.8, color=NAVY)
    ax1.set_title("A. Complejidad Estructural de 10 Mallas UNAB", fontsize=10.3, fontweight="bold", color=NAVY, pad=10)
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

    ax2.barh(y2, b_vals, color=NAVY, edgecolor=NAVY, lw=0.6, height=0.62, label="Factor de Bloqueo b(v)")
    ax2.barh(y2, d_vals, left=b_vals, color=TEAL, edgecolor=NAVY, lw=0.6, height=0.62, label="Factor de Retraso d(v)")

    for i, (bv, dv) in enumerate(zip(b_vals, d_vals, strict=True)):
        ax2.text(bv + dv + 0.6, i, f"c={bv + dv}", va="center", fontsize=8.2, fontweight="bold", color=NAVY)

    ax2.set_yticks(y2)
    ax2.set_yticklabels(labels_t, fontsize=7.8, color=NAVY)
    ax2.set_xlim(0, max(b_vals + d_vals) + 6)
    ax2.set_xlabel("Contribución a Complejidad Curricular c(v)", fontsize=8.8, color=NAVY)
    ax2.set_title(
        "B. Top-8 Cuellos de Botella · Ing. Civil Informática", fontsize=10.3, fontweight="bold", color=NAVY, pad=10
    )
    ax2.grid(axis="x", linestyle="--", alpha=0.45)
    ax2.legend(loc="lower right", fontsize=8, frameon=True, facecolor=BG_PANEL)

    fig.suptitle(
        "Diagnóstico Curricular Analytics (DAG) en la Facultad de Ingeniería UNAB (0 Ciclos Detectados)",
        fontsize=11.6,
        fontweight="bold",
        color=NAVY,
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
        ("branch_and_bound", "Branch & Bound exacto", NAVY),
        ("recocido_simulado", "Recocido Simulado (SA)", TEAL),
    ]

    for idx, (clave, label, col) in enumerate(algs):
        vals = [inst["resultados"][clave]["penalizacion"] for inst in uctp]
        bars = ax1.bar(x + (idx - 1) * w, vals, w, label=label, color=col, edgecolor=NAVY, lw=0.6)
        for bar, v in zip(bars, vals, strict=True):
            ax1.text(
                bar.get_x() + bar.get_width() / 2,
                v + 1.2,
                f"{v:.0f}",
                ha="center",
                va="bottom",
                fontsize=7.8,
                fontweight="bold",
                color=NAVY,
            )

    ax1.set_xticks(x)
    ax1.set_xticklabels(etiquetas, fontsize=8.3, color=NAVY)
    ax1.set_ylabel("Penalización blanda f(x)  (menor es mejor)", fontsize=8.8, color=NAVY)
    ax1.set_ylim(0, 90)
    ax1.set_title("A. Función Objetivo Compuesta f(x)", fontsize=10.3, fontweight="bold", color=NAVY, pad=10)
    ax1.grid(axis="y", linestyle="--", alpha=0.45)
    ax1.legend(loc="upper right", fontsize=8, frameon=True, facecolor=BG_PANEL)

    for idx, (clave, label, col) in enumerate(algs):
        vals = [inst["resultados"][clave]["ventanas"] for inst in uctp]
        bars = ax2.bar(x + (idx - 1) * w, vals, w, label=label, color=col, edgecolor=NAVY, lw=0.6)
        for bar, v in zip(bars, vals, strict=True):
            ax2.text(
                bar.get_x() + bar.get_width() / 2,
                v + 0.35,
                f"{v}",
                ha="center",
                va="bottom",
                fontsize=8,
                fontweight="bold",
                color=NAVY,
            )

    ax2.set_xticks(x)
    ax2.set_xticklabels(etiquetas, fontsize=8.3, color=NAVY)
    ax2.set_ylabel("Ventanas horarias (módulos libres intermedios)", fontsize=8.8, color=NAVY)
    ax2.set_ylim(0, 19)
    ax2.set_title("B. Reducción de Ventanas Horarias (H1 = 0)", fontsize=10.3, fontweight="bold", color=NAVY, pad=10)
    ax2.grid(axis="y", linestyle="--", alpha=0.45)
    ax2.legend(loc="upper right", fontsize=8, frameon=True, facecolor=BG_PANEL)

    fig.suptitle(
        "Benchmark del Motor Combinatorio UCTP: Línea Base vs. Branch-and-Bound vs. Simulated Annealing",
        fontsize=11.5,
        fontweight="bold",
        color=NAVY,
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
        ("branch_and_bound", "Branch & Bound exacto", NAVY),
        ("recocido_simulado", "Recocido Simulado (SA)", TEAL),
    ]

    max_f = max((ds["resultados"][clave]["f_promedio"] or 0.0) for ds in itc for clave, _, _ in algs)
    max_w = max((ds["resultados"][clave]["ventanas_promedio"] or 0.0) for ds in itc for clave, _, _ in algs)

    for idx, (clave, label, col) in enumerate(algs):
        vals = [ds["resultados"][clave]["f_promedio"] or 0.0 for ds in itc]
        bars = ax1.bar(x + (idx - 1) * w, vals, w, label=label, color=col, edgecolor=NAVY, lw=0.6)
        for bar, v in zip(bars, vals, strict=True):
            ax1.text(
                bar.get_x() + bar.get_width() / 2,
                v + max_f * 0.018,
                f"{v:.1f}",
                ha="center",
                va="bottom",
                fontsize=7.8,
                fontweight="bold",
                color=NAVY,
            )

    ax1.set_xticks(x)
    ax1.set_xticklabels(etiquetas, fontsize=8.3, color=NAVY)
    ax1.set_ylabel("Penalización blanda promedio f(x)  (menor es mejor)", fontsize=8.8, color=NAVY)
    ax1.set_ylim(0, max_f * 1.18)
    ax1.set_title("A. Función Objetivo Compuesta f(x) · ITC-2019", fontsize=10.3, fontweight="bold", color=NAVY, pad=10)
    ax1.grid(axis="y", linestyle="--", alpha=0.45)
    ax1.legend(loc="upper left", fontsize=8, frameon=True, facecolor=BG_PANEL)

    for idx, (clave, label, col) in enumerate(algs):
        vals = [ds["resultados"][clave]["ventanas_promedio"] or 0.0 for ds in itc]
        bars = ax2.bar(x + (idx - 1) * w, vals, w, label=label, color=col, edgecolor=NAVY, lw=0.6)
        for bar, v in zip(bars, vals, strict=True):
            ax2.text(
                bar.get_x() + bar.get_width() / 2,
                v + max_w * 0.018,
                f"{v:.2f}",
                ha="center",
                va="bottom",
                fontsize=7.8,
                fontweight="bold",
                color=NAVY,
            )

    ax2.set_xticks(x)
    ax2.set_xticklabels(etiquetas, fontsize=8.3, color=NAVY)
    ax2.set_ylabel("Ventanas horarias promedio (H1 = 0)", fontsize=8.8, color=NAVY)
    ax2.set_ylim(0, max_w * 1.18)
    ax2.set_title("B. Reducción de Ventanas Horarias · ITC-2019", fontsize=10.3, fontweight="bold", color=NAVY, pad=10)
    ax2.grid(axis="y", linestyle="--", alpha=0.45)
    ax2.legend(loc="upper left", fontsize=8, frameon=True, facecolor=BG_PANEL)

    fig.suptitle(
        "Evaluación Externa UCTP sobre Benchmarks Estándar ITC-2019 (Perfiles Estudiantiles Reales)",
        fontsize=11.4,
        fontweight="bold",
        color=NAVY,
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
