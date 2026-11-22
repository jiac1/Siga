"""Renderiza diagramas de arquitectura en alta resolución (3000+ px) para el Paper E3."""

from __future__ import annotations

import os

from playwright.sync_api import sync_playwright

BASE_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  background: #FFFFFF;
  font-family: 'Segoe UI', 'Calibri', Arial, sans-serif;
  color: #0F2043;
  padding: 28px 32px;
  display: inline-block;
}
.canvas {
  width: 1080px;
  background: #FFFFFF;
}
.title {
  text-align: center;
  font-size: 21px;
  font-weight: 800;
  color: #0F2043;
  margin-bottom: 18px;
  letter-spacing: -0.2px;
}
.box {
  border-radius: 12px;
  border: 2px solid #0F2043;
  background: #F8FAFC;
  padding: 14px 18px;
  box-shadow: 0 2px 8px rgba(15, 32, 67, 0.06);
}
.box-navy {
  background: #0F2043;
  color: #FFFFFF;
  border-color: #0F2043;
}
.box-teal {
  background: #ECFDF5;
  border-color: #0D9488;
}
.box-blue {
  background: #EFF6FF;
  border-color: #1E40AF;
}
.box-db {
  background: #F1F5F9;
  border-color: #334155;
  border-radius: 26px / 12px;
}
.box h3 {
  font-size: 16px;
  font-weight: 700;
  margin-bottom: 4px;
  line-height: 1.25;
}
.box p, .box li {
  font-size: 13.5px;
  color: #334155;
  line-height: 1.4;
}
.box-navy p { color: #CBD5E1; }
.badge {
  display: inline-block;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.6px;
  padding: 3px 9px;
  border-radius: 99px;
  margin-bottom: 7px;
}
.b-navy { background: #E2E8F0; color: #0F2043; }
.b-blue { background: #DBEAFE; color: #1E40AF; }
.b-teal { background: #CCFBF1; color: #0F766E; }
.b-slate { background: #E2E8F0; color: #334155; }
.arrow-down {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin: 8px 0;
}
.arrow-label {
  font-size: 12.5px;
  font-weight: 700;
  color: #1E40AF;
  background: #EFF6FF;
  border: 1px solid #BFDBFE;
  padding: 2px 10px;
  border-radius: 99px;
  margin: 4px 0;
}
"""

HTML_DSS_CICLO = f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8"><style>
{BASE_CSS}
.gw-wrap {{ display: flex; justify-content: center; }}
.gw-box {{ width: 540px; text-align: center; }}
.cols {{ display: grid; grid-template-columns: 1fr 1fr; gap: 28px; margin-top: 4px; }}
.panel {{
  border: 2px dashed #64748B;
  border-radius: 14px;
  padding: 16px 18px;
  background: #F8FAFC;
}}
.panel-h {{
  font-size: 15px;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 12px;
  text-align: center;
}}
.stack {{ display: flex; flex-direction: column; gap: 10px; }}
.mod-card {{
  background: #FFFFFF;
  border: 1.5px solid #CBD5E1;
  border-left: 5px solid #1E40AF;
  border-radius: 10px;
  padding: 11px 14px;
}}
.panel-oferta .mod-card {{ border-left-color: #0D9488; }}
.mod-card b {{ display: block; font-size: 15px; color: #0F2043; margin-bottom: 3px; }}
.mod-card span {{ font-size: 13px; color: #475569; line-height: 1.35; display: block; }}
.feedback {{
  margin-top: 16px;
  border: 2px solid #0D9488;
  background: #F0FDFA;
  border-radius: 12px;
  padding: 12px 20px;
  text-align: center;
  font-size: 14.5px;
  font-weight: 700;
  color: #0F766E;
}}
</style></head><body>
<div class="canvas" id="diagram">
  <div class="title">Arquitectura SIGA-DSS en Ciclo Cerrado</div>
  <div class="gw-wrap">
    <div class="box box-navy gw-box">
      <h3>Orquestador Central y Gateway Único</h3>
      <p>Nginx Reverse Proxy (:8080) / CloudFront + ALB · SSO Federado (JWT HS256)</p>
    </div>
  </div>
  <div class="arrow-down">
    <svg width="620" height="36" viewBox="0 0 620 36">
      <line x1="310" y1="0" x2="310" y2="14" stroke="#334155" stroke-width="2.5"/>
      <line x1="150" y1="14" x2="470" y2="14" stroke="#334155" stroke-width="2.5"/>
      <line x1="150" y1="14" x2="150" y2="30" stroke="#1E40AF" stroke-width="2.5"/>
      <polygon points="144,26 156,26 150,35" fill="#1E40AF"/>
      <line x1="470" y1="14" x2="470" y2="30" stroke="#0D9488" stroke-width="2.5"/>
      <polygon points="464,26 476,26 470,35" fill="#0D9488"/>
    </svg>
  </div>
  <div class="cols">
    <div class="panel">
      <div class="panel-h" style="color:#1E40AF">Gestión Curricular · Demanda Pedagógica</div>
      <div class="stack">
        <div class="mod-card">
          <b>1. Malla Interactiva (DAG)</b>
          <span>Recorrido BFS/DFS de prerrequisitos, cascada de aprobación y avance SCT (10 mallas UNAB).</span>
        </div>
        <div class="mod-card">
          <b>2. Estrés de Malla (MallaIQ)</b>
          <span>Curricular Analytics: bloqueo b(v), retraso d(v), complejidad c(v) y tasas reales de actas.</span>
        </div>
        <div class="mod-card">
          <b>3. Convalidaciones con IA</b>
          <span>Motor híbrido TF-IDF + 50 conceptos + Dice-IDF + precedentes históricos (F1 = 0,957).</span>
        </div>
      </div>
    </div>
    <div class="panel panel-oferta">
      <div class="panel-h" style="color:#0F766E">Gestión de Capacidad · Oferta Operativa</div>
      <div class="stack">
        <div class="mod-card">
          <b>4. Mapa de Calor de Salas</b>
          <span>Analítica matricial por campus, edificio y bloque horario (M1–M20) sobre
          planillas Banner/Syaproa.</span>
        </div>
        <div class="mod-card">
          <b>5. Generador de Horarios (UCTP)</b>
          <span>Branch &amp; Bound admisible + Recocido Simulado: cero topes (H1), auditoría
          salas/docentes (H2/H3) y minimización de ventanas.</span>
        </div>
        <div class="mod-card" style="border-left-color:#334155;background:#F1F5F9;">
          <b>6. Vacantes Efectivas sin Tope</b>
          <span>Verificación combinatoria de cupos reales compatibles con el resto de la carga semestral.</span>
        </div>
      </div>
    </div>
  </div>
  <div class="feedback">
    ⇄ Retroalimentación Continua de Ciclo Cerrado: Demanda Curricular Proyectada ↔ Capacidad Física de Aulas y Secciones
  </div>
</div>
</body></html>"""

HTML_C4_CONTENEDORES = f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8"><style>
{BASE_CSS}
.actor-wrap {{ display: flex; justify-content: center; }}
.actor {{
  background: #0F2043; color: #FFF; padding: 11px 28px; border-radius: 99px;
  font-size: 15.5px; font-weight: 700; text-align: center;
}}
.gw {{ width: 720px; margin: 0 auto; text-align: center; }}
.grid4 {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-top: 6px; }}
.grid3 {{ display: grid; grid-template-columns: 1fr 1fr 1.25fr; gap: 18px; margin-top: 14px; align-items: stretch; }}
.svc {{ min-height: 155px; display: flex; flex-direction: column; justify-content: space-between; }}
.route {{
  font-family: Consolas, monospace; font-size: 13px; font-weight: 700;
  color: #1E40AF; background: #DBEAFE; padding: 3px 8px; border-radius: 6px;
  display: inline-block; margin-bottom: 6px;
}}
.db-card {{ text-align: center; display: flex; flex-direction: column; justify-content: center; }}
.sso-box {{ border: 2px solid #0D9488; background: #F0FDFA; border-radius: 12px; padding: 12px 16px; }}
.sso-box h3 {{ font-size: 15.5px; font-weight: 800; color: #0F766E; margin-bottom: 4px; }}
.sso-box p {{ font-size: 13px; color: #1E293B; line-height: 1.4; }}
</style></head><body>
<div class="canvas" id="diagram">
  <div class="title">Modelo C4 · Diagrama de Contenedores de SIGA-DSS</div>
  <div class="actor-wrap">
    <div class="actor">Estudiante · Postulante · Docente / Jefatura · Secretaría Académica</div>
  </div>
  <div class="arrow-down">
    <span class="arrow-label">HTTP :8080 (Docker Local) · HTTPS :443 (CloudFront + WAF)</span>
    <svg width="24" height="22" viewBox="0 0 24 22">
      <line x1="12" y1="0" x2="12" y2="14" stroke="#0F2043" stroke-width="2.5"/>
      <polygon points="6,12 18,12 12,21" fill="#0F2043"/>
    </svg>
  </div>
  <div class="box box-navy gw">
    <h3>Gateway Reverse Proxy Unificado (Nginx / CloudFront + ALB)</h3>
    <p>Enrutamiento por prefijo sin reescritura · Cabeceras de seguridad (HSTS, X-Frame-Options, nosniff)</p>
  </div>
  <div class="arrow-down">
    <svg width="920" height="32" viewBox="0 0 920 32">
      <line x1="460" y1="0" x2="460" y2="12" stroke="#334155" stroke-width="2.5"/>
      <line x1="115" y1="12" x2="805" y2="12" stroke="#334155" stroke-width="2.5"/>
      <line x1="115" y1="12" x2="115" y2="25" stroke="#1E40AF" stroke-width="2.5"/>
      <polygon points="109,22 121,22 115,31" fill="#1E40AF"/>
      <line x1="345" y1="12" x2="345" y2="25" stroke="#1E40AF" stroke-width="2.5"/>
      <polygon points="339,22 351,22 345,31" fill="#1E40AF"/>
      <line x1="575" y1="12" x2="575" y2="25" stroke="#1E40AF" stroke-width="2.5"/>
      <polygon points="569,22 581,22 575,31" fill="#1E40AF"/>
      <line x1="805" y1="12" x2="805" y2="25" stroke="#1E40AF" stroke-width="2.5"/>
      <polygon points="799,22 811,22 805,31" fill="#1E40AF"/>
    </svg>
  </div>
  <div class="grid4">
    <div class="box box-blue svc">
      <div>
        <span class="route">/</span>
        <h3>Portal Web Estático</h3>
        <p>Nginx / S3 + CloudFront</p>
      </div>
      <p style="margin-top:8px;">Malla DAG, Horarios UCTP (<code>uctp-solver.js</code>), Convalidación UI y SIGA.</p>
    </div>
    <div class="box box-blue svc">
      <div>
        <span class="route">/core/*</span>
        <h3>Servicio Core</h3>
        <p>Django 5.2 + DRF</p>
      </div>
      <p style="margin-top:8px;">Identidad SSO, RBAC, Licencias, Catálogo, Convalidaciones IA y API REST UCTP.</p>
    </div>
    <div class="box box-blue svc">
      <div>
        <span class="route">/estres-malla/*</span>
        <h3>Estrés de Malla</h3>
        <p>Django Multi-Tenant</p>
      </div>
      <p style="margin-top:8px;">MallaIQ: métricas DAG b(v), d(v), c(v), actas históricas e índice de estrés.</p>
    </div>
    <div class="box box-teal svc">
      <div>
        <span class="route">/mapa-calor/*</span>
        <h3>Mapa de Calor</h3>
        <p>Django Stateless</p>
      </div>
      <p style="margin-top:8px;">Procesamiento en memoria de planillas Banner/Syaproa, matriz espacial y .xlsx.</p>
    </div>
  </div>
  <div class="grid3">
    <div class="box box-db db-card">
      <h3>PostgreSQL 16 · Core</h3>
      <p>Organizaciones, Usuarios, Licencias, Catálogo, Solicitudes, Precedentes y Auditoría.</p>
    </div>
    <div class="box box-db db-card">
      <h3>PostgreSQL 16 · Estrés</h3>
      <p>Organizaciones, Carreras, Umbrales, Análisis Históricos y Archivos en S3/Media.</p>
    </div>
    <div class="sso-box">
      <h3>Paquete Compartido: suite-sso (JWT HS256)</h3>
      <p><b>Core</b> emite cookie <code>HttpOnly</code> firmada con <code>SUITE_SSO_SECRET</code>;
      <b>Estrés de Malla</b> y <b>Mapa de Calor</b> validan identidad, rol y licencias localmente
      sin consultar la BD de Core.</p>
    </div>
  </div>
</div>
</body></html>"""

HTML_PIPELINE_ETL = f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8"><style>
{BASE_CSS}
.row {{
  display: grid;
  grid-template-columns: 1fr 44px 1fr 44px 1fr;
  align-items: center;
  gap: 6px;
}}
.row-bottom {{
  display: grid;
  grid-template-columns: 1fr 44px 1fr;
  align-items: center;
  gap: 8px;
  width: 72%;
  margin: 0 auto;
}}
.step {{
  min-height: 122px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}}
.step h3 {{ font-size: 16px; color: #0F2043; margin-bottom: 5px; }}
.step p {{ font-size: 13.5px; color: #334155; }}
.h-arrow {{ display: flex; flex-direction: column; align-items: center; justify-content: center; }}
.h-arrow span {{ font-size: 11px; font-weight: 700; color: #1E40AF; margin-bottom: 3px; text-align: center; }}
.turn-connector {{
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 12px;
  margin: 12px 0;
}}
</style></head><body>
<div class="canvas" id="diagram">
  <div class="title">Pipeline de Extracción, Transformación, Validación y Carga (ETL Curricular)</div>
  <div class="row">
    <div class="box step">
      <span class="badge b-slate">Paso 1 · Fuentes</span>
      <h3>Resoluciones UNAB y Mallas Nacionales</h3>
      <p>Decretos oficiales UNAB (10 carreras) y prospectos de 11 universidades chilenas
      con trazabilidad en <code>fuentes.csv</code>.</p>
    </div>
    <div class="h-arrow">
      <span>Parsing</span>
      <svg width="36" height="18" viewBox="0 0 36 18">
        <line x1="0" y1="9" x2="26" y2="9" stroke="#1E40AF" stroke-width="2.5"/>
        <polygon points="24,4 35,9 24,14" fill="#1E40AF"/>
      </svg>
    </div>
    <div class="box box-blue step">
      <span class="badge b-blue">Paso 2 · Extracción</span>
      <h3>27 Transcripciones Estructuradas</h3>
      <p>Textos normalizados (<code>.txt</code>) con códigos, créditos, semestres, descriptores
      y aprendizajes esperados.</p>
    </div>
    <div class="h-arrow">
      <span>Esquema</span>
      <svg width="36" height="18" viewBox="0 0 36 18">
        <line x1="0" y1="9" x2="26" y2="9" stroke="#1E40AF" stroke-width="2.5"/>
        <polygon points="24,4 35,9 24,14" fill="#1E40AF"/>
      </svg>
    </div>
    <div class="box box-blue step">
      <span class="badge b-blue">Paso 3 · Normalización</span>
      <h3>Catálogo JSON Unificado</h3>
      <p>10 mallas UNAB (486 ramos), 27 mallas externas (1.582 ramos) y diccionario semántico de 50 conceptos.</p>
    </div>
  </div>

  <div class="turn-connector">
    <svg width="26" height="28" viewBox="0 0 26 28">
      <line x1="13" y1="0" x2="13" y2="18" stroke="#0D9488" stroke-width="2.8"/>
      <polygon points="6,16 20,16 13,27" fill="#0D9488"/>
    </svg>
    <span class="arrow-label" style="color:#0F766E;background:#CCFBF1;border-color:#99F6E4;">
      Validación Topológica DAG (0 Ciclos) e Ingesta Idempotente (cargar_catalogo)
    </span>
  </div>

  <div class="row-bottom">
    <div class="box box-db step">
      <span class="badge b-navy">Paso 4 · Persistencia</span>
      <h3>PostgreSQL 16 + Estáticos JSON</h3>
      <p>Tablas normalizadas en <code>core</code> (preservando precedentes aprobados)
      y copias estáticas versionadas en el portal.</p>
    </div>
    <div class="h-arrow">
      <span>Consumo</span>
      <svg width="36" height="18" viewBox="0 0 36 18">
        <line x1="0" y1="9" x2="26" y2="9" stroke="#0D9488" stroke-width="2.5"/>
        <polygon points="24,4 35,9 24,14" fill="#0D9488"/>
      </svg>
    </div>
    <div class="box box-teal step">
      <span class="badge b-teal">Paso 5 · Motores DSS</span>
      <h3>Inferencia IA · MallaIQ · UCTP</h3>
      <p>Convalidaciones (<code>F1=0,957</code>), métricas de estrés
      <code>b(v), d(v), c(v)</code> y optimización horaria sin topes.</p>
    </div>
  </div>
</div>
</body></html>"""

DIAGRAMS = {
    "dss_ciclo_cerrado": HTML_DSS_CICLO,
    "c4_contenedores": HTML_C4_CONTENEDORES,
    "pipeline_etl": HTML_PIPELINE_ETL,
}


def render_all() -> None:
    """Renderiza los diagramas de arquitectura en PNG de alta resolución (3x)."""
    os.makedirs("docs/img", exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for name, html in DIAGRAMS.items():
            page = browser.new_page(viewport={"width": 1240, "height": 1000}, device_scale_factor=3)
            page.set_content(html, wait_until="load")
            el = page.locator("#diagram")
            out_png = f"docs/img/{name}.png"
            el.screenshot(path=out_png)
            print(f"Generado exitosamente: {out_png}")
            page.close()
        browser.close()


if __name__ == "__main__":
    render_all()
