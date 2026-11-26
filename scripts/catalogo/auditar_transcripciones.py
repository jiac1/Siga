"""Auditoría por muestreo de las transcripciones del catálogo curricular nacional.

Responde a la pregunta de defensa: «¿cómo se verificó la transcripción de las 1.582 asignaturas?».
El pipeline (build_catalogo_universidades.py) valida el FORMATO de las transcripciones; esta auditoría
contrasta su CONTENIDO con la fuente oficial:

  1) sortea una muestra de mallas con semilla fija (reproducible)
  2) descarga la fuente oficial registrada en data/universidades/fuentes.csv
  3) si el PDF tiene capa de texto, busca automáticamente cada asignatura transcrita
  4) deja en un CSV las asignaturas no encontradas automáticamente (y las fuentes sin texto o en imagen)
     para revisión visual humana

Uso:
  python scripts/catalogo/auditar_transcripciones.py --muestra 6 --semilla 2026 \\
      --cache <carpeta_descargas> --csv auditoria.csv [--sin-descarga]
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import re
import sys
import unicodedata
import urllib.request
from difflib import SequenceMatcher
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
FUENTES = RAIZ / "data" / "universidades" / "fuentes.csv"
CATALOGO = RAIZ / "data" / "universidades" / "catalogo"
UMBRAL_SIMILITUD = 0.88


def normalizar(texto: str) -> str:
    # Primero separar por cualquier símbolo (viñetas «•» pegadas en la capa de texto), luego quitar tildes
    t = re.sub(r"[^\w]+", " ", texto)
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().lower()
    t = re.sub(r"[^a-z0-9]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def asignaturas_transcritas(slug: str) -> list[dict]:
    d = json.loads((CATALOGO / f"{slug}.json").read_text(encoding="utf-8"))
    filas = []
    for sem in d["semestres"]:
        for a in sem["asignaturas"]:
            filas.append({"semestre": sem["numero"], "nombre": a["nombre"], "generico": a.get("generico", False)})
    return filas


def texto_pdf(ruta: Path) -> str:
    from pypdf import PdfReader

    return " ".join((p.extract_text() or "") for p in PdfReader(str(ruta)).pages)


def buscar(nombre: str, texto_norm: str) -> tuple[bool, float]:
    """Coincidencia exacta normalizada o, si no, la mejor ventana de igual largo en palabras."""
    n = normalizar(nombre)
    if not n:
        return False, 0.0
    if f" {n} " in f" {texto_norm} ":
        return True, 1.0
    palabras_t = texto_norm.split()
    k = len(n.split())
    mejor = 0.0
    for largo in {k, k + 1, max(1, k - 1)}:
        for i in range(0, max(0, len(palabras_t) - largo) + 1):
            r = SequenceMatcher(None, n, " ".join(palabras_t[i : i + largo])).ratio()
            mejor = max(mejor, r)
    return mejor >= UMBRAL_SIMILITUD, round(mejor, 3)


def descargar(url: str, destino: Path) -> Path:
    destino.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (auditoria academica)"})
    with urllib.request.urlopen(req, timeout=60) as resp:  # noqa: S310 (URL de fuentes.csv versionado)
        destino.write_bytes(resp.read())
    return destino


def main(argv: list[str] | None = None) -> int:
    for flujo in (sys.stdout, sys.stderr):
        if hasattr(flujo, "reconfigure"):
            flujo.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--muestra", type=int, default=6)
    ap.add_argument("--semilla", type=int, default=2026)
    ap.add_argument("--cache", type=Path, required=True, help="carpeta para las fuentes descargadas")
    ap.add_argument("--csv", type=Path, help="detalle por asignatura")
    ap.add_argument("--sin-descarga", action="store_true", help="usar solo archivos ya presentes en --cache")
    args = ap.parse_args(argv)

    fuentes = list(csv.DictReader(FUENTES.open(encoding="utf-8")))
    muestra = random.Random(args.semilla).sample(fuentes, args.muestra)
    detalle: list[dict] = []
    total = encontradas = 0
    print(f"Muestra de {len(muestra)} de {len(fuentes)} mallas (semilla {args.semilla})\n")
    for f in muestra:
        slug, url = f["slug"], f["fuente_url"]
        ext = Path(url.split("?")[0]).suffix.lower() or ".bin"
        archivo = args.cache / f"{slug}{ext}"
        if not archivo.exists() and not args.sin_descarga:
            descargar(url, archivo)
        asigs = asignaturas_transcritas(slug)
        texto = ""
        if ext == ".pdf" and archivo.exists():
            texto = normalizar(texto_pdf(archivo))
        modo = "automatica" if len(texto) > 200 else "visual"
        ok_malla = 0
        for a in asigs:
            if modo == "automatica":
                ok, sim = buscar(a["nombre"], texto)
            else:
                ok, sim = False, None
            ok_malla += ok
            detalle.append(
                {
                    "slug": slug,
                    "semestre": a["semestre"],
                    "asignatura": a["nombre"],
                    "generico": a["generico"],
                    "modo": modo,
                    "encontrada_auto": ok,
                    "similitud": sim,
                    "revision_visual": "" if ok else "PENDIENTE",
                }
            )
        total += len(asigs)
        encontradas += ok_malla
        estado = (
            f"{ok_malla}/{len(asigs)} encontradas en la capa de texto"
            if modo == "automatica"
            else "sin capa de texto: revisión visual"
        )
        print(f"  {slug:35s} {estado}")

    print(
        f"\nAsignaturas auditadas: {total} · verificadas automáticamente: {encontradas} · "
        f"a revisión visual: {total - encontradas}"
    )
    if args.csv:
        args.csv.parent.mkdir(parents=True, exist_ok=True)
        with args.csv.open("w", encoding="utf-8-sig", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(detalle[0]))
            w.writeheader()
            w.writerows(detalle)
        print(f"Detalle: {args.csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
