# Suite UNAB

Plataforma web unificada de aplicaciones de apoyo académico (Facultad de Ingeniería, Universidad Andrés Bello, sede Santiago): Malla curricular, Convalidación de asignaturas, Generador de horarios, Mapa de calor de salas, Estrés de malla y SIGA. Cada módulo funciona por sí solo o como suite, con inicio de sesión único y licencias por módulo.

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

## Estructura

```
services/portal        front-ends estáticos (portal, Malla, Horarios, Convalidación, SIGA)
services/core          Django 5.2 + DRF: identidad, licencias, catálogo, convalidaciones
services/mapa-calor    Django sin estado
services/estres-malla  Django multi-institución
packages/suite-sso     librería compartida de SSO
data/                  catálogo curricular
scripts/               catálogo, evaluación del motor, entorno de desarrollo
deploy/ infra/         Docker, nginx, Terraform (AWS)
```
