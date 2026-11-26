# SIGA-DSS

Plataforma web unificada (Sistema de Soporte a la Decisión Curricular y Logística, Facultad de Ingeniería, Universidad Andrés Bello, sede Santiago): Malla curricular DAG, Convalidación de asignaturas con IA, Generador de horarios (UCTP), Mapa de calor de salas, Estrés de malla (*MallaIQ*) y SIGA. Cada módulo funciona por sí solo o como suite, con inicio de sesión único y licencias por módulo.

---

## Ejecutar la demo

```bash
python -m venv .venv
.venv\Scripts\activate                 # macOS/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
python scripts/dev/suite.py preparar   # migraciones, datos demo y catálogo
python scripts/dev/suite.py iniciar    # http://localhost:8080
```

En Windows también: doble clic en `iniciar-suite.bat`. Usuarios de prueba en `.env.example`.

## 🐳 Ejecución con Docker

Requiere únicamente Docker y Docker Compose (sin instalar Python ni PostgreSQL en el equipo):

```bash
git clone https://github.com/jiac1/Siga.git
cd Siga
cp .env.example .env
docker compose up --build
```

El portal unificado y todos los módulos quedan disponibles en `http://localhost:8080`. Si se omite `cp .env.example .env`, `docker-compose.yml` usa claves de desarrollo local por defecto para levantar el entorno sin bloqueos.

---

## Estructura

```text
services/portal        front-ends estáticos (portal, Malla DAG, Horarios UCTP, Convalidación, SIGA)
services/core          Django 5.2 + DRF: identidad, licencias, catálogo, convalidaciones IA, motor UCTP
services/mapa-calor    Django sin estado (analítica espacial Banner/Syaproa)
services/estres-malla  Django multi-institución (MallaIQ + Curricular Analytics DAG b/d/c)
packages/suite-sso     librería compartida de SSO (JWT HS256)
data/                  catálogo curricular (10 mallas UNAB + 27 mallas de 11 universidades + Gold Standard)
scripts/               catálogo, evaluación de motores (convalidación, UCTP, suite) y compilación de informes
deploy/ infra/         Docker, nginx, Terraform (AWS)
```

## Pruebas y evaluación reproducible

```bash
# Suite automatizada (69 pruebas: suite-sso, core, mapa-calor, estres-malla)
python -m pytest packages/suite-sso
(cd services/core && python -m pytest)
(cd services/mapa-calor && python -m pytest)
(cd services/estres-malla && python -m pytest)

# Benchmarks algorítmicos y auditoría técnica integral
python scripts/evaluacion/evaluar_motor.py
python scripts/evaluacion/evaluar_uctp.py
python scripts/evaluacion/evaluar_itc2019.py --max-perfiles 30 --json docs/img/metricas_itc2019.json
python scripts/evaluacion/evaluar_campus_itc2019.py --iteraciones 2500 --json docs/img/metricas_campus_itc2019.json
python scripts/evaluacion/evaluar_suite.py

# Usabilidad SUS con datos reales de terreno (protocolo en docs/evaluacion_sus/)
python scripts/evaluacion/analizar_sus.py data/evaluacion_sus/respuestas.csv --markdown --json docs/img/metricas_sus.json

# Generación de figuras, informe consolidado E1-E3, presentación y guión de defensa
python scripts/render_diagrams.py
python scripts/generar_gantt_matplotlib.py
python scripts/generar_graficos_e3.py
python scripts/generar_docx_formal.py
python scripts/generar_ppt_defensa.py
python scripts/generar_guion_docx.py
python scripts/generar_poster.py                     # póster A0 (requiere "qrcode[pil]")

# Evidencia para la defensa (docs/defensa/)
python scripts/evaluacion/acuerdo_gold.py planilla --salida docs/defensa/Anotacion_Ciega_Gold_Standard.xlsx
python scripts/evaluacion/acuerdo_gold.py kappa <planilla_completada.xlsx>
python scripts/catalogo/auditar_transcripciones.py --muestra 6 --semilla 2026 --cache <carpeta> --csv <salida.csv>
```
