"""Genera la presentación de defensa final E3 de SIGA-DSS en formato 16:9.

Aplica el sistema visual editorial de SIGA (`#1D6B55`, `#F6F6F2`, `#191B16`)
con tipografía nativa Windows (`Segoe UI` / `Consolas`), gráficos de alta
resolución en `docs/img/` y logotipos oficiales de la Facultad de Ingeniería UNAB.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

RAIZ = Path(__file__).resolve().parents[1]
IMG_DIR = RAIZ / "docs" / "img"
ASSETS_DIR = IMG_DIR / "assets"
SALIDA_DEFAULT = RAIZ / "docs" / "Presentacion_Defensa_SIGA_DSS.pptx"

SLIDE_W = Inches(40 / 3)  # 13.333 in exactos (16:9)
SLIDE_H = Inches(7.5)

FONT_SANS = "Segoe UI"
FONT_MONO = "Consolas"

# Paleta editorial SIGA (`services/portal/apps/siga/index.html`)
BRAND = RGBColor(29, 107, 85)
BRAND_2 = RGBColor(35, 128, 95)
BRAND_DARK = RGBColor(21, 78, 62)
BRAND_SOFT = RGBColor(231, 241, 236)
BG = RGBColor(246, 246, 242)
BG_2 = RGBColor(239, 239, 234)
SURFACE = RGBColor(255, 255, 255)
SURFACE_2 = RGBColor(244, 244, 239)
INK = RGBColor(25, 27, 22)
INK_2 = RGBColor(91, 94, 86)
INK_3 = RGBColor(142, 145, 137)
LINE = RGBColor(222, 222, 215)
OK = RGBColor(42, 157, 92)
OK_BG = RGBColor(233, 246, 238)
WARN = RGBColor(216, 155, 30)
WARN_BG = RGBColor(251, 243, 225)
CRIT = RGBColor(199, 60, 46)
CRIT_BG = RGBColor(250, 233, 230)
CYAN = RGBColor(12, 133, 153)
CYAN_SOFT = RGBColor(236, 250, 252)
BLUE = RGBColor(63, 98, 224)
MINT_DARK = RGBColor(127, 211, 182)
DARK_CARD = RGBColor(34, 38, 31)
DARK_LINE = RGBColor(58, 64, 53)
WHITE = RGBColor(255, 255, 255)
LIGHT_MUTED = RGBColor(200, 206, 198)


def _new_blank_slide(prs: Presentation, bg_color: RGBColor = BG):
    """Agrega una diapositiva en blanco con fondo sólido."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = bg_color
    return slide


def _add_rect(
    slide,
    x: float,
    y: float,
    w: float,
    h: float,
    fill_color: RGBColor,
    *,
    line_color: RGBColor | None = None,
    line_pt: float = 1.0,
    rounded: bool = False,
    radius_adj: float = 0.04,
):
    """Crea un rectángulo o tarjeta redondeada sin sombra intrusiva."""
    shape_type = MSO_SHAPE.ROUNDED_RECTANGLE if rounded else MSO_SHAPE.RECTANGLE
    shape = slide.shapes.add_shape(shape_type, Inches(x), Inches(y), Inches(w), Inches(h))
    if rounded and len(shape.adjustments) > 0:
        shape.adjustments[0] = radius_adj
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill_color
    if line_color is not None:
        shape.line.color.rgb = line_color
        shape.line.width = Pt(line_pt)
    else:
        shape.line.fill.background()
    shape.shadow.inherit = False
    return shape


def _add_card(
    slide,
    x: float,
    y: float,
    w: float,
    h: float,
    *,
    fill: RGBColor = SURFACE,
    border: RGBColor | None = LINE,
    accent_left: RGBColor | None = None,
    accent_top: RGBColor | None = None,
    radius_adj: float = 0.03,
):
    """Agrega una tarjeta redondeada limpia con banda de acento opcional."""
    card = _add_rect(slide, x, y, w, h, fill, line_color=border, line_pt=1.0, rounded=True, radius_adj=radius_adj)
    if accent_left is not None:
        _add_rect(slide, x, y + 0.12, 0.065, h - 0.24, accent_left)
    if accent_top is not None:
        _add_rect(slide, x + 0.14, y, w - 0.28, 0.055, accent_top)
    return card


def _add_textbox(
    slide,
    x: float,
    y: float,
    w: float,
    h: float,
    *,
    valign: MSO_ANCHOR = MSO_ANCHOR.TOP,
    margin_lr: float = 0.04,
    margin_tb: float = 0.02,
):
    """Agrega un cuadro de texto configurado para ajuste limpio de palabra."""
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = valign
    tf.margin_left = Inches(margin_lr)
    tf.margin_right = Inches(margin_lr)
    tf.margin_top = Inches(margin_tb)
    tf.margin_bottom = Inches(margin_tb)
    return tf


def _set_paragraph(
    para,
    segments: list[tuple[str, bool, RGBColor, str]],
    *,
    size: float = 12.0,
    align: PP_ALIGN = PP_ALIGN.LEFT,
    line_spacing: float = 1.18,
    space_after: float = 4.0,
) -> None:
    """Rellena un párrafo con segmentos tipográficos diferenciados."""
    para.alignment = align
    para.line_spacing = line_spacing
    para.space_after = Pt(space_after)
    for text, bold, color, font_name in segments:
        run = para.add_run()
        run.text = text
        run.font.name = font_name
        run.font.size = Pt(size)
        run.font.bold = bold
        run.font.color.rgb = color


def _add_lines(
    tf,
    paragraphs: list[list[tuple[str, bool, RGBColor, str]]],
    *,
    size: float = 12.0,
    align: PP_ALIGN = PP_ALIGN.LEFT,
    line_spacing: float = 1.18,
    space_after: float = 5.0,
) -> None:
    """Agrega múltiples párrafos con formato rico a un text_frame."""
    for idx, segs in enumerate(paragraphs):
        p = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
        sa = 0.0 if idx == len(paragraphs) - 1 else space_after
        _set_paragraph(p, segs, size=size, align=align, line_spacing=line_spacing, space_after=sa)


def _add_badge(
    slide,
    text: str,
    x: float,
    y: float,
    w: float,
    h: float,
    *,
    fill: RGBColor = BRAND_SOFT,
    text_color: RGBColor = BRAND,
    border: RGBColor | None = None,
    size: float = 9.0,
    font_name: str = FONT_SANS,
    bold: bool = True,
):
    """Agrega una píldora tipográfica centrada."""
    pill = _add_rect(slide, x, y, w, h, fill, line_color=border, line_pt=0.8, rounded=True, radius_adj=0.45)
    tf = pill.text_frame
    tf.word_wrap = False
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_left = Inches(0.06)
    tf.margin_right = Inches(0.06)
    tf.margin_top = Inches(0.01)
    tf.margin_bottom = Inches(0.01)
    _set_paragraph(
        tf.paragraphs[0], [(text, bold, text_color, font_name)], size=size, align=PP_ALIGN.CENTER, space_after=0
    )
    return pill


def _add_image_fit(
    slide,
    img_path: Path,
    x: float,
    y: float,
    max_w: float,
    max_h: float,
    *,
    center: bool = True,
) -> None:
    """Inserta una imagen preservando estrictamente su relación de aspecto."""
    if not img_path.exists():
        raise FileNotFoundError(f"Asset de imagen requerido no encontrado: {img_path}")
    with Image.open(img_path) as im:
        iw, ih = im.size
    aspect = iw / ih
    box_aspect = max_w / max_h
    if aspect >= box_aspect:
        w = max_w
        h = max_w / aspect
    else:
        h = max_h
        w = max_h * aspect
    px = x + (max_w - w) / 2 if center else x
    py = y + (max_h - h) / 2 if center else y
    slide.shapes.add_picture(str(img_path), Inches(px), Inches(py), width=Inches(w), height=Inches(h))


