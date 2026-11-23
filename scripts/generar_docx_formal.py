"""Compila los informes Markdown de SIGA-DSS a Word (.docx) formal."""

from __future__ import annotations

import os
import re
from pathlib import Path

import docx
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.shared import Inches, Pt, RGBColor

RAIZ = Path(__file__).resolve().parents[1]
ASSETS_DIR = RAIZ / "docs" / "img" / "assets"

BRAND = RGBColor(29, 107, 85)
BRAND_DARK = RGBColor(21, 78, 62)
INK = RGBColor(25, 27, 22)
INK_2 = RGBColor(91, 94, 86)
MUTED = RGBColor(142, 145, 137)
CODE_COLOR = RGBColor(199, 60, 46)

HEX_BRAND = "1D6B55"
HEX_BG_ZEBRA = "F6F6F2"
HEX_CALLOUT_BG = "E7F1EC"
HEX_CODE_BG = "F4F4EF"
HEX_LINE = "DEDED7"


def set_cell_background(cell, fill_hex: str) -> None:
    """Aplica color de fondo hexadecimal a una celda de tabla Word."""
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tc_pr.append(shd)


def set_cell_margins(cell, top: int = 110, bottom: int = 110, left: int = 140, right: int = 140) -> None:
    """Configura márgenes internos (dxa) de una celda de tabla Word."""
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_mar = parse_xml(
        f"<w:tcMar {nsdecls('w')}>"
        f'<w:top w:w="{top}" w:type="dxa"/>'
        f'<w:bottom w:w="{bottom}" w:type="dxa"/>'
        f'<w:left w:w="{left}" w:type="dxa"/>'
        f'<w:right w:w="{right}" w:type="dxa"/>'
        f"</w:tcMar>"
    )
    tc_pr.append(tc_mar)


def set_table_borders(
    table,
    top_bottom_color: str = HEX_BRAND,
    inner_color: str = HEX_LINE,
) -> None:
    """Agrega bordes horizontales sutiles con acento de marca a una tabla Word."""
    tbl_pr = table._tbl.tblPr
    for prev in tbl_pr.findall(qn("w:tblBorders")):
        tbl_pr.remove(prev)
    borders = parse_xml(
        f"<w:tblBorders {nsdecls('w')}>"
        f'<w:top w:val="single" w:sz="8" w:space="0" w:color="{top_bottom_color}"/>'
        f'<w:bottom w:val="single" w:sz="8" w:space="0" w:color="{top_bottom_color}"/>'
        f'<w:insideH w:val="single" w:sz="4" w:space="0" w:color="{inner_color}"/>'
        f'<w:left w:val="none"/><w:right w:val="none"/><w:insideV w:val="none"/>'
        f"</w:tblBorders>"
    )
    tbl_pr.append(borders)


def set_box_borders(
    table,
    *,
    left_color: str = "none",
    left_sz: int = 24,
    all_color: str = "none",
    all_sz: int = 4,
) -> None:
    """Configura bordes de una tabla de caja (sin bordes, borde completo o barra izquierda)."""
    tbl_pr = table._tbl.tblPr
    for prev in tbl_pr.findall(qn("w:tblBorders")):
        tbl_pr.remove(prev)
    if left_color != "none" and all_color == "none":
        xml = (
            f"<w:tblBorders {nsdecls('w')}>"
            f'<w:left w:val="single" w:sz="{left_sz}" w:space="0" w:color="{left_color}"/>'
            f'<w:top w:val="none"/><w:right w:val="none"/><w:bottom w:val="none"/>'
            f'<w:insideH w:val="none"/><w:insideV w:val="none"/>'
            f"</w:tblBorders>"
        )
    elif all_color != "none":
        xml = (
            f"<w:tblBorders {nsdecls('w')}>"
            f'<w:top w:val="single" w:sz="{all_sz}" w:space="0" w:color="{all_color}"/>'
            f'<w:bottom w:val="single" w:sz="{all_sz}" w:space="0" w:color="{all_color}"/>'
            f'<w:left w:val="single" w:sz="{all_sz}" w:space="0" w:color="{all_color}"/>'
            f'<w:right w:val="single" w:sz="{all_sz}" w:space="0" w:color="{all_color}"/>'
            f'<w:insideH w:val="none"/><w:insideV w:val="none"/>'
            f"</w:tblBorders>"
        )
    else:
        xml = (
            f"<w:tblBorders {nsdecls('w')}>"
            f'<w:top w:val="none"/><w:bottom w:val="none"/>'
            f'<w:left w:val="none"/><w:right w:val="none"/>'
            f'<w:insideH w:val="none"/><w:insideV w:val="none"/>'
            f"</w:tblBorders>"
        )
    tbl_pr.append(parse_xml(xml))


