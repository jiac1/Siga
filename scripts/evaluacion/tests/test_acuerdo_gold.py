"""Pruebas del cálculo de acuerdo entre anotadores del Gold Standard."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from acuerdo_gold import (  # noqa: E402
    HOJA_CATALOGO,
    SIN_EQUIVALENTE,
    ErrorAnotacion,
    calcular_acuerdo,
    cargar_gold,
    generar_planilla,
    interpretar,
    kappa_cohen,
    leer_anotaciones,
    main,
    nombre_hoja,
    normalizar_etiqueta,
    pares_etiquetas,
)

openpyxl = pytest.importorskip("openpyxl")


def test_kappa_valores_de_referencia():
    assert kappa_cohen(["a", "b", "a", "b"], ["a", "b", "a", "b"]) == 1.0
    # Tabla 2x2 equilibrada: po=0,80, pe=0,50 -> kappa=0,60
    a = ["si"] * 20 + ["si"] * 5 + ["no"] * 5 + ["no"] * 20
    b = ["si"] * 20 + ["no"] * 5 + ["si"] * 5 + ["no"] * 20
    assert kappa_cohen(a, b) == pytest.approx(0.6, abs=1e-9)
    # Tabla desequilibrada: po=0,70, pe=0,54 -> kappa=0,16/0,46
    a = ["si"] * 25 + ["si"] * 10 + ["no"] * 5 + ["no"] * 10
    b = ["si"] * 25 + ["no"] * 10 + ["si"] * 5 + ["no"] * 10
    assert kappa_cohen(a, b) == pytest.approx(0.16 / 0.46, abs=1e-9)


def test_interpretacion_landis_koch():
    assert interpretar(0.85) == "casi perfecto"
    assert interpretar(0.7) == "sustancial"
    assert interpretar(0.5) == "moderado"
    assert interpretar(-0.1) == "pobre"


def test_normalizar_etiqueta_desde_lista_desplegable():
    assert normalizar_etiqueta("fmmp112 · Cálculo Diferencial") == "FMMP112"
    assert normalizar_etiqueta(SIN_EQUIVALENTE) == SIN_EQUIVALENTE
    assert normalizar_etiqueta("  ") is None


def _completar(ruta: Path, salida: Path, cambiar: int = 0) -> None:
    """Rellena la planilla ciega con las etiquetas del gold; las primeras `cambiar` filas se alteran."""
    casos = {c["origen"]: c for c in cargar_gold()}
    wb = openpyxl.load_workbook(ruta)
    alteradas = 0
    for i, caso in enumerate(casos.values(), start=1):
        hoja = wb[nombre_hoja(i, caso)]
        for fila in hoja.iter_rows(min_row=3):
            gold = caso["etiquetas"][fila[1].value]
            valor = SIN_EQUIVALENTE if gold is None else (gold if isinstance(gold, str) else gold[-1])
            if alteradas < cambiar:
                valor = "ZZZ999" if valor == SIN_EQUIVALENTE else SIN_EQUIVALENTE
                alteradas += 1
            fila[2].value = valor
    wb.save(salida)


def test_planilla_es_ciega_y_completa(tmp_path):
    ruta = tmp_path / "ciega.xlsx"
    assert generar_planilla(ruta) == 112
    wb = openpyxl.load_workbook(ruta)
    assert HOJA_CATALOGO in wb.sheetnames
    gold = cargar_gold()
    for i, caso in enumerate(gold, start=1):
        filas = list(wb[nombre_hoja(i, caso)].iter_rows(min_row=3, values_only=True))
        assert {f[1] for f in filas} == set(caso["etiquetas"])
        assert all(f[2] is None for f in filas)  # sin etiquetas originales
        assert [f[1] for f in filas] != list(caso["etiquetas"])  # orden aleatorio


def test_acuerdo_perfecto_y_con_desacuerdos(tmp_path):
    ciega = tmp_path / "ciega.xlsx"
    generar_planilla(ciega)

    perfecta = tmp_path / "perfecta.xlsx"
    _completar(ciega, perfecta)
    r = calcular_acuerdo(pares_etiquetas(leer_anotaciones(perfecta)))
    assert r["n"] == 112 and r["kappa"] == 1.0 and r["desacuerdos"] == []

    con_errores = tmp_path / "errores.xlsx"
    _completar(ciega, con_errores, cambiar=10)
    r = calcular_acuerdo(pares_etiquetas(leer_anotaciones(con_errores)))
    assert len(r["desacuerdos"]) == 10
    assert r["acuerdo_observado"] == pytest.approx(102 / 112, abs=0.001)
    assert 0 < r["kappa"] < 1
    lo, hi = r["kappa_ic95_bootstrap"]
    assert lo <= r["kappa"] <= hi


def test_planilla_incompleta_se_rechaza(tmp_path, capsys):
    ciega = tmp_path / "ciega.xlsx"
    generar_planilla(ciega)
    with pytest.raises(ErrorAnotacion, match="sin completar"):
        leer_anotaciones(ciega)
    assert main(["kappa", str(ciega)]) == 1
