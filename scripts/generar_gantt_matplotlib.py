"""Genera el cronograma de hitos y entregables SIGA-DSS (Agosto - Noviembre 2026)."""

from __future__ import annotations

import datetime

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.patches import Patch


def generate_gantt_chart(output_path: str = "docs/img/gantt_cronograma.png") -> None:
    """Renderiza el diagrama de Gantt actualizado al cierre de la Evaluación E3."""
    tasks = [
        ("Levantamiento de problemas y SIES", "2026-08-01", "2026-08-20", "#8E9189"),
        ("Formulación hipótesis y marco teórico", "2026-08-21", "2026-09-10", "#8E9189"),
        ("Aprobación y Defensa E1", "2026-09-11", "2026-09-25", "#191B16"),
        ("Unificación arquitectura microservicios", "2026-09-26", "2026-10-05", "#0C8599"),
        ("Modelado DAG y Curricular Analytics", "2026-10-06", "2026-10-15", "#0C8599"),
        ("Calibración Motor IA (F1 >= 0,90)", "2026-10-16", "2026-10-21", "#0C8599"),
        ("Docker Compose, Gateway, SSO y Terraform IaC", "2026-10-22", "2026-10-23", "#0C8599"),
        ("CI/CD Automatizado y Entrega E2", "2026-10-23", "2026-11-07", "#191B16"),
        ("Motor UCTP (B&B + SA) y Curricular Analytics", "2026-11-08", "2026-11-18", "#1D6B55"),
        ("Evaluación técnica integral y Paper Final E3", "2026-11-15", "2026-11-19", "#1D6B55"),
        ("Despliegue AWS Staging (trabajo futuro / cierre)", "2026-11-19", "2026-11-23", "#D89B1E"),
        ("Aplicación en campo SUS (trabajo futuro)", "2026-11-20", "2026-11-25", "#D89B1E"),
    ]

    fig, ax = plt.subplots(figsize=(11.2, 6.0), dpi=300)

    y_labels = [t[0] for t in tasks]
    y_pos = range(len(tasks))

    for idx, (_name, start_s, end_s, color) in enumerate(tasks):
        start = datetime.datetime.strptime(start_s, "%Y-%m-%d")
        end = datetime.datetime.strptime(end_s, "%Y-%m-%d")
        duration = max((end - start).days, 1)
        ax.barh(
            idx,
            duration,
            left=start,
            height=0.55,
            align="center",
            color=color,
            edgecolor="#191B16",
            linewidth=0.8,
            alpha=0.92,
        )

    ax.set_yticks(list(y_pos))
    ax.set_yticklabels(y_labels, fontsize=9.2, fontweight="500", color="#191B16")
    ax.invert_yaxis()

    ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d-%b"))

    plt.xticks(fontsize=9, color="#5B5E56")
    ax.grid(axis="x", linestyle="--", alpha=0.6, color="#DEDED7")

    cierre_e3 = datetime.datetime(2026, 11, 18)
    ax.axvline(cierre_e3, color="#C73C2E", linestyle="--", linewidth=1.5)

    legend_elements = [
        Patch(facecolor="#8E9189", edgecolor="#191B16", label="Hito 1: Fundamentación (E1 · Completado)"),
        Patch(facecolor="#0C8599", edgecolor="#191B16", label="Hito 2: Avance Tecnológico (E2 · Completado)"),
        Patch(facecolor="#1D6B55", edgecolor="#191B16", label="Hito 3: UCTP, Validación y Paper E3 (Completado)"),
        Patch(facecolor="#D89B1E", edgecolor="#191B16", label="Continuidad: AWS en vivo y SUS de campo"),
    ]
    ax.legend(
        handles=legend_elements,
        loc="lower left",
        frameon=True,
        facecolor="#F6F6F2",
        edgecolor="#DEDED7",
        fontsize=8.2,
    )

    ax.set_title(
        "Cronograma de Hitos y Trazabilidad SIGA-DSS (Agosto – Noviembre 2026)",
        fontsize=11.5,
        fontweight="bold",
        color="#191B16",
        pad=14,
    )
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"Gantt guardado exitosamente en: {output_path}")


if __name__ == "__main__":
    generate_gantt_chart()
