"""Pruebas unitarias del motor (sin base de datos) y umbral mínimo de calidad."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

from convalidaciones.motor import Conceptos, nivel_de, normalizar_nombre, similitud_nombres, stem, tokenizar

RAIZ = Path(__file__).resolve().parents[3]


def test_stem_conserva_raices():
    assert stem("operadores") == "operador"
    assert stem("bases") == "base"
    assert stem("variables") == "variable"
    assert stem("datos") == "dato"


def test_tokenizar_quita_acentos_y_vacias():
    assert tokenizar("Programación de las Bases de Datos") == ["programacion", "base", "dato"]


def test_normalizar_quita_sufijos():
    assert normalizar_nombre("Cálculo I para Ingeniería") == "calculo i"
    assert normalizar_nombre("Business Intelligence (Inglés)") == "business intelligence"


def test_nivel():
    assert nivel_de("Cálculo II") == 2
    assert nivel_de("Inglés 3") == 3
    assert nivel_de("Bases de Datos") is None


def test_conceptos():
    c = Conceptos.desde_archivo(RAIZ / "data" / "convalidacion" / "conceptos.json")
    assert "calculo-diferencial" in c.de("Cálculo en una Variable")
    assert "bases-de-datos" in c.de("Diseño de Bases de Datos")
    assert c.de("Teología I") == set()


def test_similitud_nombres_simetrica():
    idf = {"base": 1.0, "dato": 1.0, "diseno": 2.0}
    assert similitud_nombres("Base de Datos", "Bases de Datos", idf) == 1.0
    assert similitud_nombres("Diseño de Bases de Datos", "Base de Datos", idf) == similitud_nombres(
        "Base de Datos", "Diseño de Bases de Datos", idf
    )


def test_calidad_minima_en_conjunto_de_evaluacion():
    """Evita regresiones: el F1 del motor en el conjunto etiquetado no debe caer bajo 0.85."""
    salida = Path(tempfile.mkdtemp()) / "eval.json"
    subprocess.run(
        [sys.executable, str(RAIZ / "scripts" / "evaluacion" / "evaluar_motor.py"), "--json", str(salida)],
        check=True,
        capture_output=True,
    )
    resumen = json.loads(salida.read_text(encoding="utf-8"))["resumen"]["mejorado"]
    assert resumen["f1"] >= 0.85 and resumen["precision"] >= 0.85
