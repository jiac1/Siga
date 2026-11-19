"""Renderiza diagramas arquitectónicos Mermaid a PNG de alta resolución (2x)."""

from __future__ import annotations

import os

from playwright.sync_api import sync_playwright

DIAGRAMS = {
    "dss_ciclo_cerrado": """flowchart TD
    GW["<b>SIGA-DSS · Suite UNAB</b><br/>(Gateway Nginx :8080 / CloudFront + ALB)"]

    subgraph DEMANDA["GESTIÓN CURRICULAR (Demanda Pedagógica)"]
        D1["1. Malla Interactiva (DAG)<br/>- Trayectoria, cascada y what-if"]
        D2["2. Estrés de Malla (MallaIQ)<br/>- Curricular Analytics b(v), d(v), c(v) + Actas"]
        D3["3. Convalidaciones con IA<br/>- Motor TF-IDF + 50 Conceptos + Precedentes"]
    end

    subgraph OFERTA["GESTIÓN DE CAPACIDAD (Oferta Operativa)"]
        O1["4. Mapa de Calor de Salas<br/>- Matriz espacial Banner/Syaproa"]
        O2["5. Generador de Horarios (UCTP)<br/>- Branch & Bound + SA + Auditoría H2/H3"]
    end

    GW --> DEMANDA
    GW --> OFERTA
    DEMANDA -.->|"Retroalimentación Continua: Demanda Curricular vs. Capacidad Física"| OFERTA
""",
    "c4_contenedores": (
        "graph TD\n"
        "    User([Estudiante / Postulante / Directivo]) -->|HTTP :8080 / HTTPS| "
        "Gateway[Gateway Reverse Proxy / Nginx / CloudFront+ALB]\n\n"
        '    subgraph SIGA_Arch["Arquitectura de Contenedores SIGA-DSS (Suite UNAB)"]\n'
        '        Gateway -->|/| Portal["Portal Web Estático (S3/Nginx)'
        '<br/>Malla DAG · Horarios UCTP · Convalidación UI"]\n'
        '        Gateway -->|/core/*| CoreService["Servicio Core (Django 5.2 + DRF)'
        '<br/>Identidad SSO · Catálogo · Convalidaciones · API UCTP"]\n'
        '        Gateway -->|/mapa-calor/*| MapaCalor["Servicio Mapa de Calor (Django Stateless)'
        '<br/>Analítica Espacial Banner/Syaproa"]\n'
        '        Gateway -->|/estres-malla/*| EstresMalla["Servicio Estrés de Malla (Django Multi-tenant)'
        '<br/>MallaIQ · Curricular Analytics DAG + Actas"]\n\n'
        "        CoreService --> CoreDB[(PostgreSQL 16 / SQLite Core)]\n"
        "        EstresMalla --> EstresDB[(PostgreSQL 16 / SQLite Estrés)]\n\n"
        "        CoreService -.->|Emite Cookie JWT HS256| User\n"
        "        MapaCalor -.->|Valida JWT + Licencia| SuiteSSO[Paquete Compartido suite-sso]\n"
        "        EstresMalla -.->|Valida JWT + Licencia| SuiteSSO\n"
        "    end\n"
    ),
    "pipeline_etl": (
        "flowchart LR\n"
        '    A["Resoluciones UNAB & Mallas 11 Univ."] -->|"Transcripción & Trazabilidad"| '
        'B["27 Transcripciones .txt + fuentes.csv"]\n'
        '    B -->|"Normalización & Esquema JSON"| C["Catálogo Unificado (10 UNAB + 27 Externas)"]\n'
        '    C -->|"Validación DAG & Carga ORM"| D[("PostgreSQL / Repositorio Estático")]\n'
        '    D -->|"Consumo sin Estado"| E["Motor Convalidación IA · MallaIQ · UCTP"]\n'
    ),
}


def render_all() -> None:
    """Renderiza cada diagrama Mermaid a ``docs/img/<nombre>.png`` usando Chromium."""
    os.makedirs("docs/img", exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for name, code in DIAGRAMS.items():
            html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <script>
        mermaid.initialize({{
            startOnLoad: true,
            theme: 'base',
            themeVariables: {{
                fontFamily: 'Calibri, sans-serif',
                primaryColor: '#EEF2F6',
                primaryTextColor: '#0F2043',
                primaryBorderColor: '#0F2043',
                lineColor: '#334155',
                secondaryColor: '#F8FAFC',
                tertiaryColor: '#FFFFFF'
            }}
        }});
    </script>
    <style>
        body {{
            background: #FFFFFF;
            padding: 28px;
            margin: 0;
            display: inline-block;
        }}
        .mermaid svg {{
            max-width: 100% !important;
            height: auto !important;
        }}
    </style>
</head>
<body>
    <div class="mermaid">
{code}
    </div>
</body>
</html>"""
            page = browser.new_page(viewport={"width": 1360, "height": 900}, device_scale_factor=2)
            page.set_content(html)
            page.wait_for_selector(".mermaid svg")
            svg = page.locator(".mermaid svg")
            out_png = f"docs/img/{name}.png"
            svg.screenshot(path=out_png)
            print(f"Generado exitosamente: {out_png}")
            page.close()
        browser.close()


if __name__ == "__main__":
    render_all()
