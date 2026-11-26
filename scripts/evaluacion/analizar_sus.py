"""Análisis reproducible de la evaluación de usabilidad SUS de SIGA-DSS (Anexo A del informe).

Lee las respuestas reales recolectadas en terreno (una fila por participante) y calcula:
  - puntaje SUS individual (Brooke, 1996) y estadística descriptiva del grupo
  - intervalo de confianza al 95% por bootstrap percentil (B=2.000, semilla fija)
  - proporción de participantes con SUS >= 70 y rango de aceptabilidad (Bangor et al., 2008)
  - promedio por ítem y desagregación por perfil (estudiante / staff)
  - tasa de éxito y tiempo mediano de las tareas guiadas T1..T4

El script NO genera datos: si el archivo no tiene participantes válidos, termina con error.

Uso:
  python scripts/evaluacion/analizar_sus.py data/evaluacion_sus/respuestas.csv
  python scripts/evaluacion/analizar_sus.py respuestas.csv --json docs/img/metricas_sus.json \\
      --markdown --figura docs/img/fig_sus.png
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import statistics
import sys
from dataclasses import dataclass, field
from pathlib import Path

ITEMS = [f"sus_{i}" for i in range(1, 11)]
TAREAS = ["t1", "t2", "t3", "t4"]
PERFILES = {"estudiante", "staff"}
UMBRAL_OBJETIVO = 70.0
BOOTSTRAP_B = 2000
BOOTSTRAP_SEMILLA = 2026

# Columnas mínimas del CSV (ver data/evaluacion_sus/plantilla_respuestas.csv)
COLUMNAS = (
    ["participante_id", "perfil", "consentimiento"]
    + ITEMS
    + [f"{t}_{c}" for t in TAREAS for c in ("exito", "segundos")]
)


class ErrorDatos(ValueError):
    """Fila o archivo con datos inválidos."""


@dataclass
class Participante:
    id: str
    perfil: str
    respuestas: list[int]
    tareas: dict[str, tuple[float | None, float | None]] = field(default_factory=dict)

    @property
    def sus(self) -> float:
        return puntaje_sus(self.respuestas)


def puntaje_sus(respuestas: list[int]) -> float:
    """Puntaje SUS estándar en [0, 100].

    Ítems impares (positivos) aportan x-1; ítems pares (negativos) aportan 5-x; la suma se multiplica por 2,5.
    """
    if len(respuestas) != 10:
        raise ErrorDatos(f"Se esperaban 10 respuestas SUS y llegaron {len(respuestas)}")
    total = 0
    for i, x in enumerate(respuestas, start=1):
        if x not in (1, 2, 3, 4, 5):
            raise ErrorDatos(f"Respuesta fuera de escala Likert 1-5 en ítem {i}: {x!r}")
        total += (x - 1) if i % 2 == 1 else (5 - x)
    return total * 2.5


def rango_aceptabilidad(sus: float) -> str:
    """Rangos de aceptabilidad de Bangor, Kortum y Miller (2008)."""
    if sus >= 70:
        return "aceptable"
    if sus >= 50:
        return "marginal"
    return "no aceptable"


def _exito(valor: str, fila: str, tarea: str) -> float | None:
    v = valor.strip().lower()
    if v == "":
        return None  # tarea no aplicada a este perfil (p. ej., T4 solo para staff)
    mapa = {"1": 1.0, "si": 1.0, "sí": 1.0, "0": 0.0, "no": 0.0, "0.5": 0.5, "0,5": 0.5, "parcial": 0.5}
    if v not in mapa:
        raise ErrorDatos(f"{fila}: valor de éxito inválido en {tarea} ({valor!r}); use 1, 0 o parcial")
    return mapa[v]


def _segundos(valor: str, fila: str, tarea: str) -> float | None:
    v = valor.strip().replace(",", ".")
    if v == "":
        return None
    try:
        s = float(v)
    except ValueError as exc:
        raise ErrorDatos(f"{fila}: tiempo inválido en {tarea} ({valor!r})") from exc
    if s < 0:
        raise ErrorDatos(f"{fila}: tiempo negativo en {tarea}")
    return s


def leer_respuestas(ruta: Path) -> tuple[list[Participante], list[str]]:
    """Lee el CSV y devuelve (participantes válidos, avisos de filas excluidas)."""
    with ruta.open(encoding="utf-8-sig", newline="") as fh:
        muestra = fh.read(4096)
        fh.seek(0)
        dialecto = csv.Sniffer().sniff(muestra, delimiters=",;") if muestra else csv.excel
        lector = csv.DictReader(fh, dialect=dialecto)
        faltantes = [c for c in COLUMNAS if c not in (lector.fieldnames or [])]
        if faltantes:
            raise ErrorDatos(f"Faltan columnas en {ruta.name}: {', '.join(faltantes)}")

        participantes: list[Participante] = []
        avisos: list[str] = []
        vistos: set[str] = set()
        for n, fila in enumerate(lector, start=2):
            pid = (fila["participante_id"] or "").strip()
            etiqueta = f"fila {n} ({pid or 'sin id'})"
            if not pid:
                avisos.append(f"{etiqueta}: excluida por no tener participante_id")
                continue
            if pid in vistos:
                raise ErrorDatos(f"{etiqueta}: participante_id duplicado")
            if (fila["consentimiento"] or "").strip().lower() not in ("si", "sí", "1"):
                avisos.append(f"{etiqueta}: excluida por no registrar consentimiento informado")
                continue
            perfil = (fila["perfil"] or "").strip().lower()
            if perfil not in PERFILES:
                raise ErrorDatos(f"{etiqueta}: perfil inválido {perfil!r}; use estudiante o staff")
            try:
                respuestas = [int((fila[c] or "").strip()) for c in ITEMS]
            except ValueError:
                avisos.append(f"{etiqueta}: excluida por cuestionario SUS incompleto")
                continue
            p = Participante(id=pid, perfil=perfil, respuestas=respuestas)
            p.sus  # valida la escala  # noqa: B018
            for t in TAREAS:
                p.tareas[t] = (
                    _exito(fila[f"{t}_exito"] or "", etiqueta, t),
                    _segundos(fila[f"{t}_segundos"] or "", etiqueta, t),
                )
            vistos.add(pid)
            participantes.append(p)
    return participantes, avisos


def ic_bootstrap(valores: list[float], b: int = BOOTSTRAP_B, semilla: int = BOOTSTRAP_SEMILLA) -> tuple[float, float]:
    """IC 95% bootstrap percentil de la media."""
    if len(valores) < 2:
        return (valores[0], valores[0]) if valores else (float("nan"), float("nan"))
    rng = random.Random(semilla)
    n = len(valores)
    medias = sorted(statistics.fmean(rng.choices(valores, k=n)) for _ in range(b))
    return medias[int(0.025 * b)], medias[int(0.975 * b) - 1]


def _resumen_grupo(participantes: list[Participante]) -> dict:
    puntajes = [p.sus for p in participantes]
    lo, hi = ic_bootstrap(puntajes)
    media = statistics.fmean(puntajes)
    return {
        "n": len(puntajes),
        "media": round(media, 2),
        "desviacion_estandar": round(statistics.stdev(puntajes), 2) if len(puntajes) > 1 else 0.0,
        "mediana": round(statistics.median(puntajes), 2),
        "minimo": min(puntajes),
        "maximo": max(puntajes),
        "ic95_bootstrap": [round(lo, 2), round(hi, 2)],
        "proporcion_sobre_umbral": round(sum(s >= UMBRAL_OBJETIVO for s in puntajes) / len(puntajes), 3),
        "rango_aceptabilidad_media": rango_aceptabilidad(media),
    }


def analizar(participantes: list[Participante]) -> dict:
    if not participantes:
        raise ErrorDatos("No hay participantes válidos: no se puede calcular el SUS")

    por_perfil = {
        perfil: _resumen_grupo(grupo)
        for perfil in sorted(PERFILES)
        if (grupo := [p for p in participantes if p.perfil == perfil])
    }
    items = {c: round(statistics.fmean(p.respuestas[i] for p in participantes), 2) for i, c in enumerate(ITEMS)}

    tareas = {}
    for t in TAREAS:
        aplicadas = [p.tareas[t] for p in participantes if p.tareas[t][0] is not None]
        if not aplicadas:
            continue
        tiempos_exito = [seg for ex, seg in aplicadas if ex == 1.0 and seg is not None]
        tareas[t] = {
            "n": len(aplicadas),
            "tasa_exito": round(statistics.fmean(ex for ex, _ in aplicadas), 3),
            "tiempo_mediano_exito_s": round(statistics.median(tiempos_exito), 1) if tiempos_exito else None,
        }

    global_ = _resumen_grupo(participantes)
    return {
        "instrumento": "System Usability Scale (Brooke, 1996), 10 ítems Likert 1-5",
        "umbral_objetivo": UMBRAL_OBJETIVO,
        "cumple_objetivo": global_["media"] >= UMBRAL_OBJETIVO,
        "bootstrap": {"B": BOOTSTRAP_B, "semilla": BOOTSTRAP_SEMILLA},
        "global": global_,
        "por_perfil": por_perfil,
        "promedio_por_item": items,
        "tareas": tareas,
        "puntajes_individuales": {p.id: p.sus for p in participantes},
    }


def _fmt(x: float, dec: int = 1) -> str:
    return f"{x:.{dec}f}".replace(".", ",")


def tabla_markdown(r: dict) -> str:
    """Tabla lista para pegar en el informe (formato numérico chileno)."""
    filas = [
        "| Grupo | $n$ | SUS medio | DE | Mediana | $\\text{IC}_{95\\%}$ | % SUS $\\ge 70$ | Rango |",
        "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
    ]
    grupos = [("**Global**", r["global"])] + [(p.capitalize(), g) for p, g in r["por_perfil"].items()]
    for nombre, g in grupos:
        lo, hi = g["ic95_bootstrap"]
        filas.append(
            f"| {nombre} | {g['n']} | {_fmt(g['media'])} | {_fmt(g['desviacion_estandar'])} | {_fmt(g['mediana'])} "
            f"| $[{_fmt(lo)}; {_fmt(hi)}]$ | {_fmt(100 * g['proporcion_sobre_umbral'])}% "
            f"| {g['rango_aceptabilidad_media']} |"
        )
    if r["tareas"]:
        filas += ["", "| Tarea | $n$ | Tasa de éxito | Tiempo mediano (éxito) |", "| :--- | :---: | :---: | :---: |"]
        for t, d in r["tareas"].items():
            tiempo = f"{_fmt(d['tiempo_mediano_exito_s'])} s" if d["tiempo_mediano_exito_s"] is not None else "—"
            filas.append(f"| {t.upper()} | {d['n']} | {_fmt(100 * d['tasa_exito'])}% | {tiempo} |")
    return "\n".join(filas)


def generar_figura(r: dict, salida: Path) -> None:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as exc:  # matplotlib es opcional: solo se usa para la figura del informe
        raise SystemExit("Para --figura instale matplotlib: pip install matplotlib") from exc

    puntajes = sorted(r["puntajes_individuales"].values())
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4))
    ax1.axvspan(0, 50, color="#f4c7c3", alpha=0.6, label="No aceptable (<50)")
    ax1.axvspan(50, 70, color="#fce8b2", alpha=0.6, label="Marginal (50–70)")
    ax1.axvspan(70, 100, color="#b7e1cd", alpha=0.6, label="Aceptable (≥70)")
    ax1.scatter(puntajes, [1] * len(puntajes), color="#1a3c6e", zorder=3, alpha=0.7)
    g = r["global"]
    ax1.errorbar(
        g["media"],
        1.25,
        xerr=[[g["media"] - g["ic95_bootstrap"][0]], [g["ic95_bootstrap"][1] - g["media"]]],
        fmt="D",
        color="#c0392b",
        capsize=5,
        label=f"Media {g['media']:.1f} (IC 95%)",
    )
    ax1.set_xlim(0, 100)
    ax1.set_yticks([])
    ax1.set_xlabel("Puntaje SUS")
    ax1.set_title(f"A. Puntajes SUS individuales (n={g['n']})")
    ax1.legend(loc="lower left", fontsize=7)

    items = list(r["promedio_por_item"].values())
    colores = ["#1a3c6e" if i % 2 == 0 else "#8e9aaf" for i in range(10)]
    ax2.bar([str(i) for i in range(1, 11)], items, color=colores)
    ax2.set_ylim(1, 5)
    ax2.set_xlabel("Ítem SUS (impares positivos · pares negativos)")
    ax2.set_ylabel("Promedio Likert")
    ax2.set_title("B. Promedio por ítem")
    fig.tight_layout()
    salida.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(salida, dpi=200)
    plt.close(fig)


def main(argv: list[str] | None = None) -> int:
    for flujo in (sys.stdout, sys.stderr):  # tildes legibles en la consola de Windows
        if hasattr(flujo, "reconfigure"):
            flujo.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("respuestas", type=Path, help="CSV con una fila por participante")
    ap.add_argument("--json", type=Path, help="guardar métricas en JSON")
    ap.add_argument("--markdown", action="store_true", help="imprimir tabla Markdown para el informe")
    ap.add_argument("--figura", type=Path, help="guardar figura PNG (requiere matplotlib)")
    args = ap.parse_args(argv)

    try:
        participantes, avisos = leer_respuestas(args.respuestas)
        r = analizar(participantes)
    except (ErrorDatos, FileNotFoundError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    for aviso in avisos:
        print(f"AVISO: {aviso}", file=sys.stderr)
    g = r["global"]
    print(f"Participantes válidos: {g['n']}  (excluidos: {len(avisos)})")
    print(
        f"SUS medio: {g['media']:.2f}  DE={g['desviacion_estandar']:.2f}  IC95%=[{g['ic95_bootstrap'][0]:.2f}; "
        f"{g['ic95_bootstrap'][1]:.2f}]  mediana={g['mediana']:.2f}"
    )
    print(
        f"Sobre umbral {UMBRAL_OBJETIVO:.0f}: {100 * g['proporcion_sobre_umbral']:.1f}%  ->  "
        f"{'CUMPLE' if r['cumple_objetivo'] else 'NO CUMPLE'} objetivo (rango: {g['rango_aceptabilidad_media']})"
    )
    if g["n"] < 30:
        print(f"Nota: n={g['n']} es menor que la muestra objetivo del protocolo (n=30).")

    if args.markdown:
        print()
        print(tabla_markdown(r))
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(r, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"JSON: {args.json}")
    if args.figura:
        generar_figura(r, args.figura)
        print(f"Figura: {args.figura}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