def set_paragraph_border(paragraph, side: str, color: str, sz: int = 6, space: int = 4) -> None:
    """Agrega un borde fino en un lado del párrafo respetando el orden ECMA-376 de CT_PPr."""
    p_pr = paragraph._p.get_or_add_pPr()
    for prev in p_pr.findall(qn("w:pBdr")):
        p_pr.remove(prev)
    p_bdr = parse_xml(
        f'<w:pBdr {nsdecls("w")}><w:{side} w:val="single" w:sz="{sz}" w:space="{space}" w:color="{color}"/></w:pBdr>'
    )
    has_pstyle = len(p_pr) > 0 and p_pr[0].tag == qn("w:pStyle")
    p_pr.insert(1 if has_pstyle else 0, p_bdr)


def configure_row_pagination(row, is_header: bool = False) -> None:
    """Evita división de filas entre páginas y repite encabezados si aplica."""
    tr_pr = row._tr.get_or_add_trPr()
    tr_pr.append(OxmlElement("w:cantSplit"))
    if is_header:
        tr_pr.append(OxmlElement("w:tblHeader"))


def new_restarted_num_id(doc, style_name: str = "List Number") -> int | None:
    """Crea un nuevo ``numId`` en ``numbering.xml`` reiniciando la numeración en 1."""
    style = doc.styles[style_name]
    p_pr = style._element.find(qn("w:pPr"))
    if p_pr is None:
        return None
    num_pr = p_pr.find(qn("w:numPr"))
    if num_pr is None:
        return None
    num_id_el = num_pr.find(qn("w:numId"))
    if num_id_el is None:
        return None

    base_num_id = num_id_el.get(qn("w:val"))
    numbering = doc.part.numbering_part.numbering_definitions._numbering
    abstract_id = None
    max_id = 0
    for num_el in numbering.findall(qn("w:num")):
        nid = int(num_el.get(qn("w:numId")))
        max_id = max(max_id, nid)
        if str(nid) == str(base_num_id):
            abs_el = num_el.find(qn("w:abstractNumId"))
            if abs_el is not None:
                abstract_id = abs_el.get(qn("w:val"))

    if abstract_id is None:
        return None

    nuevo_id = max_id + 1
    nuevo_num = OxmlElement("w:num")
    nuevo_num.set(qn("w:numId"), str(nuevo_id))

    abs_ref = OxmlElement("w:abstractNumId")
    abs_ref.set(qn("w:val"), str(abstract_id))
    nuevo_num.append(abs_ref)

    lvl_ov = OxmlElement("w:lvlOverride")
    lvl_ov.set(qn("w:ilvl"), "0")
    start_ov = OxmlElement("w:startOverride")
    start_ov.set(qn("w:val"), "1")
    lvl_ov.append(start_ov)
    nuevo_num.append(lvl_ov)

    numbering.append(nuevo_num)
    return nuevo_id


def apply_num_id(paragraph, num_id: int | None) -> None:
    """Asigna un ``numId`` específico a un párrafo de lista numerada."""
    if num_id is None:
        return
    p_pr = paragraph._p.get_or_add_pPr()
    num_pr = p_pr.find(qn("w:numPr"))
    if num_pr is None:
        num_pr = OxmlElement("w:numPr")
        p_pr.append(num_pr)
    num_id_el = num_pr.find(qn("w:numId"))
    if num_id_el is None:
        num_id_el = OxmlElement("w:numId")
        num_pr.append(num_id_el)
    num_id_el.set(qn("w:val"), str(num_id))