def _add_chrome(
    slide,
    kicker: str,
    title: str,
    slide_num: int,
    *,
    role_tag: str,
    total_slides: int = 12,
) -> None:
    """Aplica cabecera editorial SIGA y pie de página consistente en slides de contenido."""
    _add_rect(slide, 0.0, 0.0, 13.333, 0.065, BRAND)
    _add_rect(slide, 0.60, 0.41, 0.28, 0.032, BRAND)

    tf_k = _add_textbox(slide, 0.96, 0.28, 8.0, 0.28, valign=MSO_ANCHOR.MIDDLE, margin_lr=0, margin_tb=0)
    _set_paragraph(tf_k.paragraphs[0], [(kicker.upper(), True, BRAND, FONT_SANS)], size=9.5, space_after=0)

    _add_badge(
        slide,
        role_tag,
        10.18,
        0.25,
        2.55,
        0.30,
        fill=BRAND_SOFT,
        text_color=BRAND_DARK,
        border=RGBColor(183, 222, 201),
        size=8.5,
    )

    tf_t = _add_textbox(slide, 0.58, 0.58, 12.15, 0.54, valign=MSO_ANCHOR.MIDDLE, margin_lr=0, margin_tb=0)
    _set_paragraph(tf_t.paragraphs[0], [(title, True, INK, FONT_SANS)], size=23.0, line_spacing=1.08, space_after=0)

    _add_rect(slide, 0.60, 7.06, 12.13, 0.012, LINE)
    tf_fl = _add_textbox(slide, 0.60, 7.12, 9.5, 0.26, valign=MSO_ANCHOR.MIDDLE, margin_lr=0, margin_tb=0)
    _set_paragraph(
        tf_fl.paragraphs[0],
        [("SIGA-DSS · Facultad de Ingeniería UNAB · CINF200", False, INK_3, FONT_SANS)],
        size=8.8,
        space_after=0,
    )
    tf_fr = _add_textbox(slide, 10.8, 7.12, 1.93, 0.26, valign=MSO_ANCHOR.MIDDLE, margin_lr=0, margin_tb=0)
    _set_paragraph(
        tf_fr.paragraphs[0],
        [(f"{slide_num} / {total_slides}", True, BRAND, FONT_MONO)],
        size=9.2,
        align=PP_ALIGN.RIGHT,
        space_after=0,
    )


def _add_kpi_card(
    slide,
    x: float,
    y: float,
    w: float,
    h: float,
    value: str,
    label: str,
    detail: str,
    *,
    accent: RGBColor = BRAND,
    value_size: float = 28.0,
) -> None:
    """Renderiza una tarjeta métrica KPI con barra superior y detalle."""
    _add_card(slide, x, y, w, h, fill=SURFACE, border=LINE, accent_top=accent)
    tf = _add_textbox(slide, x + 0.16, y + 0.14, w - 0.32, h - 0.24, valign=MSO_ANCHOR.TOP)
    _add_lines(
        tf,
        [
            [(label.upper(), True, INK_3, FONT_SANS)],
            [(value, True, accent, FONT_SANS)],
            [(detail, False, INK_2, FONT_SANS)],
        ],
        size=10.5,
        line_spacing=1.18,
        space_after=3.0,
    )
    tf.paragraphs[0].runs[0].font.size = Pt(8.8)
    tf.paragraphs[1].runs[0].font.size = Pt(value_size)
    tf.paragraphs[1].space_after = Pt(4.0)
    tf.paragraphs[2].runs[0].font.size = Pt(10.0)


def _set_notes(slide, text: str) -> None:
    """Adjunta notas breves del expositor en la diapositiva."""
    slide.notes_slide.notes_text_frame.text = text.strip()


def _build_slide_01_portada(prs: Presentation) -> None:
    slide = _new_blank_slide(prs, INK)
    _add_rect(slide, 0.0, 0.0, 13.333, 0.08, BRAND)

    # Marca SIGA-DSS superior izquierda
    mark = _add_rect(slide, 0.72, 0.56, 0.44, 0.44, BRAND, rounded=True, radius_adj=0.22)
    tf_m = mark.text_frame
    tf_m.vertical_anchor = MSO_ANCHOR.MIDDLE
    _set_paragraph(tf_m.paragraphs[0], [("S", True, WHITE, FONT_SANS)], size=18.0, align=PP_ALIGN.CENTER, space_after=0)

    tf_b = _add_textbox(slide, 1.28, 0.52, 4.5, 0.52, valign=MSO_ANCHOR.MIDDLE, margin_lr=0, margin_tb=0)
    _add_lines(
        tf_b,
        [
            [("SIGA-DSS", True, WHITE, FONT_SANS)],
            [("SISTEMA DE SOPORTE A LA DECISIÓN ACADÉMICA", True, MINT_DARK, FONT_MONO)],
        ],
        size=9.5,
        line_spacing=1.08,
        space_after=1.0,
    )
    tf_b.paragraphs[0].runs[0].font.size = Pt(16.0)
    tf_b.paragraphs[1].runs[0].font.size = Pt(8.2)

    # Logo oficial blanco Facultad de Ingeniería UNAB arriba a la derecha
    _add_image_fit(slide, ASSETS_DIR / "unab_facultad_ingenieria_blanco.png", 9.65, 0.42, 3.05, 1.05, center=True)

    _add_badge(
        slide,
        "DEFENSA FINAL E3 · CINF200 · NOVIEMBRE 2026",
        0.72,
        1.78,
        4.35,
        0.34,
        fill=DARK_CARD,
        text_color=MINT_DARK,
        border=BRAND,
        size=9.2,
        font_name=FONT_MONO,
    )

    tf_t = _add_textbox(slide, 0.70, 2.30, 11.90, 1.55, valign=MSO_ANCHOR.TOP, margin_lr=0, margin_tb=0)
    _add_lines(
        tf_t,
        [
            [("SIGA-DSS: Plataforma Modular para ", True, WHITE, FONT_SANS)],
            [
                ("Trayectorias Curriculares", True, MINT_DARK, FONT_SANS),
                (" y Capacidad Académica", True, WHITE, FONT_SANS),
            ],
        ],
        size=31.0,
        line_spacing=1.12,
        space_after=2.0,
    )

    tf_sub = _add_textbox(slide, 0.72, 3.92, 10.6, 0.90, valign=MSO_ANCHOR.TOP, margin_lr=0, margin_tb=0)
    _set_paragraph(
        tf_sub.paragraphs[0],
        [
            (
                "Arquitectura en ciclo cerrado con Grafos DAG (Curricular Analytics), motor híbrido de convalidaciones "
                "y optimización combinatoria de horarios (UCTP) · Facultad de Ingeniería UNAB",
                False,
                LIGHT_MUTED,
                FONT_SANS,
            )
        ],
        size=14.0,
        line_spacing=1.28,
        space_after=0,
    )

    # Barra inferior de metadatos
    _add_rect(
        slide, 0.72, 5.72, 11.90, 1.24, DARK_CARD, line_color=DARK_LINE, line_pt=1.0, rounded=True, radius_adj=0.06
    )
    _add_rect(slide, 0.72, 5.84, 0.06, 1.00, BRAND_2)

    cols = [
        ("AUTORES", "Felipe Riquelme Salvo · José Ignacio Amar · Maximiliano Alonso Vargas", 0.96, 5.65),
        ("PROFESOR GUÍA", "Jorge Humberto Sabattin Ortega", 6.85, 3.25),
        ("ASIGNATURA / SEDE", "CINF200 · Santiago de Chile", 10.30, 2.20),
    ]
    for lbl, val, cx, cw in cols:
        tf_c = _add_textbox(slide, cx, 5.86, cw, 0.96, valign=MSO_ANCHOR.MIDDLE, margin_lr=0, margin_tb=0)
        _add_lines(
            tf_c,
            [[(lbl, True, MINT_DARK, FONT_MONO)], [(val, False, WHITE, FONT_SANS)]],
            size=11.5,
            line_spacing=1.22,
            space_after=3.0,
        )
        tf_c.paragraphs[0].runs[0].font.size = Pt(8.6)
        tf_c.paragraphs[1].runs[0].font.size = Pt(11.4)

    _set_notes(slide, "José Ignacio (0:30): Saludo, presentación del título SIGA-DSS, equipo y contexto CINF200 UNAB.")


