"""Acuerdo entre anotadores del Gold Standard de convalidación (kappa de Cohen).

Responde a la observación de la evaluación E3: el Gold Standard fue etiquetado por un único anotador del
equipo. Este script permite que un segundo anotador independiente etiquete a ciegas las mismas 112
asignaturas y mide el acuerdo con las etiquetas originales.

Dos pasos:

  1) planilla  genera un Excel CIEGO (sin las etiquetas originales, en orden aleatorio) con una hoja por
               par universitario y una lista desplegable con las asignaturas UNAB de destino.
  2) kappa     lee el Excel completado, calcula el acuerdo y lista los desacuerdos para adjudicar.

Métricas:
  - acuerdo observado (exact match del código UNAB o de "sin equivalente")
  - kappa de Cohen multiclase (código UNAB / sin equivalente) e IC 95% bootstrap
  - kappa binario (¿tiene equivalente? sí/no), que aísla el acuerdo sobre la existencia de equivalencia
  - interpretación según Landis y Koch (1977)

Uso:
  python scripts/evaluacion/acuerdo_gold.py planilla --salida anotacion_ciega.xlsx
  python scripts/evaluacion/acuerdo_gold.py kappa anotacion_ciega_completada.xlsx \\
      --json docs/img/metricas_acuerdo_gold.json --desacuerdos desacuerdos.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
GOLD = RAIZ / "data" / "convalidacion" / "evaluacion" / "gold.json"
BASE_UNAB = RAIZ / "data" / "unab" / "base-convalidacion.json"
CATALOGO = RAIZ / "data" / "universidades" / "catalogo"

SIN_EQUIVALENTE = "SIN EQUIVALENTE"
SEMILLA = 2026
BOOTSTRAP_B = 2000
HOJA_CATALOGO = "Catalogo_UNAB"


class ErrorAnotacion(ValueError):
    """Planilla completada con datos faltantes o inválidos."""


# ---------------------------------------------------------------------------
# Datos
# ---------------------------------------------------------------------------


def slug_unab(nombre: str) -> str:
    t = unicodedata.normalize("NFKD", nombre).encode("ascii", "ignore").decode()
    return "unab-" + re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")


def cargar_gold() -> list[dict]:
    return json.loads(GOLD.read_text(encoding="utf-8"))["casos"]


def cargar_destinos() -> dict[str, list[tuple[str, str]]]:
    """slug destino -> [(código, nombre)] sin duplicados, ordenado por código."""
    crudo = json.loads(BASE_UNAB.read_text(encoding="utf-8"))
    destinos = {}
    for carrera, asignaturas in crudo.items():
        vistos = {}
        for a in asignaturas:
            vistos.setdefault(a["codigo"].strip().upper(), a["nombre"].strip())
        destinos[slug_unab(carrera)] = sorted(vistos.items())
    return destinos


def nombre_origen(slug: str) -> str:
    ruta = CATALOGO / f"{slug}.json"
    if ruta.exists():
        d = json.loads(ruta.read_text(encoding="utf-8"))
        return f"{d['sigla']} · {d['carrera']}"
    return slug


def nombre_hoja(i: int, caso: dict) -> str:
    return f"Par{i}_{caso['origen']}"[:31]


def normalizar_etiqueta(valor) -> str | None:
    """Código UNAB en mayúsculas, o None si no hay equivalente."""
    if valor is None:
        return None
    v = str(valor).strip().upper()
    if v in ("", "NONE", "NULL"):
        return None
    if v in (SIN_EQUIVALENTE, "SIN EQUIVALENCIA", "NO", "-"):
        return SIN_EQUIVALENTE
    return v.split()[0]  # admite "FMMP112 · Cálculo Diferencial" desde la lista desplegable


# ---------------------------------------------------------------------------
# Paso 1: planilla ciega
# ---------------------------------------------------------------------------


def generar_planilla(salida: Path, semilla: int = SEMILLA) -> int:
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.worksheet.datavalidation import DataValidation

    casos = cargar_gold()
    destinos = cargar_destinos()
    rng = random.Random(semilla)
    wb = Workbook()

    ins = wb.active
    ins.title = "Instrucciones"
    lineas = [
        "Anotación ciega del Gold Standard de convalidación — SIGA-DSS",
        "",
        "Para cada asignatura de origen, indique la asignatura de la malla UNAB que una Dirección de Carrera",
        "aceptaría como equivalente, considerando SOLO el nombre (como en el modo catálogo del sistema).",
        "",
        "• Elija el código en la lista desplegable de la columna C.",
        f"• Si no existe equivalente en la malla UNAB, elija «{SIN_EQUIVALENTE}».",
        "• Si duda, elija la opción más probable y explique en Comentario (columna D).",
        "• No consulte las etiquetas originales ni al otro anotador: el acuerdo debe ser independiente.",
        "• Complete TODAS las filas de todas las hojas Par1, Par2 y Par3.",
        "",
        f"La hoja {HOJA_CATALOGO} lista las asignaturas UNAB de cada carrera de destino (solo referencia).",
        "",
        "Anotador (iniciales o rol, sin RUT):",
        "Fecha:",
    ]
    for i, linea in enumerate(lineas, start=1):
        ins.cell(row=i, column=1, value=linea)
    ins["A1"].font = Font(bold=True, size=14)
    ins.column_dimensions["A"].width = 110

    cat = wb.create_sheet(HOJA_CATALOGO)
    columna_por_destino: dict[str, tuple[str, int]] = {}
    for j, (slug, asignaturas) in enumerate(sorted((d, destinos[d]) for d in {c["destino"] for c in casos}), start=1):
        letra = cat.cell(row=1, column=j).column_letter
        cat.cell(row=1, column=j, value=slug).font = Font(bold=True)
        opciones = [SIN_EQUIVALENTE] + [f"{cod} · {nom}" for cod, nom in asignaturas]
        for k, op in enumerate(opciones, start=2):
            cat.cell(row=k, column=j, value=op)
        cat.column_dimensions[letra].width = 60
        columna_por_destino[slug] = (letra, len(opciones) + 1)

    encabezado = ["N", "Asignatura de origen", "Equivalente UNAB (lista)", "Comentario"]
    relleno = PatternFill("solid", fgColor="1A3C6E")
    total = 0
    for i, caso in enumerate(casos, start=1):
        hoja = wb.create_sheet(nombre_hoja(i, caso))
        hoja.append([f"Origen: {nombre_origen(caso['origen'])}  →  Destino: {caso['destino']}"])
        hoja["A1"].font = Font(bold=True)
        hoja.append(encabezado)
        for c in hoja[2]:
            c.font = Font(bold=True, color="FFFFFF")
            c.fill = relleno
        asignaturas = list(caso["etiquetas"])
        rng.shuffle(asignaturas)
        for n, asig in enumerate(asignaturas, start=1):
            hoja.append([n, asig, None, None])
        letra, fin = columna_por_destino[caso["destino"]]
        dv = DataValidation(type="list", formula1=f"={HOJA_CATALOGO}!${letra}$2:${letra}${fin}", allow_blank=True)
        hoja.add_data_validation(dv)
        dv.add(f"C3:C{len(asignaturas) + 2}")
        for col, ancho in zip("ABCD", (5, 50, 55, 45), strict=True):
            hoja.column_dimensions[col].width = ancho
        for fila in hoja.iter_rows(min_row=3):
            fila[1].alignment = Alignment(wrap_text=True)
        total += len(asignaturas)

    salida.parent.mkdir(parents=True, exist_ok=True)
    wb.save(salida)
    return total


# ---------------------------------------------------------------------------
# Paso 2: kappa
# ---------------------------------------------------------------------------


def leer_anotaciones(ruta: Path) -> dict[tuple[str, str], str]:
    """(origen, asignatura) -> etiqueta normalizada del segundo anotador."""
    from openpyxl import load_workbook

    wb = load_workbook(ruta, read_only=True, data_only=True)
    casos = cargar_gold()
    anot: dict[tuple[str, str], str] = {}
    faltantes: list[str] = []
    for i, caso in enumerate(casos, start=1):
        hoja_nombre = nombre_hoja(i, caso)
        if hoja_nombre not in wb.sheetnames:
            raise ErrorAnotacion(f"Falta la hoja {hoja_nombre}")
        for fila in wb[hoja_nombre].iter_rows(min_row=3, values_only=True):
            if not fila or fila[1] is None:
                continue
            asig = str(fila[1]).strip()
            if asig not in caso["etiquetas"]:
                raise ErrorAnotacion(f"{hoja_nombre}: asignatura desconocida {asig!r}")
            etiqueta = normalizar_etiqueta(fila[2] if len(fila) > 2 else None)
            if etiqueta is None:
                faltantes.append(f"{hoja_nombre}: {asig}")
                continue
            anot[(caso["origen"], asig)] = etiqueta
    if faltantes:
        muestra = "; ".join(faltantes[:5])
        raise ErrorAnotacion(f"{len(faltantes)} filas sin completar (p. ej. {muestra})")
    return anot


def pares_etiquetas(anot: dict[tuple[str, str], str]) -> list[dict]:
    """Une gold y segundo anotador. Si el gold admite varios códigos, coincidir con cualquiera cuenta como acuerdo."""
    filas = []
    for caso in cargar_gold():
        for asig, gold in caso["etiquetas"].items():
            clave = (caso["origen"], asig)
            if clave not in anot:
                raise ErrorAnotacion(f"No se anotó {asig!r} ({caso['origen']})")
            segundo = anot[clave]
            admitidos = [SIN_EQUIVALENTE] if gold is None else ([gold] if isinstance(gold, str) else list(gold))
            admitidos = [a.upper() for a in admitidos]
            primero = segundo if segundo in admitidos else admitidos[0]
            filas.append({"origen": caso["origen"], "asignatura": asig, "gold": primero, "segundo": segundo})
    return filas


def kappa_cohen(a: list[str], b: list[str]) -> float:
    n = len(a)
    if n == 0:
        return float("nan")
    po = sum(x == y for x, y in zip(a, b, strict=True)) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / (n * n)
    return 1.0 if pe == 1 else (po - pe) / (1 - pe)


def ic_bootstrap_kappa(a: list[str], b: list[str], binario: bool = False) -> tuple[float, float]:
    rng = random.Random(SEMILLA)
    n = len(a)
    valores = []
    for _ in range(BOOTSTRAP_B):
        idx = [rng.randrange(n) for _ in range(n)]
        xa, xb = [a[i] for i in idx], [b[i] for i in idx]
        if binario:
            xa, xb = _binarizar(xa), _binarizar(xb)
        k = kappa_cohen(xa, xb)
        if k == k:  # descarta NaN
            valores.append(k)
    valores.sort()
    return valores[int(0.025 * len(valores))], valores[int(0.975 * len(valores)) - 1]


def _binarizar(etiquetas: list[str]) -> list[str]:
    return ["no" if e == SIN_EQUIVALENTE else "si" for e in etiquetas]


def interpretar(k: float) -> str:
    """Escala de Landis y Koch (1977)."""
    if k < 0:
        return "pobre"
    for limite, texto in ((0.20, "leve"), (0.40, "aceptable"), (0.60, "moderado"), (0.80, "sustancial")):
        if k <= limite:
            return texto
    return "casi perfecto"


def calcular_acuerdo(filas: list[dict]) -> dict:
    a = [f["gold"] for f in filas]
    b = [f["segundo"] for f in filas]
    k = kappa_cohen(a, b)
    kb = kappa_cohen(_binarizar(a), _binarizar(b))
    por_par = {}
    for origen in dict.fromkeys(f["origen"] for f in filas):
        sub = [f for f in filas if f["origen"] == origen]
        por_par[origen] = {
            "n": len(sub),
            "acuerdo_observado": round(sum(f["gold"] == f["segundo"] for f in sub) / len(sub), 3),
            "kappa": round(kappa_cohen([f["gold"] for f in sub], [f["segundo"] for f in sub]), 3),
        }
    return {
        "n": len(filas),
        "acuerdo_observado": round(sum(x == y for x, y in zip(a, b, strict=True)) / len(a), 3),
        "kappa": round(k, 3),
        "kappa_ic95_bootstrap": [round(x, 3) for x in ic_bootstrap_kappa(a, b)],
        "kappa_interpretacion": interpretar(k),
        "kappa_binario": round(kb, 3),
        "kappa_binario_ic95_bootstrap": [round(x, 3) for x in ic_bootstrap_kappa(a, b, binario=True)],
        "kappa_binario_interpretacion": interpretar(kb),
        "por_par": por_par,
        "desacuerdos": [f for f in filas if f["gold"] != f["segundo"]],
        "bootstrap": {"B": BOOTSTRAP_B, "semilla": SEMILLA},
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    for flujo in (sys.stdout, sys.stderr):
        if hasattr(flujo, "reconfigure"):
            flujo.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="accion", required=True)
    p1 = sub.add_parser("planilla", help="generar Excel ciego para el segundo anotador")
    p1.add_argument("--salida", type=Path, default=Path("anotacion_ciega_gold.xlsx"))
    p2 = sub.add_parser("kappa", help="calcular acuerdo desde el Excel completado")
    p2.add_argument("planilla", type=Path)
    p2.add_argument("--json", type=Path)
    p2.add_argument("--desacuerdos", type=Path, help="CSV con los desacuerdos para adjudicar")
    args = ap.parse_args(argv)

    if args.accion == "planilla":
        n = generar_planilla(args.salida)
        print(f"Planilla ciega con {n} asignaturas: {args.salida}")
        return 0

    try:
        r = calcular_acuerdo(pares_etiquetas(leer_anotaciones(args.planilla)))
    except (ErrorAnotacion, FileNotFoundError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"Asignaturas comparadas: {r['n']}")
    print(f"Acuerdo observado: {100 * r['acuerdo_observado']:.1f}%")
    lo, hi = r["kappa_ic95_bootstrap"]
    print(f"Kappa de Cohen (multiclase): {r['kappa']:.3f}  IC95%=[{lo:.3f}; {hi:.3f}]  ({r['kappa_interpretacion']})")
    lo, hi = r["kappa_binario_ic95_bootstrap"]
    print(
        f"Kappa binario (¿hay equivalente?): {r['kappa_binario']:.3f}  IC95%=[{lo:.3f}; {hi:.3f}]  "
        f"({r['kappa_binario_interpretacion']})"
    )
    for par, d in r["por_par"].items():
        print(f"  {par}: n={d['n']}  acuerdo={100 * d['acuerdo_observado']:.1f}%  kappa={d['kappa']:.3f}")
    print(f"Desacuerdos a adjudicar: {len(r['desacuerdos'])}")
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(r, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.desacuerdos:
        with args.desacuerdos.open("w", encoding="utf-8-sig", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=["origen", "asignatura", "gold", "segundo", "decision_final"])
            w.writeheader()
            for f in r["desacuerdos"]:
                w.writerow({**f, "decision_final": ""})
        print(f"Desacuerdos: {args.desacuerdos}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
