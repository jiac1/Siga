"""Compila los informes Markdown de SIGA-DSS (Suite UNAB) a Word (.docx) formal."""

from __future__ import annotations

import os
import re

import docx
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.shared import Inches, Pt, RGBColor

NAVY = RGBColor(15, 32, 67)
SLATE = RGBColor(51, 65, 85)
DARK_TEXT = RGBColor(30, 41, 59)
MUTED = RGBColor(100, 116, 139)
CODE_COLOR = RGBColor(180, 40, 40)


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


def set_table_borders(table, color: str = "CBD5E1") -> None:
    """Agrega bordes horizontales y verticales sutiles a una tabla Word."""
    tbl_pr = table._tbl.tblPr
    borders = parse_xml(
        f"<w:tblBorders {nsdecls('w')}>"
        f'<w:top w:val="single" w:sz="6" w:space="0" w:color="0F2043"/>'
        f'<w:bottom w:val="single" w:sz="6" w:space="0" w:color="0F2043"/>'
        f'<w:insideH w:val="single" w:sz="4" w:space="0" w:color="{color}"/>'
        f'<w:left w:val="none"/><w:right w:val="none"/><w:insideV w:val="none"/>'
        f"</w:tblBorders>"
    )
    tbl_pr.append(borders)


def configure_row_pagination(row, is_header: bool = False) -> None:
    """Evita división de filas entre páginas y repite encabezados si aplica."""
    tr_pr = row._tr.get_or_add_trPr()
    tr_pr.append(OxmlElement("w:cantSplit"))
    if is_header:
        tr_pr.append(OxmlElement("w:tblHeader"))


def add_page_number_footer(section, header_text: str) -> None:
    """Configura encabezado sutil y pie con número de página omitiendo portada."""
    section.different_first_page_header_footer = True

    hdr = section.header
    p_hdr = hdr.paragraphs[0]
    p_hdr.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r_hdr = p_hdr.add_run(header_text)
    r_hdr.font.name = "Calibri"
    r_hdr.font.size = Pt(8.5)
    r_hdr.font.color.rgb = MUTED

    ftr = section.footer
    p_ftr = ftr.paragraphs[0]
    p_ftr.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_pre = p_ftr.add_run("Universidad Andrés Bello · Facultad de Ingeniería · Página ")
    r_pre.font.name = "Calibri"
    r_pre.font.size = Pt(8.5)
    r_pre.font.color.rgb = MUTED

    for fld_name, suffix in (("PAGE", " de "), ("NUMPAGES", "")):
        r_fld = p_ftr.add_run()
        r_fld.font.name = "Calibri"
        r_fld.font.size = Pt(8.5)
        r_fld.font.color.rgb = MUTED
        fld_begin = OxmlElement("w:fldChar")
        fld_begin.set(qn("w:fldCharType"), "begin")
        instr = OxmlElement("w:instrText")
        instr.set(qn("xml:space"), "preserve")
        instr.text = f" {fld_name} "
        fld_sep = OxmlElement("w:fldChar")
        fld_sep.set(qn("w:fldCharType"), "separate")
        fld_end = OxmlElement("w:fldChar")
        fld_end.set(qn("w:fldCharType"), "end")
        r_fld._r.extend([fld_begin, instr, fld_sep, fld_end])
        if suffix:
            r_suf = p_ftr.add_run(suffix)
            r_suf.font.name = "Calibri"
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
    base_color: RGBColor = DARK_TEXT,
    font_name: str = "Calibri",
) -> None:
    """Agrega segmentos con negrita, cursiva y código inline a un párrafo Word."""
    clean_text = clean_math_text(text)
    _emit_inline_tokens(paragraph, clean_text, base_bold, base_italic, font_size, base_color, font_name)