def _build_slide_02_diagnostico(prs: Presentation) -> None:
    slide = _new_blank_slide(prs)
    _add_chrome(
        slide,
        "01 · Diagnóstico del Problema",
        "La sobreduración en ingeniería exige atacar cuellos de botella y fragmentación",
        2,
        role_tag="José Ignacio · Bloque 1",
    )

    kpis = [
        (
            "13,8 sem",
            "Duración real TIC (SIES)",
            "+2,91 sem en exceso sobre 10–11 nominales (3,45 en ejecución).",
            BRAND,
        ),
        (
            "~50%",
            "Deserción al 3.er año",
            "DIINF USACH: 28,0% (2017) y 21,9% (2018) en 1.er año; ~50% al 3.er año.",
            CRIT,
        ),
        (
            ">US$1.100M",
            "Impacto país quinquenal",
            "US$128–141M anuales directos por deserción temprana en Chile.",
            CYAN,
        ),
        (
            "34%–43%",
            "Créditos perdidos (GAO)",
            "Convalidaciones ≥90% multiplican por 2,5× la probabilidad de titulación.",
            BLUE,
        ),
    ]
    for idx, (val, lbl, det, col) in enumerate(kpis):
        _add_kpi_card(slide, 0.60 + idx * 3.08, 1.32, 2.88, 1.98, val, lbl, det, accent=col, value_size=26.0)

    # Dos tarjetas inferiores
    _add_card(slide, 0.60, 3.55, 5.95, 3.25, fill=SURFACE, border=LINE, accent_left=BRAND)
    tf_l = _add_textbox(slide, 0.86, 3.74, 5.50, 2.90)
    _add_lines(
        tf_l,
        [
            [("Evidencia Estructural en la Literatura", True, BRAND_DARK, FONT_SANS)],
            [
                ("• 76,21% de desertores tardíos", True, INK, FONT_SANS),
                (
                    " abandonan adeudando asignaturas cuello de botella tras ~9 semestres "
                    "(Salazar-Fernández et al., 2021).",
                    False,
                    INK_2,
                    FONT_SANS,
                ),
            ],
            [
                ("• 6 de los 7 predictores críticos", True, INK, FONT_SANS),
                (
                    " de abandono provienen del rendimiento en el 1.er semestre (Bello et al., 2020).",
                    False,
                    INK_2,
                    FONT_SANS,
                ),
            ],
            [
                ("• +20 pts de complejidad C(G)", True, INK, FONT_SANS),
                (
                    " reducen en 3,74% la titulación oportuna (Slim et al., 2016); auditorías guiadas suben +17 pp.",
                    False,
                    INK_2,
                    FONT_SANS,
                ),
            ],
        ],
        size=11.6,
        line_spacing=1.24,
        space_after=8.0,
    )
    tf_l.paragraphs[0].runs[0].font.size = Pt(14.5)

    _add_card(slide, 6.78, 3.55, 5.95, 3.25, fill=SURFACE, border=LINE, accent_left=CRIT)
    tf_r = _add_textbox(slide, 7.04, 3.74, 5.50, 2.90)
    _add_lines(
        tf_r,
        [
            [("Brecha Operativa Previa en Ingeniería UNAB", True, CRIT, FONT_SANS)],
            [
                ("• Herramientas aisladas:", True, INK, FONT_SANS),
                (
                    " scripts locales de horarios, planillas Banner/Syaproa y mallas estáticas sin contrato común.",
                    False,
                    INK_2,
                    FONT_SANS,
                ),
            ],
            [
                ("• Cero autenticación ni pruebas:", True, INK, FONT_SANS),
                (
                    " sin SSO federado, sin aislamiento multi-tenant ni pruebas automatizadas de regresión.",
                    False,
                    INK_2,
                    FONT_SANS,
                ),
            ],
            [
                ("• Convalidación manual lenta:", True, INK, FONT_SANS),
                (
                    " línea base textual original alcanzaba apenas F1 = 0,029; sin optimización de ventanas UCTP.",
                    False,
                    INK_2,
                    FONT_SANS,
                ),
            ],
        ],
        size=11.6,
        line_spacing=1.24,
        space_after=8.0,
    )
    tf_r.paragraphs[0].runs[0].font.size = Pt(14.5)

    _set_notes(
        slide, "José Ignacio (1:00): Cifras duras SIES/USACH/GAO y brecha inicial en Facultad de Ingeniería UNAB."
    )


def _build_slide_03_ciclo_cerrado(prs: Presentation) -> None:
    slide = _new_blank_slide(prs)
    _add_chrome(
        slide,
        "02 · Hipótesis y Visión de Sistema",
        "SIGA-DSS articula demanda curricular y oferta operativa en ciclo cerrado",
        3,
        role_tag="José Ignacio · Bloque 1",
    )

    _add_card(slide, 0.60, 1.32, 4.65, 2.65, fill=BRAND_SOFT, border=RGBColor(183, 222, 201), accent_left=BRAND)
    tf_h = _add_textbox(slide, 0.86, 1.48, 4.22, 2.35)
    _add_lines(
        tf_h,
        [
            [("HIPÓTESIS CENTRAL", True, BRAND, FONT_MONO)],
            [
                (
                    "Unificar trayectorias DAG, convalidación asistida y optimización UCTP bajo un DSS modular, "
                    "auditable y reproducible permite diagnosticar cuellos de botella, acelerar traslados con alta "
                    "precisión y generar horarios libres de topes con ventanas mínimas.",
                    False,
                    INK,
                    FONT_SANS,
                )
            ],
        ],
        size=11.4,
        line_spacing=1.26,
        space_after=6.0,
    )
    tf_h.paragraphs[0].runs[0].font.size = Pt(9.2)

    _add_card(slide, 0.60, 4.14, 4.65, 2.66, fill=SURFACE, border=LINE)
    tf_o = _add_textbox(slide, 0.82, 4.28, 4.24, 2.40)
    _add_lines(
        tf_o,
        [
            [("Tres Pilares de Cumplimiento (OE1–OE7)", True, INK, FONT_SANS)],
            [
                ("1. Demanda Pedagógica: ", True, BRAND, FONT_SANS),
                ("mallas DAG sin ciclos, estrés MallaIQ y motor IA ≥ 0,90 F1.", False, INK_2, FONT_SANS),
            ],
            [
                ("2. Capacidad Operativa: ", True, CYAN, FONT_SANS),
                ("mapa de calor Banner/Syaproa y solver UCTP B&B + SA.", False, INK_2, FONT_SANS),
            ],
            [
                ("3. Ingeniería Reproducible: ", True, INK, FONT_SANS),
                ("suite-sso JWT, 69 tests CI/CD, Docker 1-comando e IaC AWS.", False, INK_2, FONT_SANS),
            ],
        ],
        size=10.8,
        line_spacing=1.22,
        space_after=6.0,
    )
    tf_o.paragraphs[0].runs[0].font.size = Pt(13.0)

    _add_card(slide, 5.48, 1.32, 7.25, 5.48, fill=SURFACE, border=LINE)
    _add_image_fit(slide, IMG_DIR / "dss_ciclo_cerrado.png", 5.64, 1.46, 6.93, 5.20, center=True)

    _set_notes(
        slide,
        "José Ignacio (1:00): Explicar cómo la demanda pedagógica retroalimenta "
        "la capacidad física de salas y secciones.",
    )


