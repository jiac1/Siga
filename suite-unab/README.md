# Suite UNAB — prototipo

Primer prototipo de la Suite: un "shell" único (marca, login, dashboard) que
integra las apps de apoyo académico ya desarrolladas por el secretario
académico de Ingeniería Civil Informática, sin reescribir su lógica interna.

## Estado de integración

| App | Estado | Cómo corre |
|---|---|---|
| Malla curricular | ✅ Integrada | Estática (parte del mismo servidor de la Suite) |
| Generador de horarios | ✅ Integrada | Estática (parte del mismo servidor de la Suite) |
| SIGA | ✅ Integrada | Estática (parte del mismo servidor de la Suite) |
| Mapa de calor | ✅ Integrada visualmente | Es una app **Django**; corre en su propio servidor local, en otro puerto |
| Estrés de Malla (MallaIQ) | ✅ Integrada visualmente | Otro repo del profesor (`Mallaiq`, no estaba en la carpeta original — se tomó de su GitHub). Django, con cuentas y multi-institución real. Corre en su propio servidor local |
| Convalidación con IA | ⏳ Pendiente | El profesor aún no la entrega; no incluida en este prototipo |

## De dónde salió "Estrés de Malla"

No estaba en los zips originales. El profesor tiene 18 repositorios en GitHub;
varios son versiones alternativas de las mismas apps (2-3 variantes de
Convalidar, de Generador de Horarios, de Mapa de Calor). Se comparó tamaño,
fecha de último commit y contenido real de cada familia:

- Las variantes de Convalidar/Horarios/Mapa de Calor no superan a las que ya
  teníamos (son diseños alternativos o versiones más simples, sin backend).
- `Mallaiq` resultó ser algo distinto y más valioso: un Django **multi-tenant**
  (modelos `Organization` + `User` con roles) que implementa "Estrés de
  Malla" — el módulo 4 que la landing de SIGA promete pero que no existía en
  ningún zip. Es además el primer ejemplo real, en todo el proyecto, de cómo
  se vería la arquitectura de cuentas por institución que necesita la
  comercialización a otras universidades.

**Se corrigieron dos bugs reales del repo original para poder levantarlo:**
1. `config/settings.py` forzaba el motor PostgreSQL aunque no hubiera
   `DATABASE_URL` configurada, rompiendo el uso local con SQLite.
2. Al `templates/malla/dashboard.html` le faltaba el módulo
   `malla/templatetags/malla_extras.py` que define el filtro `get_item` que
   la plantilla usa — nunca se subió al repo. Se implementó siguiendo el
   patrón estándar de Django.

**Ya probado end-to-end:** se armaron archivos de prueba
([apps/estres-malla/ejemplos/malla.xlsx](apps/estres-malla/ejemplos/malla.xlsx) y
[actas.xlsx](apps/estres-malla/ejemplos/actas.xlsx), 10 asignaturas en 2
semestres, con casos de reprobación real de 1 y 2 periodos y de estimación
contextual) y se subieron al endpoint real. Esto sacó a la luz un **tercer
bug** del repo original:

3. `templates/malla/ver_analisis.html` insertaba el dashboard generado con
   `srcdoc="{{ analisis.html_resultado|escapejs }}"` — `escapejs` es para
   strings dentro de `<script>`, no para atributos HTML, así que el iframe
   mostraba el código fuente en crudo como texto en vez de renderizarlo. Se
   cambió a escape HTML normal (quitar `|escapejs`).

Con los 3 bugs corregidos, el flujo completo funciona: login → subir
malla.xlsx + actas.xlsx → dashboard de estrés con barras por asignatura,
coloreadas por % de aprobación, igual al mockup que muestra la landing de
SIGA.

## Cómo correrlo en local

**1. La Suite (shell + Malla + Horarios + SIGA), todo estático:**

```bash
cd suite-unab
python -m http.server 8791
```

Abrir `http://localhost:8791/index.html`. Pide un login de demostración
(cualquier nombre/correo sirve — ver `shared/auth.js`, es un stub, no
seguridad real).

**2. Mapa de calor (Django, aparte):**

```bash
cd suite-unab/apps/mapa-calor
pip install -r requirements.txt
python manage.py runserver 127.0.0.1:8792
```

