"""Pruebas del análisis SUS. Los datos de estas pruebas son ficticios y solo validan el cálculo."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from analizar_sus import (  # noqa: E402
    ErrorDatos,
    analizar,
    ic_bootstrap,
    leer_respuestas,
    main,
    puntaje_sus,
    rango_aceptabilidad,
    tabla_markdown,
)

PLANTILLA = Path(__file__).resolve().parents[3] / "data" / "evaluacion_sus" / "plantilla_respuestas.csv"
ENCABEZADO = PLANTILLA.read_text(encoding="utf-8").strip()


def _csv(tmp_path: Path, filas: list[str], sep: str = ",") -> Path:
    ruta = tmp_path / "respuestas.csv"
    ruta.write_text("\n".join([ENCABEZADO.replace(",", sep)] + filas) + "\n", encoding="utf-8")
    return ruta


def _fila(pid, perfil="estudiante", consentimiento="si", sus=(4, 2) * 5, tareas=("1", "60") * 3 + ("", "")):
    return ",".join([pid, perfil, "2026-12-01", consentimiento, *map(str, sus), *tareas, ""])


def test_puntaje_sus_extremos_y_neutro():
    assert puntaje_sus([5, 1] * 5) == 100.0
    assert puntaje_sus([1, 5] * 5) == 0.0
    assert puntaje_sus([3] * 10) == 50.0
    assert puntaje_sus([4, 2] * 5) == 75.0


def test_puntaje_sus_rechaza_fuera_de_escala():
    with pytest.raises(ErrorDatos):
        puntaje_sus([6] + [3] * 9)
    with pytest.raises(ErrorDatos):
        puntaje_sus([3] * 9)


def test_rangos_bangor():
    assert rango_aceptabilidad(70) == "aceptable"
    assert rango_aceptabilidad(69.9) == "marginal"
    assert rango_aceptabilidad(49.9) == "no aceptable"


def test_ic_bootstrap_contiene_media_y_es_determinista():
    valores = [55.0, 62.5, 70.0, 72.5, 80.0, 85.0, 90.0]
    lo, hi = ic_bootstrap(valores)
    assert lo <= sum(valores) / len(valores) <= hi
    assert (lo, hi) == ic_bootstrap(valores)


def test_lectura_excluye_sin_consentimiento_y_analiza_tareas(tmp_path):
    ruta = _csv(
        tmp_path,
        [
            _fila("P01"),
            _fila("P02", sus=(5, 1) * 5, tareas=("1", "40", "0", "", "parcial", "90", "", "")),
            _fila("P03", consentimiento="no"),
            _fila("S01", perfil="staff", sus=(3,) * 10, tareas=("1", "50") * 4),
        ],
    )
    participantes, avisos = leer_respuestas(ruta)
    assert [p.id for p in participantes] == ["P01", "P02", "S01"]
    assert len(avisos) == 1 and "consentimiento" in avisos[0]

    r = analizar(participantes)
    assert r["global"]["n"] == 3
    assert r["global"]["media"] == pytest.approx((75 + 100 + 50) / 3, abs=0.01)
    assert r["por_perfil"]["estudiante"]["n"] == 2
    assert r["tareas"]["t2"]["tasa_exito"] == pytest.approx(2 / 3, abs=0.001)
    assert r["tareas"]["t3"]["tasa_exito"] == pytest.approx(2.5 / 3, abs=0.001)
    assert r["tareas"]["t4"]["n"] == 1  # T4 solo se aplicó a staff
    assert "| **Global** | 3 |" in tabla_markdown(r)


def test_acepta_csv_con_punto_y_coma(tmp_path):
    ruta = _csv(tmp_path, [_fila("P01").replace(",", ";")], sep=";")
    participantes, _ = leer_respuestas(ruta)
    assert participantes[0].sus == 75.0


def test_rechaza_duplicados_y_columnas_faltantes(tmp_path):
    with pytest.raises(ErrorDatos, match="duplicado"):
        leer_respuestas(_csv(tmp_path, [_fila("P01"), _fila("P01")]))
    ruta = tmp_path / "malo.csv"
    ruta.write_text("participante_id,perfil\nP01,estudiante\n", encoding="utf-8")
    with pytest.raises(ErrorDatos, match="Faltan columnas"):
        leer_respuestas(ruta)


def test_plantilla_vacia_no_inventa_resultados(capsys):
    assert main([str(PLANTILLA)]) == 1
    assert "No hay participantes válidos" in capsys.readouterr().err
