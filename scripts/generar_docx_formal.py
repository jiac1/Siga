import os
import re
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import qn, nsdecls

# Colores de la paleta ejecutiva UNAB
NAVY = RGBColor(15, 32, 67)       # #0F2043 (Encabezados 1)
SLATE = RGBColor(51, 65, 85)      # #334155 (Encabezados 2)
DARK_TEXT = RGBColor(30, 41, 59)  # #1E293B (Cuerpo)
MUTED = RGBColor(100, 116, 139)   # #64748B (Metadatos)
CODE_COLOR = RGBColor(180, 40, 40)

def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=120, bottom=120, left=160, right=160):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(f'''
        <w:tcMar {nsdecls("w")}>
            <w:top w:w="{top}" w:type="dxa"/>
            <w:bottom w:w="{bottom}" w:type="dxa"/>
            <w:left w:w="{left}" w:type="dxa"/>
            <w:right w:w="{right}" w:type="dxa"/>
        </w:tcMar>
    ''')
    tcPr.append(tcMar)

def add_formatted_runs(paragraph, text, base_bold=False, base_italic=False, font_size=11, base_color=DARK_TEXT, font_name="Calibri"):
    # Limpiar sintaxis KaTeX si viene como inline math \( ... \) o $ ... $
    clean_text = text.replace(r'\(', '').replace(r'\)', '')
    # Reemplazar math común para lectura limpia en Word
    clean_text = clean_text.replace(r'\text{Precisión}', 'Precisión')
    clean_text = clean_text.replace(r'\text{Exhaustividad}', 'Exhaustividad')
    clean_text = clean_text.replace(r'\mathbf{F_1 = 0,957}', 'F1 = 0,957')
    clean_text = clean_text.replace(r'\text{Top-3}', 'Top-3')
    clean_text = clean_text.replace(r'\mathcal{O}', 'O')
    clean_text = clean_text.replace(r'\cdot', '·')
    clean_text = clean_text.replace(r'\alpha', 'α').replace(r'\beta', 'β').replace(r'\gamma', 'γ')
    clean_text = clean_text.replace(r'\tau', 'τ')
    clean_text = clean_text.replace(r'\le', '≤').replace(r'\ge', '≥')
    
    tokens = re.split(r'(\*\*.*?\*\*|\*.*?\*|`.*?`)', clean_text)
    for token in tokens:
        if not token:
            continue
        if token.startswith('**') and token.endswith('**'):
            run = paragraph.add_run(token[2:-2])
            run.bold = True
            run.italic = base_italic
            run.font.name = font_name
            run.font.size = Pt(font_size)
            run.font.color.rgb = base_color
        elif token.startswith('*') and token.endswith('*'):
            run = paragraph.add_run(token[1:-1])
            run.bold = base_bold
            run.italic = True
            run.font.name = font_name
            run.font.size = Pt(font_size)
            run.font.color.rgb = base_color
        elif token.startswith('`') and token.endswith('`'):
            run = paragraph.add_run(token[1:-1])
            run.font.name = "Consolas"
            run.font.size = Pt(font_size - 1)
            run.font.color.rgb = CODE_COLOR
        else:
            run = paragraph.add_run(token)
            run.bold = base_bold
            run.italic = base_italic
            run.font.name = font_name
            run.font.size = Pt(font_size)
            run.font.color.rgb = base_color