def _build_slide_04_suite_catalogo(prs: Presentation) -> None:
    slide = _new_blank_slide(prs)
    _add_chrome(
        slide,
        "03 · Suite Modular y Catálogo",
        "Cinco aplicaciones integradas tras un portal único y catálogo nacional curado",
        4,
        role_tag="José Ignacio · Bloque 1",
    )

    modulos = [
        (
            "Malla Interactiva (DAG)",
            "Estudiantes",
            BRAND,
            BRAND_SOFT,
            "10 mallas UNAB con recorrido BFS/DFS de prerrequisitos, cascada de aprobación y avance SCT.",
        ),
        (
            "Generador de Horarios (UCTP)",
            "Estudiantes",
            BRAND,
            BRAND_SOFT,
            "Resuelve combinaciones sin topes (H1=0) minimizando ventanas, días activos y carga.",
        ),
        (
            "Convalidaciones con IA",
            "Postulantes",
            CYAN,
            CYAN_SOFT,
            "Pre-evaluación TF-IDF + 50 conceptos + Dice-IDF con precedentes aprobados y folio CV-*.",
        ),
        (
            "Estrés de Malla (MallaIQ)",
            "Gestión",
            BRAND,
            BRAND_SOFT,
            "Métricas Curricular Analytics b(v), d(v), c(v) cruzadas con actas históricas de reprobación.",
        ),
        (
            "Mapa de Calor de Salas",
            "Gestión",
            CYAN,
            CYAN_SOFT,
            "Analítica matricial stateless de ocupación por campus, edificio y bloque (M1–M20) + .xlsx.",
        ),
        (
            "Portal y Modo Dual",
            "Suite / Standalone",
            INK,
            BG_2,
            "Tokens visuales compartidos, barra suite-bar, licencias multi-tenant y operación autónoma.",
        ),
    ]
    for idx, (nombre, rol, accent, badge_bg, desc) in enumerate(modulos):
        col = idx % 3
        row = idx // 3
        cx = 0.60 + col * 4.10
        cy = 1.32 + row * 2.15
        _add_card(slide, cx, cy, 3.92, 1.96, fill=SURFACE, border=LINE, accent_left=accent)
        _add_badge(
            slide,
            rol.upper(),
            cx + 0.22,
            cy + 0.18,
            1.45,
            0.26,
            fill=badge_bg,
            text_color=accent,
            size=8.0,
            font_name=FONT_MONO,
        )
        tf = _add_textbox(slide, cx + 0.20, cy + 0.52, 3.55, 1.32)
        _add_lines(
            tf,
            [[(nombre, True, INK, FONT_SANS)], [(desc, False, INK_2, FONT_SANS)]],
            size=10.8,
            line_spacing=1.22,
            space_after=5.0,
        )
        tf.paragraphs[0].runs[0].font.size = Pt(13.2)

    # Banda inferior de datos verificados
    _add_rect(slide, 0.60, 5.74, 12.13, 1.06, INK, rounded=True, radius_adj=0.06)
    _add_rect(slide, 0.60, 5.74, 12.13, 0.055, BRAND_2)
    banda = [
        ("10 mallas UNAB", "486 ramos · 570 aristas DAG", 0.88),
        ("27 mallas externas", "11 universidades · 1.582 ramos", 3.90),
        ("400 ramos destino", "9 carreras UNAB (257 códigos)", 6.95),
        ("50 conceptos + 112 Gold", "Trazabilidad en fuentes.csv", 9.95),
    ]
    for title_b, sub_b, bx in banda:
        tf_b = _add_textbox(slide, bx, 5.88, 2.75, 0.80, valign=MSO_ANCHOR.MIDDLE, margin_lr=0, margin_tb=0)
        _add_lines(
            tf_b,
            [[(title_b, True, MINT_DARK, FONT_SANS)], [(sub_b, False, LIGHT_MUTED, FONT_SANS)]],
            size=10.5,
            line_spacing=1.18,
            space_after=2.0,
        )
        tf_b.paragraphs[0].runs[0].font.size = Pt(14.5)

    _set_notes(
        slide, "José Ignacio (1:00): Cerrar bloque presentando catálogo nacional y dar pase a Felipe para arquitectura."
    )


def _build_slide_05_arquitectura_c4(prs: Presentation) -> None:
    slide = _new_blank_slide(prs)
    _add_chrome(
        slide,
        "04 · Arquitectura de Software",
        "Modelo C4: microservicios desacoplados tras un gateway único",
        5,
        role_tag="Felipe · Bloque 2",
    )

    _add_card(slide, 0.60, 1.26, 12.13, 4.18, fill=SURFACE, border=LINE)
    _add_image_fit(slide, IMG_DIR / "c4_contenedores.png", 0.78, 1.34, 11.77, 4.02, center=True)

    pilares = [
        (
            "Desacoplamiento por Dominio",
            BRAND,
            "core (identidad, catálogo, IA, UCTP), estres-malla (multi-tenant) y "
            "mapa-calor (stateless) operan con ciclo de vida propio.",
        ),
        (
            "Gateway Reverse Proxy Único",
            CYAN,
            "Enrutamiento por prefijo sin reescritura (/core/*, /estres-malla/*, "
            "/mapa-calor/*) en Nginx :8080 y CloudFront + ALB.",
        ),
        (
            "Paridad Local ↔ AWS Terraform",
            INK,
            "1 comando docker compose up --build en local; VPC multi-AZ, ECS Fargate "
            "(Circuit Breaker), RDS SSL y S3 OAC en infra/terraform.",
        ),
    ]
    for idx, (tit, col, desc) in enumerate(pilares):
        cx = 0.60 + idx * 4.10
        _add_card(slide, cx, 5.58, 3.92, 1.26, fill=SURFACE, border=LINE, accent_left=col)
        tf = _add_textbox(slide, cx + 0.18, 5.66, 3.60, 1.12)
        _add_lines(
            tf,
            [[(tit, True, col if col != INK else INK, FONT_SANS)], [(desc, False, INK_2, FONT_SANS)]],
            size=10.2,
            line_spacing=1.18,
            space_after=3.0,
        )
        tf.paragraphs[0].runs[0].font.size = Pt(12.2)

    _set_notes(
        slide,
        "Felipe (1:10): Recorrer diagrama C4 de arriba hacia abajo: usuarios -> "
        "gateway -> 4 servicios -> BDs y suite-sso.",
    )


