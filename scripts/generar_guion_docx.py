"""Compila el guión de apoyo de la defensa a un documento Word limpio y legible."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import docx
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt, RGBColor

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ / "scripts") not in sys.path:
    sys.path.insert(0, str(RAIZ / "scripts"))

import generar_docx_formal as gdf  # noqa: E402

MD_DEFAULT = RAIZ / "docs" / "Guion_Presentacion_SIGA_DSS.md"
DOCX_DEFAULT = RAIZ / "docs" / "Guion_Presentacion_SIGA_DSS.docx"


def build_guion_docx(md_path: Path = MD_DEFAULT, docx_path: Path = DOCX_DEFAULT) -> Path:
    """Genera el documento Word operativo para ensayo y lectura en defensa."""
    doc = docx.Document()

    for style_name in ("Normal", "List Bullet", "List Number"):
        if style_name in doc.styles:
            st = doc.styles[style_name]
            st.font.name = "Segoe UI"
            st.font.color.rgb = gdf.INK

    for section in doc.sections:
        section.top_margin = Inches(0.75)
        section.bottom_margin = Inches(0.75)
        section.left_margin = Inches(0.85)
        section.right_margin = Inches(0.85)
        section.page_width = Inches(8.5)
        section.page_height = Inches(11)

        ftr = section.footer
        p_ftr = ftr.paragraphs[0]
        p_ftr.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        gdf.set_paragraph_border(p_ftr, "top", gdf.HEX_LINE, sz=4, space=4)
        r_ftr = p_ftr.add_run("Guión de Apoyo · Defensa SIGA-DSS · Pág. ")
        r_ftr.font.name = "Segoe UI"
        r_ftr.font.size = Pt(8.5)
        r_ftr.font.color.rgb = gdf.MUTED
        gdf.append_word_field(p_ftr, "PAGE")
        r_sep = p_ftr.add_run(" de ")
        r_sep.font.name = "Segoe UI"
        r_sep.font.size = Pt(8.5)
        r_sep.font.color.rgb = gdf.MUTED
        gdf.append_word_field(p_ftr, "NUMPAGES")

    lines = md_path.read_text(encoding="utf-8").splitlines()
    in_table = False
    table_rows: list[list[str]] = []

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
        gdf.set_table_borders(table)

        gdf.configure_row_pagination(table.rows[0], is_header=True)
        for c_idx, col_name in enumerate(header):
            cell = table.cell(0, c_idx)
            gdf.set_cell_background(cell, gdf.HEX_BRAND)
            gdf.set_cell_margins(cell, top=95, bottom=95, left=105, right=105)
            p = cell.paragraphs[0]
            gdf.add_formatted_runs(
                p,
                col_name.strip(),
                base_bold=True,
                font_size=8.8,
                base_color=RGBColor(255, 255, 255),
            )

        for r_idx, row_data in enumerate(data_rows, start=1):
            gdf.configure_row_pagination(table.rows[r_idx], is_header=False)
            fill_hex = gdf.HEX_BG_ZEBRA if r_idx % 2 == 1 else "FFFFFF"
            for c_idx, val in enumerate(row_data):
                if c_idx < len(table.columns):
                    cell = table.cell(r_idx, c_idx)
                    gdf.set_cell_background(cell, fill_hex)
                    gdf.set_cell_margins(cell, top=75, bottom=75, left=100, right=100)
                    p = cell.paragraphs[0]
                    gdf.add_formatted_runs(p, val.strip(), font_size=8.6)

        sp = doc.add_paragraph()
        sp.paragraph_format.space_after = Pt(4)
        in_table = False
        table_rows = []

    idx = 0
    while idx < len(lines):
        stripped = lines[idx].strip()

        if stripped.startswith("|") and stripped.endswith("|"):
            if set(stripped.replace("|", "").replace("-", "").replace(":", " ")) == {" "}:
                idx += 1
                continue
            if not in_table:
                in_table = True
                table_rows = []
            table_rows.append(gdf.split_markdown_table_row(stripped))
            idx += 1
            continue
        if in_table:
            flush_table()

        if not stripped:
            idx += 1
            continue

        if stripped == "---":
            p_div = doc.add_paragraph()
            p_div.paragraph_format.space_before = Pt(4)
            p_div.paragraph_format.space_after = Pt(6)
            gdf.set_paragraph_border(p_div, "bottom", gdf.HEX_LINE, sz=6, space=1)
            r_div = p_div.add_run(" ")
            r_div.font.size = Pt(2)
            idx += 1
            continue

        if stripped.startswith("> "):
            cue_lines: list[str] = []
            while idx < len(lines):
                cur = lines[idx].strip()
                if cur.startswith("> "):
                    cue_lines.append(cur[2:])
                    idx += 1
                elif cur == ">":
                    cue_lines.append("")
                    idx += 1
                else:
                    break
            box = doc.add_table(rows=1, cols=1)
            box.alignment = WD_TABLE_ALIGNMENT.CENTER
            gdf.set_box_borders(box, left_color=gdf.HEX_BRAND, left_sz=24)
            cell = box.cell(0, 0)
            gdf.set_cell_background(cell, gdf.HEX_BG_ZEBRA)
            gdf.set_cell_margins(cell, top=80, bottom=80, left=150, right=120)
            p = cell.paragraphs[0]
            p.paragraph_format.line_spacing = 1.18
            gdf.add_formatted_runs(p, " ".join(cue_lines).strip(), font_size=9.6, base_color=gdf.BRAND_DARK)
            sp = doc.add_paragraph()
            sp.paragraph_format.space_after = Pt(3)
            continue

        if stripped.startswith("# "):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(6)
            gdf.set_paragraph_border(p, "bottom", gdf.HEX_BRAND, sz=12, space=4)
            gdf.add_formatted_runs(p, stripped[2:], base_bold=True, font_size=17.0, base_color=gdf.INK)
        elif stripped.startswith("## "):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(14)
            p.paragraph_format.space_after = Pt(5)
            p.paragraph_format.keep_with_next = True
            gdf.add_formatted_runs(p, stripped[3:], base_bold=True, font_size=13.5, base_color=gdf.BRAND)
        elif stripped.startswith("### "):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(12)
            p.paragraph_format.space_after = Pt(4)
            p.paragraph_format.keep_with_next = True
            gdf.set_paragraph_border(p, "bottom", gdf.HEX_LINE, sz=4, space=2)
            gdf.add_formatted_runs(p, stripped[4:], base_bold=True, font_size=11.5, base_color=gdf.BRAND_DARK)
        elif stripped.startswith("#### "):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(10)
            p.paragraph_format.space_after = Pt(3)
            p.paragraph_format.keep_with_next = True
            gdf.add_formatted_runs(p, stripped[5:], base_bold=True, font_size=11.0, base_color=gdf.INK)
        elif stripped.startswith(("* ", "- ")):
            p = doc.add_paragraph(style="List Bullet")
            p.paragraph_format.space_after = Pt(3)
            p.paragraph_format.line_spacing = 1.18
            gdf.add_formatted_runs(p, stripped[2:], font_size=10.2)
        elif m_num := re.match(r"^(\d+)\.\s", stripped):
            p = doc.add_paragraph(style="List Number")
            p.paragraph_format.space_after = Pt(3)
            p.paragraph_format.line_spacing = 1.18
            gdf.add_formatted_runs(p, stripped[m_num.end() :], font_size=10.2)
        else:
            p = doc.add_paragraph()
            p.paragraph_format.space_after = Pt(5)
            p.paragraph_format.line_spacing = 1.24
            gdf.add_formatted_runs(p, stripped, font_size=10.5)

        idx += 1

    if in_table:
        flush_table()

    docx_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(docx_path))
    print(f"Guión DOCX generado exitosamente en: {docx_path}")
    return docx_path


if __name__ == "__main__":
    build_guion_docx()