def append_word_field(
    paragraph,
    field_name: str,
    *,
    font_name: str = "Segoe UI",
    font_size: float = 8.5,
    color: RGBColor = MUTED,
) -> None:
    """Inserta un campo dinámico de Word (por ejemplo PAGE o NUMPAGES)."""
    r_fld = paragraph.add_run()
    r_fld.font.name = font_name
    r_fld.font.size = Pt(font_size)
    r_fld.font.color.rgb = color
    fld_begin = OxmlElement("w:fldChar")
    fld_begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = f" {field_name} "
    fld_sep = OxmlElement("w:fldChar")
    fld_sep.set(qn("w:fldCharType"), "separate")
    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")
    r_fld._r.extend([fld_begin, instr, fld_sep, fld_end])


def add_page_number_footer(section, header_text: str) -> None:
    """Configura encabezado sutil y pie con número de página omitiendo portada."""
    section.different_first_page_header_footer = True

    hdr = section.header
    p_hdr = hdr.paragraphs[0]
    p_hdr.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    set_paragraph_border(p_hdr, "bottom", HEX_LINE, sz=4, space=4)
    r_hdr = p_hdr.add_run(header_text)
    r_hdr.font.name = "Segoe UI"
    r_hdr.font.size = Pt(8.5)
    r_hdr.font.color.rgb = MUTED

    ftr = section.footer
    p_ftr = ftr.paragraphs[0]
    p_ftr.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_paragraph_border(p_ftr, "top", HEX_LINE, sz=4, space=4)
    r_pre = p_ftr.add_run("Universidad Andrés Bello · Facultad de Ingeniería · Página ")
    r_pre.font.name = "Segoe UI"
    r_pre.font.size = Pt(8.5)
    r_pre.font.color.rgb = MUTED

    for fld_name, suffix in (("PAGE", " de "), ("NUMPAGES", "")):
        append_word_field(p_ftr, fld_name)
        if suffix:
            r_suf = p_ftr.add_run(suffix)
            r_suf.font.name = "Segoe UI"
            r_suf.font.size = Pt(8.5)
            r_suf.font.color.rgb = MUTED


def clean_math_text(text: str) -> str:
    """Convierte notación LaTeX / KaTeX a caracteres Unicode legibles en Word."""
    t = text.replace(r"\$", "__DOLLAR_SIGN__")

    # Casos piecewise \begin{cases} ... \end{cases}
    t = re.sub(
        r"\\begin\{cases\}(.*?)\\end\{cases\}",
        lambda m: "[ " + m.group(1).replace(r"\\", " ; ").replace("&", " ") + " ]",
        t,
        flags=re.DOTALL,
    )

    # Comandos de formato primero para permitir \frac con \text{} anidado
    t = re.sub(r"\\(?:text|mathbf|mathit|mathrm|vec)\{([^}]+)\}", r"\1", t)

    # Fracciones simples \frac{a}{b} -> (a) / (b)
    t = re.sub(r"\\frac\{([^{}]+)\}\{([^{}]+)\}", r"(\1) / (\2)", t)

    # Escapes comunes
    reemplazos = [
        (r"\%", "%"),
        (r"\{", "{"),
        (r"\}", "}"),
        (r"\|", "|"),
        (r"\ ", " "),
        (r"\bigl(", "("),
        (r"\bigr)", ")"),
        (r"\left(", "("),
        (r"\right)", ")"),
        (r"\leftrightarrow", "↔"),
        (r"\rightarrow", "→"),
        (r"\to", "→"),
        (r"\rightsquigarrow", "⇝"),
        (r"\ge", "≥"),
        (r"\le", "≤"),
        (r"\neq", "≠"),
        (r"\approx", "≈"),
        (r"\sim", "≈"),
        (r"\times", "×"),
        (r"\cdot", "·"),
        (r"\sum", "Σ"),
        (r"\cap", "∩"),
        (r"\cup", "∪"),
        (r"\emptyset", "∅"),
        (r"\exists", "∃"),
        (r"\forall", "∀"),
        (r"\mid", "|"),
        (r"\in", "∈"),
        (r"\alpha", "α"),
        (r"\beta", "β"),
        (r"\gamma", "γ"),
        (r"\tau", "τ"),
        (r"\lambda", "λ"),
        (r"\Delta", "Δ"),
        (r"\mu", "μ"),
        (r"\cos", "cos"),
        (r"\max", "max"),
        (r"\min", "min"),
        (r"\exp", "exp"),
        (r"\mathcal{O}", "O"),
        (r"\mathcal{C}", "C"),
        (r"\mathcal{NP}", "NP"),
    ]
    for src, dst in reemplazos:
        t = t.replace(src, dst)

    t = re.sub(r"\\(quad|qquad|enspace|;|,|!)", " ", t)
    t = re.sub(r"\\(?:text|mathbf|mathit|mathrm|vec)\{([^}]+)\}", r"\1", t)
    t = re.sub(r"_\{([^}]+)\}", r"_\1", t)
    t = re.sub(r"\^\{([^}]+)\}", r"^\1", t)

    t = t.replace("$$", "").replace(r"\(", "").replace(r"\)", "")
    t = re.sub(r"(?<!\\)\$(.*?)\$", r"\1", t)
    t = t.replace("$", "")
    t = t.replace("__DOLLAR_SIGN__", "$")
    return re.sub(r" {2,}", " ", t)