def _build_slide_06_seguridad_privacidad(prs: Presentation) -> None:
    slide = _new_blank_slide(prs)
    _add_chrome(
        slide,
        "05 · Seguridad, SSO y Cumplimiento",
        "Autenticación federada sin estado (suite-sso), OWASP y Ley 21.719 por diseño",
        6,
        role_tag="Felipe · Bloque 2",
    )

    # Tarjeta izquierda: suite-sso & Control de Acceso
    _add_card(slide, 0.60, 1.32, 5.95, 4.35, fill=SURFACE, border=LINE, accent_top=BRAND)
    _add_badge(
        slide,
        "PAQUETE SUITE-SSO",
        0.86,
        1.56,
        1.85,
        0.28,
        fill=BRAND_SOFT,
        text_color=BRAND_DARK,
        size=8.2,
        font_name=FONT_MONO,
    )
    tf_l = _add_textbox(slide, 0.82, 1.94, 5.50, 3.55)
    _add_lines(
        tf_l,
        [
            [("Identidad Sin Estado y Control de Acceso (A01–A04)", True, INK, FONT_SANS)],
            [
                ("• JWT HMAC-SHA256 en cookie HttpOnly: ", True, BRAND_DARK, FONT_SANS),
                (
                    "claims iss, aud, exp, iat, roles y módulos; secreto mínimo ≥ 32 caracteres.",
                    False,
                    INK_2,
                    FONT_SANS,
                ),
            ],
            [
                ("• Validación local sin cuello de botella: ", True, BRAND_DARK, FONT_SANS),
                ("126,7 µs/ciclo (~7.890 ops/s en 1 núcleo) sin consultar la BD de core.", False, INK_2, FONT_SANS),
            ],
            [
                ("• Defensa activa OWASP: ", True, BRAND_DARK, FONT_SANS),
                (
                    "rechazo alg=none, RBAC en 5 roles, aislamiento cross-tenant "
                    "(HTTP 404) y protección Open Redirect.",
                    False,
                    INK_2,
                    FONT_SANS,
                ),
            ],
            [
                ("• Integridad y throttling: ", True, BRAND_DARK, FONT_SANS),
                (
                    "recálculo obligatorio server-side, validación RUT mod-11 y "
                    "límites DRF (60/min anon, 240/min user, 10/h).",
                    False,
                    INK_2,
                    FONT_SANS,
                ),
            ],
        ],
        size=11.4,
        line_spacing=1.24,
        space_after=8.0,
    )
    tf_l.paragraphs[0].runs[0].font.size = Pt(14.5)

    # Tarjeta derecha: Ley 21.719 & Endurecimiento IaC
    _add_card(slide, 6.78, 1.32, 5.95, 4.35, fill=SURFACE, border=LINE, accent_top=CYAN)
    _add_badge(
        slide,
        "LEY 21.719 · TERRAFORM AWS",
        7.04,
        1.56,
        2.40,
        0.28,
        fill=CYAN_SOFT,
        text_color=CYAN,
        size=8.2,
        font_name=FONT_MONO,
    )
    tf_r = _add_textbox(slide, 7.00, 1.94, 5.50, 3.55)
    _add_lines(
        tf_r,
        [
            [("Privacidad por Diseño e Infraestructura (A05)", True, INK, FONT_SANS)],
            [
                ("• Consentimiento y auditoría inmutable: ", True, CYAN, FONT_SANS),
                ("flujo de convalidación exige consentimiento y traza en EventoAuditoria.", False, INK_2, FONT_SANS),
            ],
            [
                ("• Retención y purga automática (730 días): ", True, CYAN, FONT_SANS),
                (
                    "comando purgar_datos_vencidos anonimiza PII preservando precedentes estadísticos.",
                    False,
                    INK_2,
                    FONT_SANS,
                ),
            ],
            [
                ("• Endurecimiento perimetral e IaC: ", True, CYAN, FONT_SANS),
                (
                    "HSTS, X-Frame-Options, nosniff, S3 privado + OAC, cabecera X-Origen-Suite en ALB y WAFv2.",
                    False,
                    INK_2,
                    FONT_SANS,
                ),
            ],
            [
                ("• Cifrado y despliegue sin secretos estáticos: ", True, CYAN, FONT_SANS),
                ("RDS PostgreSQL rds.force_ssl=1, Secrets Manager y GitHub Actions OIDC.", False, INK_2, FONT_SANS),
            ],
        ],
        size=11.4,
        line_spacing=1.24,
        space_after=8.0,
    )
    tf_r.paragraphs[0].runs[0].font.size = Pt(14.5)

    # Barra inferior con brechas declaradas con transparencia
    _add_card(slide, 0.60, 5.84, 12.13, 0.96, fill=BG_2, border=LINE, accent_left=WARN)
    tf_b = _add_textbox(slide, 0.84, 5.92, 11.75, 0.80, valign=MSO_ANCHOR.MIDDLE)
    _set_paragraph(
        tf_b.paragraphs[0],
        [
            ("Transparencia de brechas residuales: ", True, INK, FONT_SANS),
            (
                "MFA/IdP delegable a Azure AD (SAML/OIDC UNAB), rotación futura a firma asimétrica RS256/JWKS "
                "y DAST pendiente sobre el ambiente AWS vivo tras aprovisionamiento.",
                False,
                INK_2,
                FONT_SANS,
            ),
        ],
        size=10.8,
        line_spacing=1.20,
        space_after=0,
    )

    _set_notes(
        slide,
        "Felipe (1:00): Enfatizar JWT sin estado (126,7 us), aislamiento multi-tenant y purga automática Ley 21.719.",
    )


def _build_slide_07_etl_cicd(prs: Presentation) -> None:
    slide = _new_blank_slide(prs)
    _add_chrome(
        slide,
        "06 · Ingeniería, ETL y Calidad",
        "Pipeline ETL trazable y CI/CD con compuertas automáticas de regresión",
        7,
        role_tag="Felipe · Bloque 2",
    )

    _add_card(slide, 0.60, 1.32, 7.62, 5.48, fill=SURFACE, border=LINE)
    _add_image_fit(slide, IMG_DIR / "pipeline_etl.png", 0.76, 1.46, 7.30, 5.20, center=True)

    # Columna derecha: tarjeta hero verde + 3 bloques de compuertas
    _add_rect(slide, 8.42, 1.32, 4.31, 1.62, BRAND, rounded=True, radius_adj=0.05)
    tf_hero = _add_textbox(slide, 8.64, 1.44, 3.88, 1.38, valign=MSO_ANCHOR.MIDDLE)
    _add_lines(
        tf_hero,
        [
            [("SUITE DE VERIFICACIÓN CI/CD", True, MINT_DARK, FONT_MONO)],
            [("69 / 69 tests", True, WHITE, FONT_SANS)],
            [("pytest en los 4 módulos + Ruff 0 errores + terraform validate", False, LIGHT_MUTED, FONT_SANS)],
        ],
        size=10.5,
        line_spacing=1.18,
        space_after=3.0,
    )
    tf_hero.paragraphs[0].runs[0].font.size = Pt(8.8)
    tf_hero.paragraphs[1].runs[0].font.size = Pt(28.0)

    gates = [
        (
            "Cobertura por Módulo",
            "suite-sso (6) · core Identidad/IA (33) · UCTP/Campus (13) · mapa-calor (6) · estres-malla (11).",
            BRAND,
        ),
        (
            "Compuerta Algorítmica",
            "evaluar_motor.py exige F1 ≥ 0,90; evaluar_uctp.py y test_mallas_dag.py bloquean ciclos o choques.",
            CYAN,
        ),
        (
            "E2E y Eficiencia Medida",
            "Playwright Chromium OK (0 errores JS); mapa-calor 267,5 ms, estres-malla 20,7 ms y carga idempotente.",
            OK,
        ),
    ]
    for idx, (tit, desc, col) in enumerate(gates):
        cy = 3.12 + idx * 1.28
        _add_card(slide, 8.42, cy, 4.31, 1.12, fill=SURFACE, border=LINE, accent_left=col)
        tf_g = _add_textbox(slide, 8.64, cy + 0.10, 3.92, 0.94, valign=MSO_ANCHOR.MIDDLE)
        _add_lines(
            tf_g,
            [[(tit, True, INK, FONT_SANS)], [(desc, False, INK_2, FONT_SANS)]],
            size=10.2,
            line_spacing=1.16,
            space_after=2.0,
        )
        tf_g.paragraphs[0].runs[0].font.size = Pt(12.2)

    _set_notes(
        slide,
        "Felipe (1:00): Mostrar cómo los datos pasan de decretos a PostgreSQL/JSON, "
        "destacar 69/69 tests y dar pase a Maximiliano.",
    )