Abrir `http://localhost:8792/`. La tarjeta "Mapa de calor" del dashboard
apunta directo a ese puerto.

> Por qué separado: es la única app que necesita un backend Python
> corriendo (procesa archivos .xlsx en el servidor); las demás son
> HTML/JS que corren enteramente en el navegador. Cuando se despliegue en
> AWS, las dos partes quedarán detrás del mismo dominio y esta diferencia
> deja de notarse para el usuario.

## Cómo está armada la integración

- `shared/tokens.css` — paleta de marca de Suite UNAB (navy/rojo, tomada de
  la app de Malla original).
- `shared/auth.js` — sesión de demostración vía `localStorage`. Aislado a
  propósito en un solo archivo para poder reemplazarlo por el SSO
  institucional real sin tocar el resto de la Suite.
- `shared/suite-bar.js` / `.css` — barra superior común ("Suite UNAB / Nombre
  de la app") que se inyecta en cada página integrada, sin modificar el
  HTML/CSS/JS propio de cada app.
- `apps/<nombre>/` — cada app copiada tal cual del repositorio original,
  con solo las líneas necesarias agregadas en `<head>`/`<body>` para cargar
  la barra compartida.
- `apps/mapa-calor/` — es distinta: al ser Django, la barra está duplicada
  directamente en `heatmap/templates/heatmap/base.html` (no puede enlazar
  a `shared/` porque corre en otro servidor/origen en local). Esto se
  simplifica en el despliegue en AWS.

## Formatos de archivo que espera cada app

Ver [FORMATOS_DE_ARCHIVOS.md](FORMATOS_DE_ARCHIVOS.md) — columnas exactas y
formato de cada .xlsx/.pdf que se sube, sacado directo del código de cada app
(no supuesto).

## Pulido hacia alpha — Malla curricular y Generador de Horarios

Auditoría completa del código de ambas apps, buscando bugs y funcionalidad
faltante (sin agregar features nuevas). Encontrado y corregido:

**Malla curricular:**
1. **Regresión real:** el listado (`index.html`) solo mostraba 8 de las 10
   mallas que existen en la carpeta. "Ingeniería en Computación e
   Informática" se perdió al agregar "Civil Industrial 2.0" (se ve en el
   diff contra `index_1.html`, una versión anterior que sí la tenía), y
   "Ingeniería Civil Industrial" (Plan 12100) nunca se agregó. Ambas se
   sumaron de vuelta, con sus datos reales (asignaturas/créditos/áreas)
   sacados de cada archivo. Se eliminó `index_1.html` (duplicado obsoleto,
   causa de la confusión).
2. El progreso marcado ("aprobadas") se guardaba en una sola clave de
   `localStorage` por carrera, sin distinguir usuario — con el login real
   que agregamos, dos personas en el mismo navegador se pisaban el avance.
   Se agregó separación por usuario logueado en los 10 archivos de malla.
3. El aviso de "inscripción de asignaturas" tenía una fecha fija ya pasada
   (semana de julio, hoy es septiembre) — se generalizó el texto para que no
   se vea desactualizado en una demo.

**Generador de Horarios:**
1. Riesgo de estabilidad real: `opcionesPorCurso` hace una búsqueda
   exhaustiva (backtracking) de combinaciones de secciones por curso, sin
   ningún tope — con un curso muy concurrido (muchas secciones × varias
   actividades) puede crecer exponencialmente y colgar el navegador. Se
   agregó un tope defensivo (300 combinaciones por curso) que no cambia el
   resultado en catálogos normales.
2. Se armó un archivo de prueba (`ejemplos/horarios_prueba.xlsx` +
   `ejemplos/malla_horarios_prueba.xlsx`, formato Programación
   Académica/Banner) y se probó el flujo completo end-to-end: carga de
   datos, carga de malla, generación de horario completo, generación de
   horarios de alumno sin topes (2 combinaciones no conflictivas generadas
   correctamente) y exportación a Excel — todo sin errores de consola.

El resto del código de ambas apps (drawer de detalle, cadena de
prerrequisitos, parseo de los distintos formatos de columnas, exportación)
ya estaba sólido — no se tocó.

## Pulido hacia alpha — Mapa de Calor y Estrés de Malla

