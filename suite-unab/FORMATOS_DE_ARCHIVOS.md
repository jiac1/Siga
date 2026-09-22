# Formatos de archivo por app

Documentado directamente desde el código de cada app (parseo de columnas),
no supuesto. Útil para armar los archivos de prueba y para la guía de uso
que verá el personal de Servicio al Estudiante.

---

## Generador de Horarios

Dos archivos `.xlsx`, ambos elegidos/arrastrados en su propia zona de carga.

### 1. Archivo de datos (obligatorio) — "Detalle de docentes por NRC"

Acepta **dos formatos** (los detecta automáticamente, escaneando las primeras
60 filas de cada hoja en busca del encabezado):

**a) Formato canónico** — una hoja cuya fila de encabezados ya trae, literal:
`CURSO`, `NRC`, `HORARIO` (más las columnas que se necesiten).

**b) Export "Programación Académica" de Banner/Syaproa** — el archivo tal
como lo entrega el sistema de la universidad, con filas de metadata arriba de
la tabla real. La fila de encabezado debe contener una de estas combinaciones:

- `CÓDIGO` (o `CODIGO`) + `NRC` + `HORARIO` + `TIPO ACTIVIDAD`
- `MATERIA` + `CURSO` + `NRC` + `HORARIO` + `TIPO ACTIVIDAD`

Columnas adicionales que reconoce si están presentes (opcionales):
`SECCIÓN`/`SECCION`, `NOMBRE PROFESOR`, `RUT PROFESOR`/`RUT`, `SALA`,
`EDIFICIO`, `VACANTES`, `INSCRITOS`, `RESTRIC. COD.PROGRAMA`,
`NOMBRE ASIGNATURA`, `FECHA INICIO`, `FECHA FIN`.

### 2. Malla curricular (opcional — solo para filtrar por semestre)

También acepta dos formatos:

- **Nuevo:** bloques de semestre en la primera columna, con encabezado tipo
  `"2210-1SEM - 1SEM-ING CIVIL INFORMÁTICA"` seguido de las filas de curso de
  ese semestre.
- **Antiguo:** una fila de encabezado con columnas `SEMESTRE` y
  `CODIGO`/`CÓDIGO`.

---

## Mapa de Calor de Salas

Un solo archivo `.xlsx`.

- **La fila de encabezados debe estar en la fila 11** de la hoja (hay 10 filas
  de título/metadata arriba, típico de un export de Banner/Syaproa).
- Columnas obligatorias, con ese nombre exacto: **`Horario`**, **`Edificio`**,
  **`Sala`**, **`Capacidad Sala`**.
- Cada celda puede traer varios valores separados por `/` (ej. una fila con
  dos horarios, dos edificios y dos salas distintas para la misma sección) —
  la app los separa y los alinea por posición.

Si falta alguna de las 4 columnas, la app rechaza el archivo y muestra
exactamente cuál falta y cuáles sí encontró.

---

## Estrés de Malla (MallaIQ)

Dos archivos `.xlsx` por análisis: **`malla.xlsx`** y **`actas.xlsx`**.

### malla.xlsx (primera hoja)

| Posición | Contenido |
|---|---|
| Fila 0 | Encabezados |
| Columna 0 | Semestre (ej. "1° Semestre") |
| Columna 1 | Código de la asignatura |
| Columna 2 | Nombre de la asignatura |
| Columna 9 | Créditos UNAB |
| Columna 10 | Prerrequisitos |

### actas.xlsx (primera hoja)

| Posición | Contenido |
|---|---|
| Fila 0 | Título general (se ignora) |
| Fila 1 | Subtítulo (se ignora) |
| Fila 2 | Encabezados reales |
| Columnas | Una por periodo, con nombre `%reprobación 202510`, `%reprobación 202410`, etc. |

---

## Convalidación con IA *(pendiente — formato ya definido en el frontend, falta el backend de IA)*

Dos cargas, ambas en **PDF** (no Excel):

1. **Certificado de notas / concentración de notas** — un solo PDF, de la
   universidad de origen del estudiante. Se usa para verificar qué
   asignaturas aprobó y con qué nota.
2. **Programas de las asignaturas cursadas** — uno o varios PDF: puede ser
   un PDF por ramo, o un único PDF que contenga todos los programas
   (la app los segmenta automáticamente).

---

## Resumen rápido

| App | Archivo(s) | Formato |
|---|---|---|
| Generador de Horarios | Datos (oblig.) + Malla (opcional) | `.xlsx` × 2 |
| Mapa de Calor | 1 archivo | `.xlsx`, encabezado en fila 11 |
| Estrés de Malla | `malla.xlsx` + `actas.xlsx` | `.xlsx` × 2, columnas por posición |
| Convalidación con IA | Certificado + programas | `.pdf` × N |