def _build_slide_08_curricular_analytics(prs: Presentation) -> None:
    slide = _new_blank_slide(prs)
    _add_chrome(
        slide,
        "07 · Motores Analíticos · Curricular Analytics",
        "Auditoría DAG en 10 mallas UNAB: 0 ciclos y cuellos de botella cuantificados",
        8,
        role_tag="Maximiliano · Bloque 3",
    )

    _add_card(slide, 0.60, 1.32, 7.82, 5.48, fill=SURFACE, border=LINE)
    _add_image_fit(slide, IMG_DIR / "fig_curricular_analytics.png", 0.74, 1.46, 7.54, 5.20, center=True)

    _add_kpi_card(
        slide,
        8.62,
        1.32,
        4.11,
        1.30,
        "0 ciclos · 16,1 ms",
        "Validación topológica (Kahn + DFS)",
        "486 asignaturas y 570 aristas verificadas en las 10 mallas UNAB.",
        accent=BRAND,
        value_size=23.0,
    )
    _add_kpi_card(
        slide,
        8.62,
        2.74,
        4.11,
        1.42,
        "52,1% bloqueo",
        "TDFI102 · Intro. a la Programación",
        "b = 25, d = 7, c = 32 en Ing. Civil Informática (C(G) = 492); seguida por PTEC101 (c = 29).",
        accent=CRIT,
        value_size=23.0,
    )
    _add_kpi_card(
        slide,
        8.62,
        4.28,
        4.11,
        1.30,
        "d = 8 semestres",
        "Camino crítico matemático",
        "FMMP012 (c = 22) y FMMP112 (c = 20) definen la cadena más larga de la carrera.",
        accent=CYAN,
        value_size=23.0,
    )

    _add_card(slide, 8.62, 5.70, 4.11, 1.10, fill=BRAND_SOFT, border=RGBColor(183, 222, 201), accent_left=BRAND)
    tf_f = _add_textbox(slide, 8.84, 5.78, 3.74, 0.94, valign=MSO_ANCHOR.MIDDLE)
    _add_lines(
        tf_f,
        [
            [("Índice de Estrés MallaIQ", True, BRAND_DARK, FONT_SANS)],
            [("e(v) = c(v) · (1 − aprob(v) / 100)", True, INK, FONT_MONO)],
            [("Cruza topología DAG con tasas reales de actas.", False, INK_2, FONT_SANS)],
        ],
        size=10.0,
        line_spacing=1.18,
        space_after=2.0,
    )
    tf_f.paragraphs[0].runs[0].font.size = Pt(11.4)

    _set_notes(
        slide,
        "Maximiliano (1:00): Destacar el puente entre topología DAG y la evidencia "
        "de Bello et al. (2020) del 1.er semestre.",
    )


def _build_slide_09_convalidacion(prs: Presentation) -> None:
    slide = _new_blank_slide(prs)
    _add_chrome(
        slide,
        "08 · Motor Híbrido de Convalidaciones",
        "Salto desde F1 = 0,029 a F1 = 0,957 determinista, auditable y en 752 ms",
        9,
        role_tag="Maximiliano · Bloque 3",
    )

    _add_card(slide, 0.60, 1.32, 7.72, 5.48, fill=SURFACE, border=LINE)
    _add_image_fit(slide, IMG_DIR / "fig_eval_convalidacion.png", 0.72, 1.46, 7.48, 5.20, center=True)

    # Tarjeta Hero F1
    _add_rect(slide, 8.50, 1.32, 4.23, 1.62, BRAND, rounded=True, radius_adj=0.05)
    tf_h = _add_textbox(slide, 8.72, 1.40, 3.82, 1.46, valign=MSO_ANCHOR.MIDDLE)
    _add_lines(
        tf_h,
        [
            [("GOLD STANDARD · n = 112 (3 PARES)", True, MINT_DARK, FONT_MONO)],
            [("F1 = 0,957", True, WHITE, FONT_SANS)],
            [("IC95%: [0,919; 0,987]", True, MINT_DARK, FONT_MONO)],
            [("P = 0,944 · R = 0,971 · Top-3 = 1,000 · 752 ms", False, WHITE, FONT_SANS)],
        ],
        size=10.0,
        line_spacing=1.15,
        space_after=2.0,
    )
    tf_h.paragraphs[0].runs[0].font.size = Pt(8.6)
    tf_h.paragraphs[1].runs[0].font.size = Pt(24.0)
    tf_h.paragraphs[2].runs[0].font.size = Pt(9.8)

    # Mini tabla de comparación y ablación
    _add_card(slide, 8.50, 3.08, 4.23, 2.48, fill=SURFACE, border=LINE)
    tbl_shape = slide.shapes.add_table(7, 3, Inches(8.64), Inches(3.18), Inches(3.95), Inches(2.26))
    tbl = tbl_shape.table
    tbl.columns[0].width = Inches(2.15)
    tbl.columns[1].width = Inches(0.85)
    tbl.columns[2].width = Inches(0.95)
    rows_conv = [
        ("Variante Evaluada", "F1", "Top-3"),
        ("Línea base (contenidos)", "0,029", "0,913"),
        ("LSA / SVD (k=32)", "0,429", "0,913"),
        ("Char n-gram (3–5)", "0,455", "0,942"),
        ("Ablación (0 conceptos)", "0,774", "0,986"),
        ("LOPO CV (poda conc.)", "0,925", "1,000"),
        ("LOPO CV (3 pares)", "0,964", "1,000"),
    ]
    for r_idx, row_vals in enumerate(rows_conv):
        for c_idx, val in enumerate(row_vals):
            cell = tbl.cell(r_idx, c_idx)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.fill.solid()
            if r_idx == 0:
                cell.fill.fore_color.rgb = INK
                tcol, is_b = WHITE, True
            elif r_idx >= 5:
                cell.fill.fore_color.rgb = BRAND_SOFT
                tcol, is_b = BRAND_DARK, True
            else:
                cell.fill.fore_color.rgb = SURFACE_2 if r_idx % 2 == 1 else SURFACE
                tcol, is_b = INK, c_idx == 1
            p = cell.text_frame.paragraphs[0]
            _set_paragraph(
                p,
                [(val, is_b, tcol, FONT_MONO if c_idx > 0 and r_idx > 0 else FONT_SANS)],
                size=9.2,
                align=PP_ALIGN.LEFT if c_idx == 0 else PP_ALIGN.CENTER,
                space_after=0,
            )

    _add_card(slide, 8.50, 5.70, 4.23, 1.10, fill=SURFACE, border=LINE, accent_left=CYAN)
    tf_n = _add_textbox(slide, 8.70, 5.78, 3.88, 0.94, valign=MSO_ANCHOR.MIDDLE)
    _add_lines(
        tf_n,
        [
            [("Human-in-the-Loop y Paridad", True, CYAN, FONT_SANS)],
            [
                (
                    "Precedentes aprobados prevalecen (S=1,00). 0 llamadas a LLMs "
                    "externos, sin costo ni alucinaciones.",
                    False,
                    INK_2,
                    FONT_SANS,
                )
            ],
        ],
        size=10.0,
        line_spacing=1.18,
        space_after=2.0,
    )
    tf_n.paragraphs[0].runs[0].font.size = Pt(11.4)

    _set_notes(
        slide,
        "Maximiliano (1:10): Explicar por qué LSA falla (confunde Cálculo I/II), "
        "aporte de Dice-IDF+nivel (0,774) y LOPO podado (0,925).",
    )


