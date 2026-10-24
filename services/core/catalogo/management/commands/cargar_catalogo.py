"""Carga (idempotente) el catálogo curricular desde data/.

  data/unab/base-convalidacion.json            mallas UNAB con contenidos y aprendizajes
  data/universidades/catalogo/*.json           mallas de universidades de origen

Uso: python manage.py cargar_catalogo [--data-dir RUTA]
"""

import json
import re
import unicodedata
from datetime import date
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from catalogo.models import Asignatura, Carrera, Universidad

AREAS_UNAB = [
    ("informatica", ("informatica", "computacion")),
    ("industrial", ("industrial",)),
    ("electrica", ("electrica",)),
    ("automatizacion", ("automatizacion", "robotica")),
    ("geologia", ("geologia",)),
    ("comercial", ("comercial",)),
]


def slugify(texto: str) -> str:
    t = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")


def area_unab(nombre: str) -> str:
    s = slugify(nombre)
    return next((area for area, claves in AREAS_UNAB if any(k in s for k in claves)), "otra")


def _con_ocurrencia(pares):
    """Clave única (semestre, nombre, n-ésima aparición): soporta cupos repetidos como 'Electivo'."""
    vistos: dict = {}
    for sem, nombre in pares:
        base = (sem, nombre.lower())
        vistos[base] = vistos.get(base, 0) + 1
        yield (*base, vistos[base])


def sincronizar(carrera: Carrera, filas: list[dict]) -> None:
    """Actualiza en sitio para no romper equivalencias ni solicitudes que referencian asignaturas."""
    actuales = list(carrera.asignaturas.order_by("id"))
    existentes = dict(zip(_con_ocurrencia((a.semestre, a.nombre) for a in actuales), actuales, strict=True))
    nuevas = list(_con_ocurrencia((f["semestre"], f["nombre"]) for f in filas))
    for clave, fila in zip(nuevas, filas, strict=True):
        actual = existentes.get(clave)
        if actual is None:
            Asignatura.objects.create(carrera=carrera, **fila)
        else:
            for k, v in fila.items():
                setattr(actual, k, v)
            actual.save()
    for clave in set(existentes) - set(nuevas):
        existentes[clave].delete()


class Command(BaseCommand):
    help = "Carga o actualiza el catálogo de mallas (UNAB y universidades de origen)"

    def add_arguments(self, parser):
        parser.add_argument("--data-dir", default=settings.DATA_DIR)

    @transaction.atomic
    def handle(self, *args, data_dir, **opts):
        raiz = Path(data_dir)
        base_unab = raiz / "unab" / "base-convalidacion.json"
        catalogo = raiz / "universidades" / "catalogo"
        if not base_unab.exists() or not catalogo.exists():
            raise CommandError(f"No se encontró el catálogo en {raiz}")

        unab, _ = Universidad.objects.update_or_create(
            sigla="UNAB", defaults={"nombre": "Universidad Andrés Bello", "es_destino": True}
        )
        n_unab = 0
        for nombre, asignaturas in json.loads(base_unab.read_text(encoding="utf-8")).items():
            carrera, _ = Carrera.objects.update_or_create(
                slug=f"unab-{slugify(nombre)}",
                defaults={
                    "universidad": unab,
                    "nombre": nombre,
                    "area": area_unab(nombre),
                    "duracion": max((a.get("semestre") or 0) for a in asignaturas) or 10,
                    "fuente_metodo": "Base curricular del sistema de convalidación UNAB (programas oficiales)",
                },
            )
            sincronizar(
                carrera,
                [
                    dict(
                        codigo=a.get("codigo") or "",
                        nombre=a["nombre"],
                        semestre=a.get("semestre") or 0,
                        creditos=a.get("creditos"),
                        contenidos=a.get("contenidos") or "",
                        aprendizajes=a.get("aprendizajes") or [],
                    )
                    for a in asignaturas
                ],
            )
            n_unab += 1

        n_origen = 0
        for ruta in sorted(catalogo.glob("*.json")):
            if ruta.name == "index.json":
                continue
            m = json.loads(ruta.read_text(encoding="utf-8"))
            uni, _ = Universidad.objects.update_or_create(sigla=m["sigla"], defaults={"nombre": m["universidad"]})
            consultado = m["fuente"].get("consultado")
            carrera, _ = Carrera.objects.update_or_create(
                slug=m["slug"],
                defaults={
                    "universidad": uni,
                    "nombre": m["carrera"],
                    "area": m["area"],
                    "plan": m.get("plan") or "",
                    "regimen": m.get("regimen", "semestral"),
                    "duracion": m.get("duracion") or len(m["semestres"]),
                    "fuente_url": m["fuente"]["url"],
                    "fuente_metodo": m["fuente"].get("metodo") or "",
                    "fuente_consultada": date.fromisoformat(consultado) if consultado else None,
                    "notas": m["fuente"].get("notas") or "",
                },
            )
            sincronizar(
                carrera,
                [
                    dict(
                        codigo=a.get("codigo") or "",
                        nombre=a["nombre"],
                        semestre=a["semestre"],
                        creditos=a.get("creditos"),
                        generica=a.get("generico", False),
                        semestre_incierto=a.get("incierto", False),
                    )
                    for s in m["semestres"]
                    for a in s["asignaturas"]
                ],
            )
            n_origen += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Catálogo cargado: {n_unab} carreras UNAB, {n_origen} mallas de origen, "
                f"{Asignatura.objects.count()} asignaturas"
            )
        )