def build_docx_from_md(
    md_path: str,
    docx_path: str,
    title_text: str,
    subtitle_text: str,
    integrantes: str | None = None,
    profesor_guia: str | None = None,
    fecha: str | None = None,
    header_text: str = "SIGA-DSS (Suite UNAB) · Informe Final E3 (CINF200)",
) -> None:
    """Genera un documento Word con portada institucional UNAB desde un Markdown."""
    if integrantes is None:
        integrantes = "Felipe Riquelme Salvo, José Ignacio Amar, Maximiliano Alonso Vargas"
    if profesor_guia is None:
        profesor_guia = "Jorge Humberto Sabattin Ortega"
    if fecha is None:
        fecha = "Noviembre de 2026"

    doc = docx.Document()

    for section in doc.sections:
        section.top_margin = Inches(0.95)
        section.bottom_margin = Inches(0.95)
        section.left_margin = Inches(0.95)
        section.right_margin = Inches(0.95)
        section.page_width = Inches(8.5)
        section.page_height = Inches(11)
        add_page_number_footer(section, header_text)

    # ── Portada Ejecutiva UNAB ──
    p_inst = doc.add_paragraph()
    p_inst.paragraph_format.space_before = Pt(24)
    p_inst.paragraph_format.space_after = Pt(4)
    r_inst = p_inst.add_run("UNIVERSIDAD ANDRÉS BELLO")
    r_inst.bold = True
    r_inst.font.name = "Calibri"
    r_inst.font.size = Pt(13)
    r_inst.font.color.rgb = NAVY

    for idx_fac, fac_line in enumerate(
        [
            "FACULTAD DE INGENIERÍA · ESCUELA DE INFORMÁTICA",
            "CARRERA DE INGENIERÍA CIVIL INFORMÁTICA",
        ]
    ):
        p_fac = doc.add_paragraph()
        p_fac.paragraph_format.space_before = Pt(0)
        p_fac.paragraph_format.space_after = Pt(36 if idx_fac == 1 else 2)
        r_fac = p_fac.add_run(fac_line)
        r_fac.font.name = "Calibri"
        r_fac.font.size = Pt(10)
        r_fac.font.color.rgb = MUTED

    p_title = doc.add_paragraph()
    p_title.paragraph_format.space_before = Pt(20)
    p_title.paragraph_format.space_after = Pt(14)
    r_title = p_title.add_run(title_text)
    r_title.bold = True
    r_title.font.name = "Calibri"
    r_title.font.size = Pt(20.5)
    r_title.font.color.rgb = NAVY

    sub_lines = [s.strip() for s in subtitle_text.splitlines() if s.strip()]
    for idx_sub, sub_line in enumerate(sub_lines):
        p_sub = doc.add_paragraph()
        p_sub.paragraph_format.space_before = Pt(0)
        p_sub.paragraph_format.space_after = Pt(48 if idx_sub == len(sub_lines) - 1 else 4)
        r_sub = p_sub.add_run(sub_line)
        r_sub.font.name = "Calibri"
        r_sub.font.size = Pt(12.5)
        r_sub.font.color.rgb = SLATE

    meta_lines = [
        "**Asignatura:** INTEGRADOR II: SEM LIC EN CS (CINF200)",
        f"**Integrantes:** {integrantes}",
        f"**Profesor Guía:** {profesor_guia}",
        f"**Fecha de Entrega:** {fecha}",
        "**Santiago de Chile**",
    ]
    for idx_meta, meta_line in enumerate(meta_lines):
        p_meta = doc.add_paragraph()
        p_meta.paragraph_format.space_before = Pt(72 if idx_meta == 0 else 0)
        p_meta.paragraph_format.space_after = Pt(4)
        p_meta.paragraph_format.line_spacing = 1.25
        add_formatted_runs(p_meta, meta_line, font_size=10.5)

    doc.add_page_break()

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
            set_cell_background(cell, "0F2043")
            set_cell_margins(cell, top=120, bottom=120, left=130, right=130)
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            add_formatted_runs(p, col_name.strip(), base_bold=True, font_size=9.0, base_color=RGBColor(255, 255, 255))

        for r_idx, row_data in enumerate(data_rows, start=1):
            configure_row_pagination(table.rows[r_idx], is_header=False)
            fill_color = "F8FAFC" if r_idx % 2 == 1 else "FFFFFF"
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
        cell = table.cell(0, 0)
        set_cell_background(cell, "F1F5F9")
        set_cell_margins(cell, top=130, bottom=130, left=180, right=180)
        for idx_line, code_line in enumerate(lineas_codigo):
            p = cell.paragraphs[0] if idx_line == 0 else cell.add_paragraph()
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(1.5)
            p.paragraph_format.line_spacing = 1.1
            r = p.add_run(code_line if code_line else " ")
            r.font.name = "Consolas"
            r.font.size = Pt(8.6)
            r.font.color.rgb = DARK_TEXT

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
            cell = table.cell(0, 0)
            set_cell_background(cell, "F8FAFC")
            set_cell_margins(cell, top=110, bottom=110, left=180, right=140)
            p = cell.paragraphs[0]
            p.paragraph_format.line_spacing = 1.25
            add_formatted_runs(
                p, "\n".join(blockquote_lines).strip(), base_italic=True, font_size=10.2, base_color=SLATE
            )
            p_space = doc.add_paragraph()
            p_space.paragraph_format.space_after = Pt(4)
            continue

        if stripped.startswith("# "):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(20)
            p.paragraph_format.space_after = Pt(8)
            p.paragraph_format.keep_with_next = True
            add_formatted_runs(p, stripped[2:], base_bold=True, font_size=16.5, base_color=NAVY)
        elif stripped.startswith("## "):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(16)
            p.paragraph_format.space_after = Pt(6)
            p.paragraph_format.keep_with_next = True
            add_formatted_runs(p, stripped[3:], base_bold=True, font_size=13.5, base_color=NAVY)
        elif stripped.startswith("### "):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(11)
            p.paragraph_format.space_after = Pt(4)
            p.paragraph_format.keep_with_next = True
            add_formatted_runs(p, stripped[4:], base_bold=True, font_size=11.5, base_color=SLATE)
        elif stripped.startswith("#### "):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(8)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.keep_with_next = True
            add_formatted_runs(p, stripped[5:], base_bold=True, font_size=10.5, base_color=NAVY)
        elif stripped.startswith("$$") and stripped.endswith("$$"):
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(6)
            p.paragraph_format.space_after = Pt(6)
            add_formatted_runs(p, stripped, base_italic=True, font_size=10.5, base_color=NAVY, font_name="Cambria")
        elif stripped.startswith(("* ", "- ")):
            p = doc.add_paragraph(style="List Bullet")
            p.paragraph_format.space_after = Pt(3)
            p.paragraph_format.line_spacing = 1.15
            add_formatted_runs(p, stripped[2:], font_size=10.2)
        elif re.match(r"^\d+\.\s", stripped):
            p = doc.add_paragraph(style="List Number")
            p.paragraph_format.space_after = Pt(3)
            p.paragraph_format.line_spacing = 1.15
            text_num = re.sub(r"^\d+\.\s", "", stripped)
            add_formatted_runs(p, text_num, font_size=10.2)
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
        "docs/Memoria_Suite_UNAB_E1_E2_E3_Paper_Final.docx",
        "SIGA-DSS (SUITE UNAB): SISTEMA DE SOPORTE A LA DECISIÓN MODULAR PARA LA "
        "OPTIMIZACIÓN DE TRAYECTORIAS CURRICULARES Y GESTIÓN DE CAPACIDAD ACADÉMICA",
        "INFORME FINAL CONSOLIDADO EN FORMATO PAPER (EVALUACIÓN E3 · E1 + E2 + E3)\n"
        "Formulación, Arquitectura, Optimización UCTP, Evaluación Técnica y Discusión Crítica\n"
        "Caso de Aplicación: Facultad de Ingeniería, Universidad Andrés Bello",
        integrantes=integrantes_oficiales,
        profesor_guia=profesor_guia_oficial,
        fecha=fecha_oficial,
        header_text="SIGA-DSS (Suite UNAB) · Paper Final E3 (CINF200)",
    )
