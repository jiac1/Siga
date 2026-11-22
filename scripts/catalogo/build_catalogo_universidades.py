"""Genera el catálogo JSON de mallas de universidades de origen.

Fuente de verdad: data/universidades/transcripciones/*.txt (formato legible y
trazable, una línea por semestre). Salida:

  data/universidades/catalogo/<slug>.json      una malla por archivo
  data/universidades/catalogo/index.json       índice liviano para selectores
  data/universidades/fuentes.csv               tabla de trazabilidad (fuente, fecha, método)
  services/portal/shared/data/                 copia servida por el portal estático (incluye
                                               data/unab y data/convalidacion/conceptos.json)

Formato de cada línea de semestre:
  N | Asignatura | Asignatura [CÓDIGO] {créditos} | ~Cupo genérico | ?Asignación incierta

  ~  cupo genérico (electivo, minor, formación general): no se usa para convalidar.
  ?  el semestre asignado es incierto (p. ej. trimestre que cae entre dos semestres).

Uso:  python scripts/catalogo/build_catalogo_universidades.py [--check]
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import sys
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
ORIGEN = RAIZ / "data" / "universidades" / "transcripciones"
DESTINO = RAIZ / "data" / "universidades" / "catalogo"
PORTAL_DATOS = RAIZ / "services" / "portal" / "shared" / "data"
PORTAL = PORTAL_DATOS / "universidades"

CAMPOS_OBLIGATORIOS = ("universidad", "sigla", "carrera", "area", "fuente", "consultado")
AREAS = {"informatica", "industrial", "civil", "electrica", "minas", "plan-comun"}
RE_CODIGO = re.compile(r"\[([^\]]+)\]")
RE_CREDITOS = re.compile(r"\{(\d+)\}")


def slugify(texto: str) -> str:
    t = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")


def parsear_asignatura(crudo: str, semestre: int, orden: int, slug: str) -> dict:
    t = crudo.strip()
    incierto = generico = False
    while t[:1] in "~?":
        if t[0] == "~":
            generico = True
        else:
            incierto = True
        t = t[1:].strip()
    codigo = RE_CODIGO.search(t)
    creditos = RE_CREDITOS.search(t)
    nombre = RE_CREDITOS.sub("", RE_CODIGO.sub("", t)).strip()
    if not nombre:
        raise ValueError(f"asignatura vacía en semestre {semestre}: {crudo!r}")
    return {
        "id": f"{slug}-s{semestre}-{orden}",
        "nombre": nombre,
        "codigo": codigo.group(1).strip() if codigo else None,
        "creditos": int(creditos.group(1)) if creditos else None,
        "semestre": semestre,
        "generico": generico,
        "incierto": incierto,
    }


def parsear_archivo(ruta: Path) -> dict:
    meta: dict[str, str] = {}
    semestres: list[dict] = []
    slug = ruta.stem
    for n, linea in enumerate(ruta.read_text(encoding="utf-8").splitlines(), 1):
        linea = linea.strip()
        if not linea:
            continue
        if linea.startswith("#"):
            clave, _, valor = linea[1:].partition(":")
            meta[clave.strip().lower()] = valor.strip()
            continue
        num, _, resto = linea.partition("|")
        if not num.strip().isdigit():
            raise ValueError(f"{ruta.name}:{n}: se esperaba 'N | ...'")
        sem = int(num)
        partes = [p for p in resto.split("|") if p.strip()]
        semestres.append(
            {
                "numero": sem,
                "asignaturas": [parsear_asignatura(p, sem, i, slug) for i, p in enumerate(partes, 1)],
            }
        )

    faltan = [c for c in CAMPOS_OBLIGATORIOS if not meta.get(c)]
    if faltan:
        raise ValueError(f"{ruta.name}: faltan metadatos {faltan}")
    if meta["area"] not in AREAS:
        raise ValueError(f"{ruta.name}: área desconocida {meta['area']!r} (válidas: {sorted(AREAS)})")

    asignaturas = [a for s in semestres for a in s["asignaturas"]]
    return {
        "slug": slug,
        "universidad": meta["universidad"],
        "sigla": meta["sigla"],
        "carrera": meta["carrera"],
        "area": meta["area"],
        "plan": meta.get("plan"),
        "regimen": meta.get("regimen", "semestral"),
        "duracion": int(meta["duracion"]) if meta.get("duracion", "").isdigit() else len(semestres),
        "unidad_creditos": meta.get("creditos"),
        "fuente": {
            "url": meta["fuente"],
            "consultado": meta["consultado"],
            "metodo": meta.get("metodo"),
            "notas": meta.get("notas"),
        },
        "estadisticas": {
            "asignaturas": len(asignaturas),
            "convalidables": sum(1 for a in asignaturas if not a["generico"]),
            "genericas": sum(1 for a in asignaturas if a["generico"]),
            "inciertas": sum(1 for a in asignaturas if a["incierto"]),
        },
        "semestres": semestres,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true", help="solo valida, no escribe archivos")
    args = ap.parse_args()

    mallas = [parsear_archivo(p) for p in sorted(ORIGEN.glob("*.txt"))]
    if not mallas:
        print("No hay transcripciones en", ORIGEN, file=sys.stderr)
        return 1
    indice = [
        {
            "slug": m["slug"],
            "universidad": m["universidad"],
            "sigla": m["sigla"],
            "carrera": m["carrera"],
            "area": m["area"],
            "plan": m["plan"],
            "duracion": m["duracion"],
            "regimen": m["regimen"],
            "asignaturas": m["estadisticas"]["convalidables"],
        }
        for m in mallas
    ]
    indice.sort(key=lambda x: (x["universidad"], x["carrera"]))

    print(
        f"{len(mallas)} mallas · {len({m['sigla'] for m in mallas})} universidades · "
        f"{sum(m['estadisticas']['convalidables'] for m in mallas)} asignaturas convalidables"
    )
    if args.check:
        return 0

    DESTINO.mkdir(parents=True, exist_ok=True)
    for viejo in DESTINO.glob("*.json"):
        viejo.unlink()
    for m in mallas:
        (DESTINO / f"{m['slug']}.json").write_text(json.dumps(m, ensure_ascii=False, indent=1), encoding="utf-8")
    (DESTINO / "index.json").write_text(json.dumps(indice, ensure_ascii=False, indent=1), encoding="utf-8")

    with (RAIZ / "data" / "universidades" / "fuentes.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["slug", "universidad", "carrera", "plan", "asignaturas", "fuente_url", "consultado", "metodo"])
        for m in mallas:
            w.writerow(
                [
                    m["slug"],
                    m["universidad"],
                    m["carrera"],
                    m["plan"],
                    m["estadisticas"]["convalidables"],
                    m["fuente"]["url"],
                    m["fuente"]["consultado"],
                    m["fuente"]["metodo"],
                ]
            )

    if PORTAL.exists():
        shutil.rmtree(PORTAL)
    shutil.copytree(DESTINO, PORTAL)
    (PORTAL_DATOS / "unab").mkdir(parents=True, exist_ok=True)
    shutil.copy2(RAIZ / "data" / "unab" / "base-convalidacion.json", PORTAL_DATOS / "unab" / "base-convalidacion.json")
    (PORTAL_DATOS / "convalidacion").mkdir(parents=True, exist_ok=True)
    shutil.copy2(RAIZ / "data" / "convalidacion" / "conceptos.json", PORTAL_DATOS / "convalidacion" / "conceptos.json")
    print("Escrito en", DESTINO.relative_to(RAIZ), "y", PORTAL_DATOS.relative_to(RAIZ))
    return 0


if __name__ == "__main__":
    sys.exit(main())