def split_markdown_table_row(line: str) -> list[str]:
    """Divide una fila de tabla Markdown respetando pipes escapados (``\\|``)."""
    protegida = line.replace(r"\|", "__ESC_PIPE__")
    partes = protegida.split("|")[1:-1]
    return [c.replace("__ESC_PIPE__", "|") for c in partes]


_RE_INLINE = re.compile(r"(\*\*\*.*?\*\*\*|\*\*.*?\*\*|\*[^*\n]+?\*|`[^`\n]+?`)")


def _emit_run(
    paragraph,
    text: str,
    bold: bool,
    italic: bool,
    font_size: float,
    color: RGBColor,
    font_name: str,
) -> None:
    """Agrega un segmento de texto plano manejando posibles saltos de línea."""
    partes = text.split("\n")
    for idx, parte in enumerate(partes):
        if parte:
            run = paragraph.add_run(parte)
            run.bold = bold
            run.italic = italic
            run.font.name = font_name
            run.font.size = Pt(font_size)
            run.font.color.rgb = color
        if idx < len(partes) - 1:
            paragraph.add_run().add_break()


def _emit_inline_tokens(
    paragraph,
    text: str,
    bold: bool,
    italic: bool,
    font_size: float,
    base_color: RGBColor,
    font_name: str,
) -> None:
    """Parsea recursivamente negrita, cursiva y código inline sin dejar asteriscos literales."""
    for token in _RE_INLINE.split(text):
        if not token:
            continue
        if token.startswith("***") and token.endswith("***") and len(token) > 6:
            _emit_inline_tokens(paragraph, token[3:-3], True, True, font_size, base_color, font_name)
        elif token.startswith("**") and token.endswith("**") and len(token) > 4:
            _emit_inline_tokens(paragraph, token[2:-2], True, italic, font_size, base_color, font_name)
        elif token.startswith("*") and token.endswith("*") and len(token) > 2:
            _emit_inline_tokens(paragraph, token[1:-1], bold, True, font_size, base_color, font_name)
        elif token.startswith("`") and token.endswith("`") and len(token) > 2:
            _emit_run(paragraph, token[1:-1], bold, italic, font_size - 1, CODE_COLOR, "Consolas")
        else:
            _emit_run(paragraph, token, bold, italic, font_size, base_color, font_name)


def add_formatted_runs(
    paragraph,
    text: str,
    base_bold: bool = False,
    base_italic: bool = False,
    font_size: float = 10.5,
    base_color: RGBColor = INK,
    font_name: str = "Segoe UI",
) -> None:
    """Agrega segmentos con negrita, cursiva y código inline a un párrafo Word."""
    clean_text = clean_math_text(text)
    _emit_inline_tokens(paragraph, clean_text, base_bold, base_italic, font_size, base_color, font_name)