def build_docx_from_md(md_path, docx_path, title_text, subtitle_text):
    doc = docx.Document()
    
    # Configurar márgenes de 1 pulgada (estándar APA / UNAB)
    for s in doc.sections:
        s.top_margin = Inches(1)
        s.bottom_margin = Inches(1)
        s.left_margin = Inches(1)
        s.right_margin = Inches(1)
        s.page_width = Inches(8.5)
        s.page_height = Inches(11)
        
    # ── PORTADA EJECUTIVA UNAB ──
    p_inst = doc.add_paragraph()
    p_inst.paragraph_format.space_before = Pt(24)
    p_inst.paragraph_format.space_after = Pt(4)
    r_inst = p_inst.add_run("UNIVERSIDAD ANDRÉS BELLO")
    r_inst.bold = True
    r_inst.font.size = Pt(13)
    r_inst.font.color.rgb = NAVY
    
    p_fac = doc.add_paragraph()
    p_fac.paragraph_format.space_after = Pt(48)
    r_fac = p_fac.add_run("FACULTAD DE INGENIERÍA · ESCUELA DE TECNOLOGÍAS DE LA INFORMACIÓN\nCARRERA DE INGENIERÍA CIVIL INFORMÁTICA")
    r_fac.font.size = Pt(10)
    r_fac.font.color.rgb = MUTED
    
    p_title = doc.add_paragraph()
    p_title.paragraph_format.space_before = Pt(36)
    p_title.paragraph_format.space_after = Pt(12)
    r_title = p_title.add_run(title_text)
    r_title.bold = True
    r_title.font.size = Pt(22)
    r_title.font.color.rgb = NAVY
    
    p_sub = doc.add_paragraph()
    p_sub.paragraph_format.space_after = Pt(72)
    r_sub = p_sub.add_run(subtitle_text)
    r_sub.font.size = Pt(13)
    r_sub.font.color.rgb = SLATE
    
    p_meta = doc.add_paragraph()
    p_meta.paragraph_format.space_before = Pt(96)
    p_meta.paragraph_format.space_after = Pt(4)
    p_meta.paragraph_format.line_spacing = 1.3
    add_formatted_runs(p_meta, "**Asignatura:** INTEGRADOR II: SEM LIC EN CS (CINF200)\n**Integrantes:** Felipe S. Riquelme Salvo, José Ignacio Amar\n**Profesor Guía:** Escuela de Ingeniería UNAB\n**Fecha de Entrega:** Octubre de 2026\n**Santiago de Chile**", font_size=10.5)
    
    doc.add_page_break()
    
    # ── CUERPO DEL INFORME ──
    with open(md_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    in_code_block = False
    code_lines = []
    in_table = False
    table_rows = []
    
    def flush_table():
        nonlocal in_table, table_rows
        if not table_rows:
            in_table = False
            return
            
        header = table_rows[0]
        data_rows = table_rows[1:]
        
        table = doc.add_table(rows=len(table_rows), cols=len(header))
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.autofit = True
        
        # Estilizar Header
        for c_idx, col_name in enumerate(header):
            cell = table.cell(0, c_idx)
            set_cell_background(cell, "0F2043") # Navy
            set_cell_margins(cell, top=140, bottom=140, left=160, right=160)
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            add_formatted_runs(p, col_name.strip(), base_bold=True, font_size=10, base_color=RGBColor(255, 255, 255))
            
        # Estilizar Filas de Datos
        for r_idx, row_data in enumerate(data_rows, start=1):
            fill_color = "F8FAFC" if r_idx % 2 == 1 else "FFFFFF"
            for c_idx, val in enumerate(row_data):
                if c_idx < len(table.columns):
                    cell = table.cell(r_idx, c_idx)
                    set_cell_background(cell, fill_color)
                    set_cell_margins(cell, top=100, bottom=100, left=150, right=150)
                    p = cell.paragraphs[0]
                    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                    add_formatted_runs(p, val.strip(), font_size=9.5)
                    
        p_space = doc.add_paragraph()
        p_space.paragraph_format.space_after = Pt(6)
        in_table = False
        table_rows = []

    def flush_code():
        nonlocal in_code_block, code_lines
        if not code_lines:
            in_code_block = False
            return
            
        code_text = "".join(code_lines)
        table = doc.add_table(rows=1, cols=1)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        cell = table.cell(0, 0)
        set_cell_background(cell, "F1F5F9") # Slate muy claro
        set_cell_margins(cell, top=140, bottom=140, left=200, right=200)
        p = cell.paragraphs[0]
        p.paragraph_format.line_spacing = 1.15
        p.paragraph_format.space_after = Pt(2)
        r = p.add_run(code_text.rstrip())
        r.font.name = "Consolas"
        r.font.size = Pt(9)
        r.font.color.rgb = RGBColor(30, 41, 59)
        
        p_space = doc.add_paragraph()
        p_space.paragraph_format.space_after = Pt(6)
        in_code_block = False
        code_lines = []

    idx = 0
    while idx < len(lines):
        line = lines[idx]
        stripped = line.strip()
        
        # Manejo de bloques de código
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
            
        # Manejo de tablas markdown
        if stripped.startswith("|") and stripped.endswith("|"):
            # Ignorar separadores como |---|---|
            if set(stripped.replace("|", "").replace("-", "").replace(":", " ")) == {" "}:
                idx += 1
                continue
            cols = [c for c in stripped.split("|")[1:-1]]
            if not in_table:
                in_table = True
                table_rows = []
            table_rows.append(cols)
            idx += 1
            continue
        elif in_table:
            flush_table()
            
        if not stripped:
            idx += 1
            continue
            
        # Saltos de sección o líneas horizontales
        if stripped == "---":
            idx += 1
            continue
            
        # Encabezados
        if stripped.startswith("# "):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(22)
            p.paragraph_format.space_after = Pt(8)
            p.paragraph_format.keep_with_next = True
            add_formatted_runs(p, stripped[2:], base_bold=True, font_size=18, base_color=NAVY)
        elif stripped.startswith("## "):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(18)
            p.paragraph_format.space_after = Pt(6)
            p.paragraph_format.keep_with_next = True
            add_formatted_runs(p, stripped[3:], base_bold=True, font_size=14, base_color=SLATE)
        elif stripped.startswith("### "):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(12)
            p.paragraph_format.space_after = Pt(4)
            p.paragraph_format.keep_with_next = True
            add_formatted_runs(p, stripped[4:], base_bold=True, font_size=12, base_color=NAVY)
        elif stripped.startswith("#### "):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(8)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.keep_with_next = True
            add_formatted_runs(p, stripped[5:], base_bold=True, font_size=11, base_color=SLATE)
        elif stripped.startswith("* ") or stripped.startswith("- "):
            p = doc.add_paragraph(style='List Bullet')
            p.paragraph_format.space_after = Pt(3)
            p.paragraph_format.line_spacing = 1.15
            add_formatted_runs(p, stripped[2:], font_size=10.5)
        elif re.match(r'^\d+\.\s', stripped):
            p = doc.add_paragraph(style='List Number')
            p.paragraph_format.space_after = Pt(3)
            p.paragraph_format.line_spacing = 1.15
            text_num = re.sub(r'^\d+\.\s', '', stripped)
            add_formatted_runs(p, text_num, font_size=10.5)
        elif stripped.startswith("> "):
            # Blockquote
            table = doc.add_table(rows=1, cols=1)
            table.alignment = WD_TABLE_ALIGNMENT.CENTER
            cell = table.cell(0, 0)
            set_cell_background(cell, "F8FAFC")
            set_cell_margins(cell, top=100, bottom=100, left=180, right=140)
            p = cell.paragraphs[0]
            p.paragraph_format.line_spacing = 1.2
            add_formatted_runs(p, stripped[2:], base_italic=True, font_size=10.5, base_color=SLATE)
            p_space = doc.add_paragraph()
            p_space.paragraph_format.space_after = Pt(4)
        else:
            # Párrafo normal
            p = doc.add_paragraph()
            p.paragraph_format.space_after = Pt(6)
            p.paragraph_format.line_spacing = 1.2
            add_formatted_runs(p, stripped, font_size=10.5)
            
        idx += 1
        
    if in_table:
        flush_table()
    if in_code_block:
        flush_code()
        
    doc.save(docx_path)
    print(f"Documento generado exitosamente en: {docx_path}")

if __name__ == "__main__":
    # 1. Informe formal E2 (según rúbrica UNAB 100 pts)
    build_docx_from_md(
        "docs/E2_Metodologia_y_Avance_Tecnologico_Suite_UNAB.md",
        "docs/E2_Metodologia_y_Avance_Tecnologico_Suite_UNAB_Renderizado.docx",
        "SUITE UNAB: SISTEMA DE SOPORTE A LA DECISIÓN (DSS) CURRICULAR",
        "EVALUACIÓN E2 · METODOLOGÍA Y AVANCE TECNOLÓGICO\nDiseño, Arquitectura de Microservicios, Modelos de Grafos e IA"
    )
    
    # 2. Informe consolidado memoria continua (E1 + E2)
    build_docx_from_md(
        "docs/Memoria_Suite_UNAB_E1_E2_Consolidado.md",
        "docs/Memoria_Suite_UNAB_E1_E2_Consolidado.docx",
        "SUITE UNAB: SISTEMA DE SOPORTE A LA DECISIÓN (DSS) CURRICULAR",
        "INFORME CONSOLIDADO DE MEMORIA DE TÍTULO (EVALUACIÓN E1 + E2)\nFormulación, Fundamentación, Metodología y Avance Tecnológico"
    )
