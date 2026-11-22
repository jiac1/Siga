"""Extrae las mallas UNAB embebidas en la app Malla curricular a JSON.

Reemplaza a services/portal/scripts/extraer_mallas.js (requería Node.js y
rutas absolutas de otro equipo). Lee el arreglo `CURSOS` de cada
services/portal/apps/malla/malla_*.html y escribe:

  services/portal/shared/mallas/<slug>.json + index.json   (catálogo del portal)
  services/estres-malla/static/mallas/                      (copia para Estrés de Malla
                                                             en modo independiente)

Uso:  python scripts/catalogo/extraer_mallas_unab.py
"""

from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
MALLAS_HTML = RAIZ / "services" / "portal" / "apps" / "malla"
SALIDA = RAIZ / "services" / "portal" / "shared" / "mallas"
COPIA_ESTRES = RAIZ / "services" / "estres-malla" / "static" / "mallas"
RE_CURSOS = re.compile(r"<script>const CURSOS = (\[.*?\]);</script>", re.S)

# Metadatos de cada carrera (nombre y resolución), igual que en apps/malla/index.html
CARRERAS = [
    (
        "automatizacion-robotica",
        "malla_automatizacion_robotica.html",
        "Ingeniería en Automatización y Robótica",
        "DUN 14-2022",
    ),
    ("civil-electrica", "malla_ingenieria_civil_electrica.html", "Ingeniería Civil Eléctrica", "DUN 84-2022"),
    ("civil-informatica", "malla_ingenieria_civil_informatica.html", "Ingeniería Civil Informática", "Plan 12210"),
    (
        "computacion-informatica",
        "malla_ingenieria_en_computacion_e_informatica.html",
        "Ingeniería en Computación e Informática",
        "Res. 2719-2020",
    ),
    ("industrial", "malla_ingenieria_industrial.html", "Ingeniería Industrial", "DUN 71-2022"),
    ("civil", "malla_ingenieria_civil.html", "Ingeniería Civil", "Plan 11300"),
    ("civil-minas", "malla_ingenieria_civil_en_minas.html", "Ingeniería Civil en Minas", "Plan 11303"),
    ("construccion", "malla_ingenieria_en_construccion.html", "Ingeniería en Construcción", "Plan 11400"),
    ("civil-industrial", "malla_ingenieria_civil_industrial.html", "Ingeniería Civil Industrial", "Plan 12100"),
    (
        "civil-industrial-2-0",
        "malla_ingenieria_civil_industrial_2_0.html",
        "Ingeniería Civil Industrial 2.0",
        "UNAB37044",
    ),
]


def main() -> int:
    SALIDA.mkdir(parents=True, exist_ok=True)
    indice = []
    for slug, archivo, nombre, badge in CARRERAS:
        html = (MALLAS_HTML / archivo).read_text(encoding="utf-8")
        m = RE_CURSOS.search(html)
        if not m:
            print("Sin arreglo CURSOS en", archivo, file=sys.stderr)
            return 1
        cursos = json.loads(m.group(1))
        semestres = {c["semestre"] for c in cursos}
        total = sum(c.get("creditos") or 0 for c in cursos)
        datos = {
            "slug": slug,
            "nombre": nombre,
            "badge": badge,
            "href": archivo,
            "nCursos": len(cursos),
            "nSemestres": len(semestres),
            "totalCreditos": total,
            "cursos": [
                {
                    "codigo": c["codigo"],
                    "nombre": c["nombre"],
                    "semestre": c["semestre"],
                    "creditos": c.get("creditos"),
                    "area": c.get("area") or "",
                    "lane": c.get("lane"),
                    "requisitos": c.get("requisitos") or [],
                }
                for c in cursos
            ],
        }
        (SALIDA / f"{slug}.json").write_text(
            json.dumps(datos, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
        )
        indice.append(
            {
                "slug": slug,
                "nombre": nombre,
                "badge": badge,
                "nCursos": len(cursos),
                "nSemestres": len(semestres),
                "totalCreditos": total,
            }
        )
        print(f"OK {slug}: {len(cursos)} cursos, {len(semestres)} semestres")
    (SALIDA / "index.json").write_text(json.dumps(indice, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    if COPIA_ESTRES.exists():
        shutil.rmtree(COPIA_ESTRES)
    shutil.copytree(SALIDA, COPIA_ESTRES)
    print("Catálogo UNAB escrito en", SALIDA.relative_to(RAIZ), "y copiado a", COPIA_ESTRES.relative_to(RAIZ))
    return 0


if __name__ == "__main__":
    sys.exit(main())