def _build_slide_10_uctp(prs: Presentation) -> None:
    slide = _new_blank_slide(prs)
    _add_chrome(
        slide,
        "09 · Optimización Combinatoria UCTP",
        "Cero topes H1=0, auditoría H2/H3 y validación externa en benchmarks ITC-2019",
        10,
        role_tag="Maximiliano · Bloque 3",
    )

    # Dos figuras lado a lado maximizadas
    _add_card(slide, 0.56, 1.26, 6.00, 3.22, fill=SURFACE, border=LINE)
    tf_c1 = _add_textbox(slide, 0.72, 1.32, 5.68, 0.26, valign=MSO_ANCHOR.MIDDLE, margin_lr=0, margin_tb=0)
    _set_paragraph(
        tf_c1.paragraphs[0],
        [("A. SUITE UNAB (256 – 202.500 COMBINACIONES)", True, BRAND, FONT_MONO)],
        size=8.6,
        space_after=0,
    )
    _add_image_fit(slide, IMG_DIR / "fig_benchmark_uctp.png", 0.66, 1.58, 5.80, 2.82, center=True)

    _add_card(slide, 6.76, 1.26, 6.00, 3.22, fill=SURFACE, border=LINE)
    tf_c2 = _add_textbox(slide, 6.92, 1.32, 5.68, 0.26, valign=MSO_ANCHOR.MIDDLE, margin_lr=0, margin_tb=0)
    _set_paragraph(
        tf_c2.paragraphs[0],
        [("B. BENCHMARKS ITC-2019 (80 PERFILES REALES)", True, CYAN, FONT_MONO)],
        size=8.6,
        space_after=0,
    )
    _add_image_fit(slide, IMG_DIR / "fig_benchmark_itc2019.png", 6.86, 1.58, 5.80, 2.82, center=True)

    kpis = [
        (
            "100% H1=0",
            "Factibilidad y Auditoría",
            "Detección exacta H2 (salas) y H3 (docentes) + E2E Playwright (0 errores).",
            BRAND,
        ),
        (
            "-42% a -60%",
            "Reducción f(x) UNAB",
            "B&B poda 98,2% en 202.500 comb. (199,7 ms); ventanas -66,7% a -100%.",
            BRAND,
        ),
        ("-17% a -33%", "Pareado ITC-2019", "Ventanas -25,7% a -44,7%; hasta 24,6× más rápido en yach-fal17.", CYAN),
        (
            "-39,7% a -77,4%",
            "Campus Global (Extensión)",
            "Conflictos estudiantiles (MRV+SA: 89,2%–90,8% clases, H2=0, 0,7–3,9 s).",
            INK,
        ),
    ]
    for idx, (val, lbl, det, col) in enumerate(kpis):
        _add_kpi_card(slide, 0.56 + idx * 3.10, 4.66, 2.92, 2.18, val, lbl, det, accent=col, value_size=21.0)

    _set_notes(
        slide,
        "Maximiliano (1:15): Contrastar B&B exacto vs SA rápido, explicar métricas "
        "ITC-2019 pareadas y extensión táctica campus.",
    )


def _build_slide_11_objetivos_limitaciones(prs: Presentation) -> None:
    slide = _new_blank_slide(prs)
    _add_chrome(
        slide,
        "10 · Cumplimiento, Límites y Futuro",
        "Respuesta trazable OE1–OE7, limitaciones declaradas y hoja de ruta",
        11,
        role_tag="Maximiliano · Bloque 3",
    )

    # Tabla OE1-OE7 a la izquierda
    _add_card(slide, 0.60, 1.32, 6.45, 5.48, fill=SURFACE, border=LINE)
    tf_h = _add_textbox(slide, 0.80, 1.44, 6.05, 0.34, margin_lr=0, margin_tb=0)
    _set_paragraph(
        tf_h.paragraphs[0], [("Cumplimiento de Objetivos Específicos", True, INK, FONT_SANS)], size=14.0, space_after=0
    )

    tbl_shape = slide.shapes.add_table(8, 3, Inches(0.76), Inches(1.86), Inches(6.13), Inches(4.76))
    tbl = tbl_shape.table
    tbl.columns[0].width = Inches(1.55)
    tbl.columns[1].width = Inches(0.95)
    tbl.columns[2].width = Inches(3.63)
    oe_rows = [
        ("Objetivo", "Estado", "Evidencia Verificable"),
        ("OE1 · Auditoría", "Cumplido", "Formatos Banner/Syaproa y 37 mallas estructuradas."),
        ("OE2 · Suite + SSO", "Cumplido", "3 Django + portal + suite-sso HS256 + gateway :8080."),
        ("OE3 · DAG y Estrés", "Cumplido", "0 ciclos en 10 mallas UNAB (16,1 ms) y MallaIQ."),
        ("OE4 · Convalidación", "Cumplido", "F1=0,957, Top-3=1,000, LOPO CV 0,964 (podado 0,925)."),
        ("OE5 · Motor UCTP", "Cumplido", "H1=0, H2/H3, B&B+SA UNAB/ITC-2019 y campus global."),
        ("OE6 · Docker + IaC", "Parcial", "Docker 1-comando y Terraform listos; cuenta AWS pendiente."),
        ("OE7 · Eval. y SUS", "Parcial", "69 tests, benchmarks y OWASP OK; SUS en campo pendiente."),
    ]
    for r_idx, row_vals in enumerate(oe_rows):
        for c_idx, val in enumerate(row_vals):
            cell = tbl.cell(r_idx, c_idx)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.fill.solid()
            if r_idx == 0:
                cell.fill.fore_color.rgb = BRAND
                tcol, is_b = WHITE, True
            elif c_idx == 1 and val == "Cumplido":
                cell.fill.fore_color.rgb = OK_BG
                tcol, is_b = OK, True
            elif c_idx == 1 and val == "Parcial":
                cell.fill.fore_color.rgb = WARN_BG
                tcol, is_b = WARN, True
            else:
                cell.fill.fore_color.rgb = BG if r_idx % 2 == 1 else SURFACE
                tcol, is_b = INK if c_idx == 0 else INK_2, c_idx == 0
            p = cell.text_frame.paragraphs[0]
            _set_paragraph(
                p,
                [(val, is_b, tcol, FONT_SANS)],
                size=9.8,
                align=PP_ALIGN.CENTER if c_idx == 1 else PP_ALIGN.LEFT,
                space_after=0,
            )

    # Tarjeta derecha superior: Limitaciones
    _add_card(slide, 7.26, 1.32, 5.47, 2.74, fill=SURFACE, border=LINE, accent_left=WARN)
    tf_lim = _add_textbox(slide, 7.50, 1.46, 5.05, 2.48)
    _add_lines(
        tf_lim,
        [
            [("Limitaciones Declaradas con Rigor", True, INK, FONT_SANS)],
            [
                ("• AWS staging & SUS de campo: ", True, INK, FONT_SANS),
                (
                    "infraestructura lista sin cuenta activa; SUS diseñado (n ≥ 30) pendiente en terreno.",
                    False,
                    INK_2,
                    FONT_SANS,
                ),
            ],
            [
                ("• Dominio de convalidación: ", True, INK, FONT_SANS),
                ("glosario de 50 conceptos acotado a ciencias básicas e ingeniería.", False, INK_2, FONT_SANS),
            ],
            [
                ("• Frontera UCTP campus vs. ERP: ", True, INK, FONT_SANS),
                (
                    "asistente táctico (89,2%–90,8%); no cubre travel times ni 19 reglas tipo UniTime.",
                    False,
                    INK_2,
                    FONT_SANS,
                ),
            ],
        ],
        size=10.6,
        line_spacing=1.20,
        space_after=5.5,
    )
    tf_lim.paragraphs[0].runs[0].font.size = Pt(13.5)

    # Tarjeta derecha inferior: Trabajo Futuro
    _add_card(slide, 7.26, 4.22, 5.47, 2.58, fill=BRAND_SOFT, border=RGBColor(183, 222, 201), accent_left=BRAND)
    tf_fut = _add_textbox(slide, 7.50, 4.36, 5.05, 2.32)
    _add_lines(
        tf_fut,
        [
            [("Trabajo Futuro Inmediato", True, BRAND_DARK, FONT_SANS)],
            [
                ("1. Piloto AWS + SUS (n ≥ 30): ", True, BRAND_DARK, FONT_SANS),
                ("levantar staging Terraform y ejecutar pruebas cronometradas.", False, INK, FONT_SANS),
            ],
            [
                ("2. Integración Banner / Azure AD: ", True, BRAND_DARK, FONT_SANS),
                ("SAML 2.0/OIDC UNAB y firma asimétrica RS256/JWKS.", False, INK, FONT_SANS),
            ],
            [
                ("3. Zona gris IA + riesgo temprano: ", True, BRAND_DARK, FONT_SANS),
                ("LLM acotado a [0,25; 0,45) y modelos regularizados en 1.er año.", False, INK, FONT_SANS),
            ],
        ],
        size=10.6,
        line_spacing=1.20,
        space_after=5.5,
    )
    tf_fut.paragraphs[0].runs[0].font.size = Pt(13.5)

    _set_notes(
        slide,
        "Maximiliano (0:55): Mostrar honestidad técnica: 5 objetivos cumplidos al 100%, "
        "2 parciales explícitos y ruta clara.",
    )


