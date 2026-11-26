"""Genera el póster académico de SIGA-DSS (A0 vertical, 841 × 1189 mm) en PPTX editable.

Reutiliza la paleta y las utilidades de `generar_ppt_defensa.py` para mantener la identidad visual de la
defensa, y las figuras reproducibles de `docs/img/`. Todas las cifras provienen del informe E3 y de los
scripts de evaluación; el póster prioriza pocas cifras clave (observación E3: láminas muy cargadas).

Uso:
  python scripts/generar_poster.py [--salida docs/Poster_SIGA_DSS.pptx]

Requiere python-pptx, Pillow y qrcode (`pip install python-pptx "qrcode[pil]"`). Para el PDF de impresión,
abrir el PPTX y exportar como PDF (PowerPoint o LibreOffice).
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

from pptx import Presentation
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

sys.path.insert(0, str(Path(__file__).resolve().parent))

from generar_ppt_defensa import (  # noqa: E402
    ASSETS_DIR,
    BG,
    BLUE,
    BRAND,
    BRAND_DARK,
    BRAND_SOFT,
    CRIT,
    CYAN,
    FONT_MONO,
    FONT_SANS,
    IMG_DIR,
    INK,
    INK_2,
    INK_3,
    LIGHT_MUTED,
    LINE,
    MINT_DARK,
    SURFACE,
    WARN,
    WHITE,
    _add_image_fit,
    _add_lines,
    _add_rect,
    _add_textbox,
    _set_paragraph,
)

RAIZ = Path(__file__).resolve().parents[1]
SALIDA_DEFAULT = RAIZ / "docs" / "Poster_SIGA_DSS.pptx"
ALTO_FIJO_SECCION = 1.3 + 0.4 + 0.3 + 1.4 + 0.6  # título + marco figura + destacado + separaciones
URL_REPO = "https://github.com/jiac1/Siga"

W, H = 33.11, 46.81  # A0 vertical en pulgadas
M = 1.0  # margen exterior
GAP = 0.8  # separación entre columnas
COL_W = (W - 2 * M - GAP) / 2
COL_L = M
COL_R = M + COL_W + GAP

CUERPO = 25.0  # puntos del texto de cuerpo


def _qr(url: str) -> Path:
    import qrcode

    img = qrcode.make(url, border=1, box_size=20)
    ruta = Path(tempfile.gettempdir()) / "siga_poster_qr.png"
    img.save(ruta)
    return ruta


def _titulo_seccion(slide, x: float, y: float, w: float, numero: str, texto: str) -> float:
    """Encabezado de sección con número en píldora; devuelve la coordenada y siguiente."""
    _add_rect(slide, x, y + 0.08, 0.95, 0.72, BRAND, rounded=True, radius_adj=0.3)
    tf = _add_textbox(slide, x, y + 0.08, 0.95, 0.72, valign=MSO_ANCHOR.MIDDLE, margin_lr=0, margin_tb=0)
    _set_paragraph(tf.paragraphs[0], [(numero, True, WHITE, FONT_SANS)], size=30, align=PP_ALIGN.CENTER, space_after=0)
    tf = _add_textbox(slide, x + 1.2, y, w - 1.2, 0.9, valign=MSO_ANCHOR.MIDDLE, margin_lr=0, margin_tb=0)
    _set_paragraph(tf.paragraphs[0], [(texto, True, INK, FONT_SANS)], size=40, space_after=0)
    _add_rect(slide, x, y + 1.02, w, 0.025, LINE)
    return y + 1.3


def _parrafos(slide, x, y, w, h, parrafos, *, size=CUERPO, color=INK_2, space_after=8.0):
    """Párrafos con negritas: cada párrafo es lista de (texto, negrita)."""
    tf = _add_textbox(slide, x, y, w, h, margin_lr=0, margin_tb=0)
    _add_lines(
        tf,
        [[(t, b, INK if b else color, FONT_SANS) for t, b in p] for p in parrafos],
        size=size,
        line_spacing=1.15,
        space_after=space_after,
    )


def _destacado(slide, x, y, w, h, partes, *, acento=BRAND, fondo=BRAND_SOFT):
    """Recuadro de resultado clave con barra lateral."""
    _add_rect(slide, x, y, w, h, fondo, rounded=True, radius_adj=0.08)
    _add_rect(slide, x, y + 0.15, 0.1, h - 0.3, acento)
    tf = _add_textbox(slide, x + 0.4, y, w - 0.6, h, valign=MSO_ANCHOR.MIDDLE, margin_lr=0, margin_tb=0)
    _add_lines(
        tf,
        [[(t, b, acento if b else INK, FONT_SANS) for t, b in p] for p in partes],
        size=CUERPO,
        line_spacing=1.12,
        space_after=4.0,
    )


def _kpi(slide, x, y, w, h, valor, etiqueta, fuente, acento):
    _add_rect(slide, x, y, w, h, SURFACE, line_color=LINE, rounded=True, radius_adj=0.06)
    _add_rect(slide, x + 0.3, y, w - 0.6, 0.12, acento)
    tf = _add_textbox(slide, x + 0.35, y + 0.35, w - 0.7, h - 0.5, margin_lr=0, margin_tb=0)
    _add_lines(
        tf,
        [
            [(valor, True, acento, FONT_SANS)],
            [(etiqueta, False, INK, FONT_SANS)],
            [(fuente, False, INK_3, FONT_SANS)],
        ],
        size=CUERPO,
        line_spacing=1.1,
        space_after=4.0,
    )
    tf.paragraphs[0].runs[0].font.size = Pt(64)
    tf.paragraphs[2].runs[0].font.size = Pt(19)


def _encabezado(slide) -> None:
    _add_rect(slide, 0, 0, W, 7.2, INK)
    _add_rect(slide, 0, 7.2, W, 0.14, BRAND)
    _add_image_fit(slide, ASSETS_DIR / "unab_facultad_ingenieria_blanco.png", M, 0.75, 7.5, 1.9, center=False)

    tf = _add_textbox(slide, M, 2.95, 24.5, 0.6, margin_lr=0, margin_tb=0)
    _set_paragraph(
        tf.paragraphs[0],
        [
            (
                "PROYECTO DE TÍTULO · INGENIERÍA CIVIL INFORMÁTICA · CINF200 · 2.º SEMESTRE 2026",
                True,
                MINT_DARK,
                FONT_SANS,
            )
        ],
        size=24,
        space_after=0,
    )
    tf = _add_textbox(slide, M, 3.45, 24.5, 1.75, valign=MSO_ANCHOR.MIDDLE, margin_lr=0, margin_tb=0)
    _set_paragraph(tf.paragraphs[0], [("SIGA-DSS", True, WHITE, FONT_SANS)], size=118, space_after=0)
    tf = _add_textbox(slide, M, 5.2, 24.5, 1.1, margin_lr=0, margin_tb=0)
    _set_paragraph(
        tf.paragraphs[0],
        [
            (
                "Sistema de soporte a la decisión para trayectorias curriculares y capacidad académica",
                False,
                LIGHT_MUTED,
                FONT_SANS,
            )
        ],
        size=33,
        line_spacing=1.1,
        space_after=0,
    )
    tf = _add_textbox(slide, M, 6.35, 24.5, 0.6, margin_lr=0, margin_tb=0)
    _set_paragraph(
        tf.paragraphs[0],
        [
            ("Felipe Riquelme Salvo · José Ignacio Amar · Maximiliano Alonso Vargas", True, WHITE, FONT_SANS),
            ("     Profesor guía: Jorge Sabattin Ortega", False, LIGHT_MUTED, FONT_SANS),
        ],
        size=25,
        space_after=0,
    )

    qx, qy, qs = W - M - 5.2, 0.7, 5.2
    _add_rect(slide, qx, qy, qs, qs + 0.95, WHITE, rounded=True, radius_adj=0.06)
    _add_image_fit(slide, _qr(URL_REPO), qx + 0.35, qy + 0.3, qs - 0.7, qs - 0.7)
    tf = _add_textbox(slide, qx, qy + qs - 0.35, qs, 1.2, valign=MSO_ANCHOR.MIDDLE, margin_lr=0, margin_tb=0)
    _add_lines(
        tf,
        [
            [("Código y demo", True, BRAND_DARK, FONT_SANS)],
            [("github.com/jiac1/Siga", True, INK, FONT_MONO)],
        ],
        size=21,
        align=PP_ALIGN.CENTER,
        space_after=0,
    )


def _problema(slide, y: float) -> float:
    y = _titulo_seccion(slide, M, y, W - 2 * M, "1", "Problema e hipótesis")
    kw, kh, kg = 6.55, 4.6, 0.45
    kpis = [
        ("13,8 sem", "duración real de Ing. Civil en Computación e Informática (nominal: 10–11)", "SIES, 2023", BRAND),
        ("~50%", "de deserción al 3.er año en Ing. Civil Informática (DIINF USACH)", "Bello et al., 2020", CRIT),
        ("34–43%", "de los créditos aprobados se pierden en traslados con convalidación manual", "GAO, 2017", BLUE),
    ]
    for i, (v, e, f, c) in enumerate(kpis):
        _kpi(slide, M + i * (kw + kg), y, kw, kh, v, e, f, c)
    hx = M + 3 * (kw + kg)
    hw = W - M - hx
    _add_rect(slide, hx, y, hw, kh, BRAND_SOFT, rounded=True, radius_adj=0.06)
    _parrafos(
        slide,
        hx + 0.45,
        y + 0.35,
        hw - 0.9,
        kh - 0.5,
        [
            [
                ("Hipótesis. ", True),
                ("Parte del rezago proviene de la estructura del currículo ", False),
                ("(prerrequisitos que bloquean la malla) y de procesos manuales fragmentados ", False),
                ("(convalidaciones, horarios, salas).", False),
            ],
            [
                ("Alcance. ", True),
                ("Se evalúa el desempeño técnico del sistema; ", False),
                ("el efecto causal sobre la deserción requiere seguimiento de cohortes.", False),
            ],
        ],
        size=23,
    )
    return y + kh + 0.9


def _seccion_figura(slide, x, y, numero, titulo, figura, alto_fig, destacado, *, acento=BRAND) -> float:
    """Altura total = alto_fig + ALTO_FIJO_SECCION."""
    y = _titulo_seccion(slide, x, y, COL_W, numero, titulo)
    _add_rect(slide, x, y, COL_W, alto_fig + 0.4, SURFACE, line_color=LINE, rounded=True, radius_adj=0.03)
    _add_image_fit(slide, IMG_DIR / figura, x + 0.2, y + 0.2, COL_W - 0.4, alto_fig)
    y += alto_fig + 0.4 + 0.3
    _destacado(slide, x, y, COL_W, 1.4, destacado, acento=acento)
    return y + 1.4 + 0.6


def _columna_izquierda(slide, y: float) -> None:
    y = _seccion_figura(
        slide,
        COL_L,
        y,
        "2",
        "Solución: un DSS en ciclo cerrado",
        "dss_ciclo_cerrado.png",
        6.1,
        [
            [("Malla DAG · Estrés curricular (MallaIQ) · Convalidación asistida", True)],
            [("Mapa de calor de salas · Generador de horarios (UCTP)", True)],
        ],
    )
    y = _seccion_figura(
        slide,
        COL_L,
        y,
        "3",
        "Arquitectura reproducible",
        "c4_contenedores.png",
        6.1,
        [
            [("69 pruebas automáticas en CI · ", True), ("Ruff sin errores", False)],
            [("1 comando: ", True), ("docker compose up --build · IaC Terraform para AWS", False)],
        ],
        acento=CYAN,
    )
    y = _titulo_seccion(slide, COL_L, y, COL_W, "4", "Datos verificables")
    _parrafos(
        slide,
        COL_L,
        y,
        COL_W,
        4.2,
        [
            [("10 mallas oficiales UNAB ", True), ("(486 asignaturas, 570 prerrequisitos).", False)],
            [
                ("27 mallas de 11 universidades ", True),
                ("(1.582 asignaturas) desde fuentes públicas trazables; ", False),
                ("auditoría por muestreo: 334/334 coinciden con la fuente.", False),
            ],
            [("Gold Standard de 112 asignaturas ", True), ("en 3 pares reales de convalidación.", False)],
            [("3 benchmarks ITC-2019 ", True), ("(International Timetabling Competition).", False)],
        ],
        size=23,
        space_after=6.0,
    )


def _columna_derecha(slide, y: float) -> None:
    y = _seccion_figura(
        slide,
        COL_R,
        y,
        "5",
        "Curricular Analytics sobre 10 mallas",
        "fig_curricular_analytics.png",
        4.3,
        [
            [("0 ciclos ", True), ("en las 10 mallas de la Facultad", False)],
            [("Intro. a la Programación ", True), ("bloquea el 52,1% del plan de Ing. Civil Informática", False)],
        ],
    )
    y = _seccion_figura(
        slide,
        COL_R,
        y,
        "6",
        "Convalidación asistida y auditable",
        "fig_eval_convalidacion.png",
        4.3,
        [
            [("F1 = 0,957 ", True), ("(IC 95%: 0,919–0,987) vs. 0,029 de la línea base", False)],
            [("0,925 ", True), ("evaluando a ciegas en un par universitario no visto", False)],
        ],
        acento=BLUE,
    )
    _seccion_figura(
        slide,
        COL_R,
        y,
        "7",
        "Horarios sin topes (UCTP)",
        "fig_benchmark_uctp.png",
        4.3,
        [
            [("100% sin topes (H1 = 0) · ", True), ("−42% a −60% de penalización vs. aleatorio", False)],
            [("Validación externa ITC-2019: ", True), ("−17% a −33% en perfiles reales", False)],
        ],
        acento=WARN,
    )


def _cierre(slide, y: float) -> None:
    alto = H - y - 1.45
    cw = (W - 2 * M - 2 * 0.6) / 3
    tarjetas = [
        (
            "Conclusiones",
            BRAND,
            [
                [("Los cuellos de botella curriculares se pueden ", False), ("medir y priorizar", True), (".", False)],
                [
                    ("La convalidación determinista ", False),
                    ("supera la meta F1 ≥ 0,90", True),
                    (" con trazabilidad y sin APIs externas.", False),
                ],
                [("Los horarios se generan ", False), ("sin topes y con menos ventanas", True), (".", False)],
            ],
        ),
        (
            "Límites y trabajo futuro",
            CRIT,
            [
                [("Despliegue en AWS ", True), ("declarado como pendiente.", False)],
                [("Encuesta SUS ", True), ("con usuarios reales: protocolo listo.", False)],
                [("Gold Standard: ", True), ("segundo anotador y kappa de Cohen.", False)],
                [("Impacto en deserción: ", True), ("requiere seguimiento de cohortes.", False)],
            ],
        ),
        (
            "Pruébelo",
            CYAN,
            [
                [("git clone github.com/jiac1/Siga", True)],
                [("cp .env.example .env", True)],
                [("docker compose up --build", True)],
                [("→ http://localhost:8080", False)],
            ],
        ),
    ]
    for i, (titulo, acento, parrafos) in enumerate(tarjetas):
        x = M + i * (cw + 0.6)
        _add_rect(slide, x, y, cw, alto, SURFACE, line_color=LINE, rounded=True, radius_adj=0.05)
        _add_rect(slide, x + 0.3, y, cw - 0.6, 0.12, acento)
        tf = _add_textbox(slide, x + 0.4, y + 0.35, cw - 0.8, 0.8, margin_lr=0, margin_tb=0)
        _set_paragraph(tf.paragraphs[0], [(titulo, True, acento, FONT_SANS)], size=34, space_after=0)
        fuente = FONT_MONO if titulo == "Pruébelo" else FONT_SANS
        tf = _add_textbox(slide, x + 0.4, y + 1.25, cw - 0.8, alto - 1.5, margin_lr=0, margin_tb=0)
        _add_lines(
            tf,
            [[(t, b, INK if b else INK_2, fuente) for t, b in p] for p in parrafos],
            size=22 if fuente == FONT_MONO else 23,
            line_spacing=1.15,
            space_after=8.0,
        )

    _add_rect(slide, 0, H - 1.0, W, 1.0, INK)
    tf = _add_textbox(slide, M, H - 1.0, W - 2 * M, 1.0, valign=MSO_ANCHOR.MIDDLE, margin_lr=0, margin_tb=0)
    _set_paragraph(
        tf.paragraphs[0],
        [
            (
                "Facultad de Ingeniería · Universidad Andrés Bello · Santiago de Chile · Noviembre 2026",
                False,
                LIGHT_MUTED,
                FONT_SANS,
            ),
            (
                "        Todas las cifras son reproducibles con los scripts de scripts/evaluacion/",
                False,
                MINT_DARK,
                FONT_SANS,
            ),
        ],
        size=19,
        space_after=0,
    )


def generar_poster(salida: Path = SALIDA_DEFAULT) -> Path:
    prs = Presentation()
    prs.slide_width = Inches(W)
    prs.slide_height = Inches(H)
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = BG

    _encabezado(slide)
    y = _problema(slide, 7.9)
    _columna_izquierda(slide, y)
    _columna_derecha(slide, y)
    _cierre(slide, 40.15)

    salida.parent.mkdir(parents=True, exist_ok=True)
    prs.save(salida)
    return salida


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--salida", type=Path, default=SALIDA_DEFAULT)
    args = ap.parse_args(argv)
    print(f"Póster generado: {generar_poster(args.salida)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