def _add_cover_page(
    doc: docx.Document,
    title_text: str,
    subtitle_text: str,
    integrantes: str,
    profesor_guia: str,
    fecha: str,
) -> None:
    """Construye la portada editorial SIGA con escudo oficial UNAB."""
    header_tbl = doc.add_table(rows=1, cols=2)
    header_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    header_tbl.autofit = False
    set_box_borders(header_tbl)

    col_widths = (Inches(0.92), Inches(5.68))
    for cell, width in zip(header_tbl.rows[0].cells, col_widths, strict=True):
        cell.width = width
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER

    cell_logo, cell_text = header_tbl.rows[0].cells
    set_cell_margins(cell_logo, top=40, bottom=40, left=0, right=120)
    set_cell_margins(cell_text, top=40, bottom=40, left=80, right=0)

    shield_path = ASSETS_DIR / "unab_escudo_color.png"
    p_logo = cell_logo.paragraphs[0]
    p_logo.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p_logo.paragraph_format.space_before = Pt(0)
    p_logo.paragraph_format.space_after = Pt(0)
    if shield_path.exists():
        p_logo.add_run().add_picture(str(shield_path), width=Inches(0.72))

    inst_lines = [
        ("UNIVERSIDAD ANDRÉS BELLO", True, 13.0, INK),
        ("Facultad de Ingeniería · Escuela de Informática", False, 10.0, INK_2),
        ("Carrera de Ingeniería Civil Informática", True, 10.0, BRAND),
    ]
    for idx_inst, (txt, is_bold, fsize, color) in enumerate(inst_lines):
        p_line = cell_text.paragraphs[0] if idx_inst == 0 else cell_text.add_paragraph()
        p_line.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p_line.paragraph_format.space_before = Pt(0)
        p_line.paragraph_format.space_after = Pt(2)
        run = p_line.add_run(txt)
        run.bold = is_bold
        run.font.name = "Segoe UI"
        run.font.size = Pt(fsize)
        run.font.color.rgb = color

    p_rule = doc.add_paragraph()
    p_rule.paragraph_format.space_before = Pt(6)
    p_rule.paragraph_format.space_after = Pt(28)
    set_paragraph_border(p_rule, "bottom", HEX_BRAND, sz=16, space=1)
    r_rule = p_rule.add_run(" ")
    r_rule.font.size = Pt(2)

    p_eye = doc.add_paragraph()
    p_eye.paragraph_format.space_before = Pt(14)
    p_eye.paragraph_format.space_after = Pt(8)
    r_eye = p_eye.add_run("PROYECTO DE TÍTULO · EVALUACIÓN FINAL E3 (INTEGRACIÓN E1 + E2 + E3)")
    r_eye.bold = True
    r_eye.font.name = "Segoe UI"
    r_eye.font.size = Pt(9.5)
    r_eye.font.color.rgb = BRAND

    p_title = doc.add_paragraph()
    p_title.paragraph_format.space_before = Pt(4)
    p_title.paragraph_format.space_after = Pt(14)
    p_title.paragraph_format.line_spacing = 1.15
    r_title = p_title.add_run(title_text)
    r_title.bold = True
    r_title.font.name = "Segoe UI"
    r_title.font.size = Pt(20.0)
    r_title.font.color.rgb = INK

    sub_lines = [s.strip() for s in subtitle_text.splitlines() if s.strip()]
    for idx_sub, sub_line in enumerate(sub_lines):
        p_sub = doc.add_paragraph()
        p_sub.paragraph_format.space_before = Pt(0)
        p_sub.paragraph_format.space_after = Pt(36 if idx_sub == len(sub_lines) - 1 else 4)
        p_sub.paragraph_format.line_spacing = 1.25
        r_sub = p_sub.add_run(sub_line)
        r_sub.font.name = "Segoe UI"
        r_sub.font.size = Pt(11.5)
        r_sub.font.color.rgb = INK_2

    meta_tbl = doc.add_table(rows=1, cols=1)
    meta_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    meta_tbl.autofit = False
    set_box_borders(meta_tbl, left_color=HEX_BRAND, left_sz=24)
    meta_cell = meta_tbl.cell(0, 0)
    meta_cell.width = Inches(6.6)
    set_cell_background(meta_cell, HEX_BG_ZEBRA)
    set_cell_margins(meta_cell, top=160, bottom=160, left=220, right=180)

    meta_lines = [
        "**Asignatura:** INTEGRADOR II: SEM LIC EN CS (CINF200)",
        f"**Integrantes:** {integrantes}",
        f"**Profesor Guía:** {profesor_guia}",
        "**Sede:** Santiago de Chile",
        f"**Fecha de Entrega:** {fecha}",
    ]
    for idx_meta, meta_line in enumerate(meta_lines):
        p_meta = meta_cell.paragraphs[0] if idx_meta == 0 else meta_cell.add_paragraph()
        p_meta.paragraph_format.space_before = Pt(0)
        p_meta.paragraph_format.space_after = Pt(0 if idx_meta == len(meta_lines) - 1 else 4)
        p_meta.paragraph_format.line_spacing = 1.25
        add_formatted_runs(p_meta, meta_line, font_size=10.2, base_color=INK)

    doc.add_page_break()