**Mapa de Calor** — 1 bug real, grave, encontrado al probar la descarga con
un archivo real (ver [ejemplos/mapa_calor_prueba.xlsx](apps/mapa-calor/ejemplos/mapa_calor_prueba.xlsx)):

1. `SESSION_ENGINE = 'signed_cookies'` guardaba **toda la sesión dentro de la
   cookie**, incluido el Excel generado en base64. Los navegadores cortan
   cada cookie en ~4 KB; con datos de un campus real (varios edificios) el
   Excel supera eso fácilmente, la cookie se descarta en silencio y
   "Descargar Excel" deja de funcionar sin ningún error visible — se
   verificó el fallo exacto con curl (el `Set-Cookie` de sesión nunca
   llegaba a guardarse). Se cambió a sesiones en archivo (no requiere base
   de datos, que este proyecto no tiene configurada). Probado de nuevo:
   subida → resultados → descarga, con el Excel de 7 hojas íntegro.

El resto (cálculo de ocupación, generación del heatmap, exportación a Excel
con formato condicional) se verificó llamando `procesar_archivo` directo y
está correcto — no se tocó.

**Estrés de Malla (MallaIQ)** — 2 bugs más encontrados (además de los 3 ya
corregidos antes: forzado de PostgreSQL, filtro `get_item` faltante,
`escapejs` mal usado):

1. `malla/views.org_required` renderiza `malla/inactiva.html` cuando la
   organización de un usuario tiene `activa=False` — la plantilla nunca se
   subió al repo. Cualquier institución desactivada (justo el escenario
   central del modelo multi-tenant: una universidad cliente cuya cuenta se
   suspende) rompía con `TemplateDoesNotExist` en vez de mostrar un mensaje
   claro. Se creó la plantilla y se probó desactivando una organización de
   verdad en la base de datos: ahora responde 403 con el mensaje correcto.
2. `accounts/urls.py` define `profile/` -> `profile_view`, pero
   `accounts/profile.html` tampoco existía (hoy no hay ningún link a esa
   página en la UI, pero la URL está viva). Se agregó la plantilla.

## Elegir malla existente (en vez de subir un archivo)

Generador de Horarios y Estrés de Malla ya no obligan a descargar la malla
de tu carrera desde Malla curricular y volver a subirla — un botón
"Elegir malla existente" abre un carrusel/buscador con las 10 mallas ya
cargadas en la Suite y la aplica directo.

**Cómo está armado:**
- `shared/mallas/*.json` — catálogo de las 10 mallas, extraído automáticamente
  de los `CURSOS` embebidos en cada `malla_*.html` con
  [scripts/extraer_mallas.js](scripts/extraer_mallas.js) (`node scripts/extraer_mallas.js`
  desde la raíz de `suite-unab`). Si una malla cambia en Malla curricular,
  hay que volver a correrlo y re-copiar el resultado a
  `apps/estres-malla/static/mallas/`.
- `shared/malla-picker.js` / `.css` — el widget del carrusel, genérico y sin
  dependencias, reutilizado igual en ambas apps.
- **Generador de Horarios** (estática, mismo origen): lee `shared/mallas/`
  directo.
- **Estrés de Malla** (Django, otro origen): igual que con la barra
  compartida, el catálogo y el widget están duplicados dentro de
  `apps/estres-malla/static/` para que Django los sirva desde su propio
  origen. Del lado servidor, `malla_desde_catalogo()` (en `engine.py`)
  arma el mismo DataFrame que `leer_malla()` pero a partir del JSON, y la
  vista `subir_excel` acepta `malla_slug` como alternativa a subir
  `archivo_malla` (se guarda en `AnalisisMalla.malla_catalogo_slug` para
  saber de dónde salió cada análisis). Se agregó una migración para que
  `archivo_malla` sea opcional.

Cuando todo quede bajo un mismo dominio en AWS, esta duplicación se puede
eliminar y ambas apps apuntar al mismo `shared/mallas/`.

## Pendiente para las próximas iteraciones

- Integrar Convalidación con IA cuando el profesor la entregue.
- Reemplazar el login de demostración por el SSO institucional de la UNAB.
- Definir arquitectura AWS (hosting estático + hosting del backend Django)
  y unificar todo bajo un solo dominio.