def _build_slide_12_cierre(prs: Presentation) -> None:
    slide = _new_blank_slide(prs, INK)
    _add_rect(slide, 0.0, 0.0, 13.333, 0.08, BRAND)

    _add_image_fit(slide, ASSETS_DIR / "unab_facultad_ingenieria_blanco.png", 9.65, 0.42, 3.05, 1.05, center=True)
    _add_badge(
        slide,
        "CIERRE Y DEMOSTRACIÓN REPRODUCIBLE",
        0.72,
        0.58,
        3.60,
        0.32,
        fill=DARK_CARD,
        text_color=MINT_DARK,
        border=BRAND,
        size=8.8,
        font_name=FONT_MONO,
    )

    tf_t = _add_textbox(slide, 0.72, 1.50, 11.8, 1.35, margin_lr=0, margin_tb=0)
    _add_lines(
        tf_t,
        [
            [("Muchas gracias · ", True, WHITE, FONT_SANS), ("¿Preguntas de la comisión?", True, MINT_DARK, FONT_SANS)],
            [
                (
                    "SIGA-DSS entrega evidencia algorítmica reproducible para reducir "
                    "el rezago y ordenar la capacidad académica.",
                    False,
                    LIGHT_MUTED,
                    FONT_SANS,
                )
            ],
        ],
        size=15.0,
        line_spacing=1.22,
        space_after=8.0,
    )
    tf_t.paragraphs[0].runs[0].font.size = Pt(34.0)
    tf_t.paragraphs[0].runs[1].font.size = Pt(34.0)

    emblemas = [
        ("0 ciclos", "10 mallas UNAB · TDFI102 c=32"),
        ("F1 = 0,957", "Top-3 = 1,000 · LOPO CV 0,964"),
        ("-60% f(x)", "H1=0 · 80 perfiles ITC-2019"),
        ("69 / 69", "Tests pytest + Ruff 0 errores"),
    ]
    for idx, (val, sub) in enumerate(emblemas):
        cx = 0.72 + idx * 3.04
        _add_rect(
            slide, cx, 3.16, 2.82, 1.56, DARK_CARD, line_color=DARK_LINE, line_pt=1.0, rounded=True, radius_adj=0.05
        )
        _add_rect(slide, cx + 0.14, 3.16, 2.54, 0.05, BRAND_2)
        tf_e = _add_textbox(slide, cx + 0.18, 3.32, 2.46, 1.24, valign=MSO_ANCHOR.MIDDLE)
        _add_lines(
            tf_e,
            [[(val, True, MINT_DARK, FONT_SANS)], [(sub, False, LIGHT_MUTED, FONT_SANS)]],
            size=11.0,
            line_spacing=1.20,
            space_after=4.0,
        )
        tf_e.paragraphs[0].runs[0].font.size = Pt(26.0)

    # Caja comando reproducible
    _add_rect(
        slide,
        0.72,
        5.10,
        11.90,
        0.72,
        RGBColor(20, 48, 39),
        line_color=BRAND,
        line_pt=1.0,
        rounded=True,
        radius_adj=0.08,
    )
    tf_cmd = _add_textbox(slide, 0.96, 5.16, 11.40, 0.60, valign=MSO_ANCHOR.MIDDLE, margin_lr=0, margin_tb=0)
    _set_paragraph(
        tf_cmd.paragraphs[0],
        [
            ("Reproducción local completa:  ", True, MINT_DARK, FONT_SANS),
            ("docker compose up --build   →   http://localhost:8080", True, WHITE, FONT_MONO),
        ],
        size=12.5,
        space_after=0,
    )

    tf_foot = _add_textbox(slide, 0.72, 6.20, 11.90, 0.70, valign=MSO_ANCHOR.MIDDLE, margin_lr=0, margin_tb=0)
    _add_lines(
        tf_foot,
        [
            [("Felipe Riquelme Salvo  ·  José Ignacio Amar  ·  Maximiliano Alonso Vargas", True, WHITE, FONT_SANS)],
            [
                (
                    "Profesor Guía: Jorge Humberto Sabattin Ortega  ·  Ingeniería Civil "
                    "Informática UNAB  ·  Noviembre 2026",
                    False,
                    LIGHT_MUTED,
                    FONT_SANS,
                )
            ],
        ],
        size=10.8,
        line_spacing=1.20,
        space_after=2.0,
    )
    tf_foot.paragraphs[0].runs[0].font.size = Pt(13.0)

    _set_notes(
        slide,
        "Cierre colectivo (0:30): Síntesis de los 4 números emblema, invitación "
        "a preguntas y disponibilidad de demo local.",
    )


def generar_presentacion(output_path: Path = SALIDA_DEFAULT) -> Path:
    """Construye la presentación completa de 12 diapositivas y la guarda en disco."""
    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H

    builders = [
        _build_slide_01_portada,
        _build_slide_02_diagnostico,
        _build_slide_03_ciclo_cerrado,
        _build_slide_04_suite_catalogo,
        _build_slide_05_arquitectura_c4,
        _build_slide_06_seguridad_privacidad,
        _build_slide_07_etl_cicd,
        _build_slide_08_curricular_analytics,
        _build_slide_09_convalidacion,
        _build_slide_10_uctp,
        _build_slide_11_objetivos_limitaciones,
        _build_slide_12_cierre,
    ]
    for builder in builders:
        builder(prs)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(output_path))
    print(f"Presentación generada exitosamente ({len(prs.slides)} slides): {output_path}")
    return output_path


if __name__ == "__main__":
    generar_presentacion()