def build_docx_from_md(
    md_path: str,
    docx_path: str,
    title_text: str,
    subtitle_text: str,
    integrantes: str | None = None,
    profesor_guia: str | None = None,
    fecha: str | None = None,
    header_text: str = "SIGA-DSS · Informe Final E3 (CINF200)",
) -> None:
    """Genera un documento Word con portada editorial SIGA y escudo oficial UNAB."""
    if integrantes is None:
        integrantes = "Felipe Riquelme Salvo, José Ignacio Amar, Maximiliano Alonso Vargas"
    if profesor_guia is None:
        profesor_guia = "Jorge Humberto Sabattin Ortega"
    if fecha is None:
        fecha = "Noviembre de 2026"

    doc = docx.Document()

    for style_name in ("Normal", "List Bullet", "List Number"):
        if style_name in doc.styles:
            st = doc.styles[style_name]
            st.font.name = "Segoe UI"
            st.font.color.rgb = INK

    for section in doc.sections:
        section.top_margin = Inches(0.95)
        section.bottom_margin = Inches(0.95)
        section.left_margin = Inches(0.95)
        section.right_margin = Inches(0.95)
        section.page_width = Inches(8.5)
        section.page_height = Inches(11)
        add_page_number_footer(section, header_text)

    _add_cover_page(doc, title_text, subtitle_text, integrantes, profesor_guia, fecha)

    with open(md_path, encoding="utf-8") as f:
        lines = f.readlines()

    start_idx = 0
    for i, line in enumerate(lines):
        line_s = line.strip()
        if line_s.startswith(("## Resumen", "# PARTE", "# 1.", "## 1.")):
            start_idx = i
            break
    lines = lines[start_idx:]

    in_code_block = False
    code_lines: list[str] = []
    in_table = False
    table_rows: list[list[str]] = []
    fig_counter = 0
    active_list_num_id: int | None = None

    def flush_table() -> None:
        nonlocal in_table, table_rows
        if not table_rows:
            in_table = False
            return

        header = table_rows[0]
        data_rows = table_rows[1:]
        table = doc.add_table(rows=len(table_rows), cols=len(header))
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.autofit = True
        set_table_borders(table)

        configure_row_pagination(table.rows[0], is_header=True)
        for c_idx, col_name in enumerate(header):
            cell = table.cell(0, c_idx)
            set_cell_background(cell, HEX_BRAND)
            set_cell_margins(cell, top=120, bottom=120, left=130, right=130)
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            add_formatted_runs(p, col_name.strip(), base_bold=True, font_size=9.0, base_color=RGBColor(255, 255, 255))

        for r_idx, row_data in enumerate(data_rows, start=1):
            configure_row_pagination(table.rows[r_idx], is_header=False)
            fill_color = HEX_BG_ZEBRA if r_idx % 2 == 1 else "FFFFFF"
            for c_idx, val in enumerate(row_data):
                if c_idx < len(table.columns):
                    cell = table.cell(r_idx, c_idx)
                    set_cell_background(cell, fill_color)
                    set_cell_margins(cell, top=90, bottom=90, left=120, right=120)
                    p = cell.paragraphs[0]
                    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                    add_formatted_runs(p, val.strip(), font_size=8.8)

        p_space = doc.add_paragraph()
        p_space.paragraph_format.space_after = Pt(4)
        in_table = False
        table_rows = []

    def flush_code() -> None:
        nonlocal in_code_block, code_lines
        if not code_lines:
            in_code_block = False
            return

        lineas_codigo = "".join(code_lines).rstrip().splitlines()
        table = doc.add_table(rows=1, cols=1)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        set_box_borders(table, all_color=HEX_LINE, all_sz=4)
        cell = table.cell(0, 0)
        set_cell_background(cell, HEX_CODE_BG)
        set_cell_margins(cell, top=130, bottom=130, left=180, right=180)
        for idx_line, code_line in enumerate(lineas_codigo):
            p = cell.paragraphs[0] if idx_line == 0 else cell.add_paragraph()
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(1.5)
            p.paragraph_format.line_spacing = 1.1
            r = p.add_run(code_line if code_line else " ")
            r.font.name = "Consolas"
            r.font.size = Pt(8.5)
            r.font.color.rgb = INK

        p_space = doc.add_paragraph()
        p_space.paragraph_format.space_after = Pt(4)
        in_code_block = False
        code_lines = []

    idx = 0
    while idx < len(lines):
        line = lines[idx]
        stripped = line.strip()

        if stripped.startswith("```"):
            if in_code_block:
                flush_code()
            else:
                if in_table:
                    flush_table()
                in_code_block = True
                code_lines = []
            idx += 1
            continue

        if in_code_block:
            code_lines.append(line)
            idx += 1
            continue

        if stripped.startswith("|") and stripped.endswith("|"):
            if set(stripped.replace("|", "").replace("-", "").replace(":", " ")) == {" "}:
                idx += 1
                continue
            cols = split_markdown_table_row(stripped)
            if not in_table:
                in_table = True
                table_rows = []
            table_rows.append(cols)
            idx += 1
            continue
        if in_table:
            flush_table()

        if not stripped or stripped == "---":
            if stripped == "---":
                active_list_num_id = None
            idx += 1
            continue

        img_match = re.match(r"^!\[(.*?)\]\((.*?)\)$", stripped)
        if img_match:
            caption_text = img_match.group(1).strip()
            img_rel_path = img_match.group(2).strip()

            if os.path.exists(img_rel_path):
                img_full_path = img_rel_path
            elif os.path.exists(os.path.join(os.path.dirname(md_path), img_rel_path)):
                img_full_path = os.path.join(os.path.dirname(md_path), img_rel_path)
            elif os.path.exists(os.path.join("docs", img_rel_path)):
                img_full_path = os.path.join("docs", img_rel_path)
            else:
                img_full_path = None

            if img_full_path:
                fig_counter += 1
                p_img = doc.add_paragraph()
                p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p_img.paragraph_format.space_before = Pt(12)
                p_img.paragraph_format.space_after = Pt(4)
                p_img.paragraph_format.keep_with_next = True
                run_img = p_img.add_run()
                run_img.add_picture(img_full_path, width=Inches(6.2))

                p_cap = doc.add_paragraph()
                p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p_cap.paragraph_format.space_after = Pt(12)
                add_formatted_runs(
                    p_cap,
                    f"**Figura {fig_counter}:** {caption_text}",
                    font_size=9.2,
                    base_italic=True,
                    base_color=MUTED,
                )
                idx += 1
                continue

        if stripped.startswith("> "):
            blockquote_lines: list[str] = []
            while idx < len(lines):
                cur = lines[idx].strip()
                if cur.startswith("> "):
                    blockquote_lines.append(cur[2:])
                    idx += 1
                elif cur == ">":
                    blockquote_lines.append("")
                    idx += 1
                elif not cur and idx + 1 < len(lines) and lines[idx + 1].strip().startswith("> "):
                    blockquote_lines.append("")
                    idx += 1
                else:
                    break

            table = doc.add_table(rows=1, cols=1)
            table.alignment = WD_TABLE_ALIGNMENT.CENTER
            set_box_borders(table, left_color=HEX_BRAND, left_sz=24)
            cell = table.cell(0, 0)
            set_cell_background(cell, HEX_CALLOUT_BG)
            set_cell_margins(cell, top=110, bottom=110, left=180, right=140)
            p = cell.paragraphs[0]
            p.paragraph_format.line_spacing = 1.25
            add_formatted_runs(
                p, "\n".join(blockquote_lines).strip(), base_italic=True, font_size=10.2, base_color=BRAND_DARK
            )
            p_space = doc.add_paragraph()
            p_space.paragraph_format.space_after = Pt(4)
            continue

        if stripped.startswith("# "):
            active_list_num_id = None
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(20)
            p.paragraph_format.space_after = Pt(8)
            p.paragraph_format.keep_with_next = True
            add_formatted_runs(p, stripped[2:], base_bold=True, font_size=16.5, base_color=BRAND)
        elif stripped.startswith("## "):
            active_list_num_id = None
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(16)
            p.paragraph_format.space_after = Pt(6)
            p.paragraph_format.keep_with_next = True
            add_formatted_runs(p, stripped[3:], base_bold=True, font_size=13.5, base_color=BRAND)
        elif stripped.startswith("### "):
            active_list_num_id = None
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(11)
            p.paragraph_format.space_after = Pt(4)
            p.paragraph_format.keep_with_next = True
            add_formatted_runs(p, stripped[4:], base_bold=True, font_size=11.5, base_color=INK)
        elif stripped.startswith("#### "):
            active_list_num_id = None
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(8)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.keep_with_next = True
            add_formatted_runs(p, stripped[5:], base_bold=True, font_size=10.5, base_color=BRAND_DARK)
        elif stripped.startswith("$$") and stripped.endswith("$$"):
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(6)
            p.paragraph_format.space_after = Pt(6)
            add_formatted_runs(
                p, stripped, base_italic=True, font_size=10.5, base_color=BRAND_DARK, font_name="Cambria"
            )
        elif stripped.startswith(("* ", "- ")):
            p = doc.add_paragraph(style="List Bullet")
            p.paragraph_format.space_after = Pt(3)
            p.paragraph_format.line_spacing = 1.15
            add_formatted_runs(p, stripped[2:], font_size=10.2)
        elif m_num := re.match(r"^(\d+)\.\s", stripped):
            if int(m_num.group(1)) == 1 or active_list_num_id is None:
                active_list_num_id = new_restarted_num_id(doc, "List Number")
            p = doc.add_paragraph(style="List Number")
            apply_num_id(p, active_list_num_id)
            p.paragraph_format.space_after = Pt(3)
            p.paragraph_format.line_spacing = 1.15
            text_num = stripped[m_num.end() :]
            add_formatted_runs(p, text_num, font_size=10.2)
        elif re.match(r"^\*\*Tabla\s+\d+:\*\*", stripped):
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_before = Pt(8)
            p.paragraph_format.space_after = Pt(3)
            p.paragraph_format.keep_with_next = True
            add_formatted_runs(p, stripped, font_size=9.2, base_color=BRAND)
        elif re.match(r"^\*\*Nota:\*\*", stripped):
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(8)
            add_formatted_runs(p, stripped, font_size=8.6, base_italic=True, base_color=MUTED)
        else:
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            p.paragraph_format.space_after = Pt(5.5)
            p.paragraph_format.line_spacing = 1.18
            add_formatted_runs(p, stripped, font_size=10.2)

        idx += 1

    if in_table:
        flush_table()
    if in_code_block:
        flush_code()

    doc.save(docx_path)
    print(f"Documento generado exitosamente en: {docx_path}")


