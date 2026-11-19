# Siga — Suite UNAB

Plataforma web unificada de aplicaciones de apoyo académico (Facultad de Ingeniería, Universidad Andrés Bello, sede Santiago): Malla curricular, Convalidación de asignaturas, Generador de horarios, Mapa de calor de salas, Estrés de malla y SIGA. Cada módulo funciona por sí solo o como suite, con inicio de sesión único y licencias por módulo.

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

En Windows también: doble clic en `iniciar-suite.bat`. Con Docker: `docker compose up --build`. Usuarios de prueba en `.env.example`.

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
# Suite automatizada (65 pruebas: suite-sso, core, mapa-calor, estres-malla)
python -m pytest packages/suite-sso
(cd services/core && python -m pytest)
(cd services/mapa-calor && python -m pytest)
(cd services/estres-malla && python -m pytest)

# Benchmarks algorítmicos y auditoría técnica integral
python scripts/evaluacion/evaluar_motor.py
python scripts/evaluacion/evaluar_uctp.py
python scripts/evaluacion/evaluar_suite.py
```