if __name__ == "__main__":
    integrantes_oficiales = "Felipe Riquelme Salvo, José Ignacio Amar, Maximiliano Alonso Vargas"
    profesor_guia_oficial = "Jorge Humberto Sabattin Ortega"
    fecha_oficial = "Noviembre de 2026"

    build_docx_from_md(
        "docs/Memoria_Suite_UNAB_E1_E2_E3_Paper_Final.md",
        "docs/Memoria_Siga_DSS_E1_E2_E3_Paper_Final.docx",
        "SIGA-DSS: SISTEMA DE SOPORTE A LA DECISIÓN MODULAR PARA LA "
        "OPTIMIZACIÓN DE TRAYECTORIAS CURRICULARES Y GESTIÓN DE CAPACIDAD ACADÉMICA",
        "INFORME FINAL CONSOLIDADO EN FORMATO PAPER (EVALUACIÓN E3 · E1 + E2 + E3)\n"
        "Formulación, Arquitectura, Optimización UCTP, Evaluación Técnica y Discusión Crítica\n"
        "Caso de Aplicación: Facultad de Ingeniería, Universidad Andrés Bello",
        integrantes=integrantes_oficiales,
        profesor_guia=profesor_guia_oficial,
        fecha=fecha_oficial,
        header_text="SIGA-DSS · Paper Final E3 (CINF200)",
    )
