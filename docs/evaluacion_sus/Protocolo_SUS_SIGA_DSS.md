# Protocolo de Evaluación de Usabilidad (SUS) — SIGA-DSS

Documento operativo para aplicar en terreno el protocolo del **Anexo A** del informe final y cerrar el objetivo **OE7**. Incluye todo lo necesario para que cualquier integrante del equipo modere una sesión de forma idéntica: preparación, consentimiento, guion, tareas con criterio de éxito, cuestionario SUS, registro y análisis.

| Parámetro | Valor |
| :--- | :--- |
| Instrumento | *System Usability Scale* (Brooke, 1996), 10 ítems, Likert 1–5 |
| Muestra objetivo | $n = 30$ (estudiantes de Ingeniería Civil Informática + personal de secretaría académica / dirección de carrera) |
| Criterio de aceptación | SUS medio $\ge 70$ (rango "aceptable", Bangor et al., 2008) |
| Duración por sesión | ~15 minutos (10 min de tareas + 5 min de cuestionario) |
| Entorno | SIGA-DSS local con `docker compose up --build` en `http://localhost:8080` |
| Registro | `data/evaluacion_sus/plantilla_respuestas.csv` (una fila por participante) |
| Análisis | `python scripts/evaluacion/analizar_sus.py <respuestas.csv> --markdown --json --figura` |

---

## 1. Preparación (una vez, antes de la primera sesión)

1. Levantar la plataforma desde la raíz del repositorio:
   ```bash
   cp .env.example .env
   docker compose up --build
   ```
2. Verificar que se pueda iniciar sesión con las cuentas de demostración (`estudiante@unab.cl` para estudiantes y `staff@unab.cl` para personal académico; contraseñas en `.env`).
3. Dejar a mano en el escritorio los archivos de las tareas:
   * T3: `services/portal/apps/horarios/ejemplos/horarios_prueba.xlsx` y `malla_horarios_prueba.xlsx`
   * T4: `services/estres-malla/ejemplos/actas.xlsx`, `services/estres-malla/ejemplos/malla.xlsx` y `services/mapa-calor/ejemplos/mapa_calor_prueba.xlsx`
4. Preparar el cuestionario (Sección 6) como formulario en línea (Google Forms o Microsoft Forms) o impreso. **No** debe pedir nombre, RUT ni correo: solo el código de participante.
5. Tener un cronómetro y una copia impresa de la hoja de registro (Sección 7).

**Antes de cada sesión:** cerrar sesión, limpiar el horario armado y recargar el portal, para que todos partan del mismo estado.

## 2. Reclutamiento y muestra

* **Estudiantes (~24):** Ingeniería Civil Informática UNAB, idealmente de distintos niveles (1.º–2.º año y 3.º año o más), porque el uso de la malla y del generador de horarios cambia con el avance.
* **Staff (~6):** secretaría académica, coordinación o dirección de carrera. Son quienes realizan T4.
* Criterio de exclusión: haber participado en el desarrollo de SIGA-DSS.
* Asignar códigos correlativos: `P01`, `P02`, … para estudiantes y `S01`, `S02`, … para staff.

## 3. Consentimiento informado (leer al participante)

> "Gracias por participar. Estamos evaluando la facilidad de uso de SIGA-DSS, un proyecto de título de Ingeniería Civil Informática de la UNAB. **Evaluamos el sistema, no a usted**: si algo resulta difícil, es información valiosa para mejorarlo. La sesión dura unos 15 minutos. Le pediremos realizar algunas tareas y luego responder un cuestionario de 10 preguntas. No registraremos su nombre, RUT ni ningún dato que lo identifique; sus respuestas se guardarán solo con un código anónimo y se usarán exclusivamente con fines académicos, conforme a la Ley N.º 19.628 y la Ley N.º 21.719. Su participación es voluntaria y puede retirarse en cualquier momento sin dar explicaciones. ¿Acepta participar?"

Registrar `consentimiento = si` solo si la respuesta es afirmativa. Las filas sin consentimiento se excluyen automáticamente del análisis.

## 4. Guion del moderador

1. Leer el consentimiento.
2. Explicar: *"Le leeré cada tarea. Intente resolverla por su cuenta, como lo haría en su casa. Puede pensar en voz alta. Yo no podré ayudarle durante la tarea."*
3. Para cada tarea: leer el enunciado, **iniciar el cronómetro** al terminar de leer y **detenerlo** cuando el participante diga "listo" o cuando se cumpla el tiempo límite.
4. **No guiar.** Si el participante pregunta, responder: *"¿Qué haría usted si estuviera solo?"* Si se queda bloqueado más de 30 segundos, ofrecer pasar a la siguiente tarea y registrarla como fallida (`0`).
5. Al terminar las tareas, entregar el cuestionario SUS **antes** de conversar sobre la experiencia, para no sesgar las respuestas.
6. Anotar en `observaciones` los problemas observados (dónde dudó, qué buscó, errores). Es la información más útil para la discusión del informe.

## 5. Tareas guiadas

Criterio de éxito: `1` = completa sin ayuda dentro del tiempo; `parcial` = completa con un error menor o recién al límite; `0` = no completa, se rinde o se excede el tiempo.

| Tarea | Perfil | Enunciado para leer al participante | Criterio de éxito (`1`) | Límite |
| :--- | :--- | :--- | :--- | :---: |
| **T1 · Malla DAG** | Todos | "Abra la malla de Ingeniería Civil Informática (Plan 12210). Marque como aprobadas todas las asignaturas del primer semestre y dígame qué asignaturas quedan habilitadas para inscribir y cuántos créditos SCT lleva aprobados." | Marca los 4 ramos de S1 (Intro. Matemáticas, Física General, Intro. Ingeniería, Intro. Programación) e identifica correctamente los ramos habilitados y los créditos. | 3 min |
| **T2 · Convalidaciones** | Todos | "Imagine que viene transferido desde Ingeniería Civil Informática de la USACH. Seleccione esa carrera de origen, ingrese 5 asignaturas aprobadas y dígame qué asignatura UNAB le sugiere el sistema para cada una." | Selecciona el origen, evalúa 5 asignaturas y lee las sugerencias Top-3 con el folio generado. | 4 min |
| **T3 · Horarios UCTP** | Todos | "Cargue la programación semestral y la malla de los archivos del escritorio. Pida un horario con jornada de mañana usando *Branch & Bound*, verifique que no tenga topes y expórtelo a Excel." | Carga ambos archivos, genera un horario con 0 topes y descarga el Excel. | 4 min |
| **T4 · Gestión académica** | Solo staff | "En *Estrés de Malla*, cargue las actas y la malla, y dígame cuál es la asignatura más crítica. Luego, en *Mapa de Calor*, cargue la planilla de salas e identifique un bloque horario subutilizado." | Identifica el ramo con mayor índice de estrés y al menos un bloque ocioso. | 5 min |

Para estudiantes, dejar `t4_exito` y `t4_segundos` **vacíos** (no `0`): el script interpreta el vacío como "tarea no aplicada".

## 6. Cuestionario SUS (versión en español)

Instrucción al participante: *"Para cada afirmación, marque cuánto está de acuerdo, pensando en su experiencia recién vivida con SIGA-DSS. Responda todas; si no está seguro, marque 3."*

Escala: **1** = Totalmente en desacuerdo · **2** · **3** · **4** · **5** = Totalmente de acuerdo

| N.º | Afirmación |
| :---: | :--- |
| 1 | Creo que me gustaría usar SIGA-DSS con frecuencia. |
| 2 | Encontré SIGA-DSS innecesariamente complejo. |
| 3 | Pensé que SIGA-DSS era fácil de usar. |
| 4 | Creo que necesitaría el apoyo de una persona con conocimientos técnicos para poder usar SIGA-DSS. |
| 5 | Encontré que las distintas funciones de SIGA-DSS estaban bien integradas. |
| 6 | Pensé que había demasiada inconsistencia en SIGA-DSS. |
| 7 | Imagino que la mayoría de las personas aprendería a usar SIGA-DSS muy rápidamente. |
| 8 | Encontré SIGA-DSS muy engorroso de usar. |
| 9 | Me sentí muy seguro/a usando SIGA-DSS. |
| 10 | Necesité aprender muchas cosas antes de poder empezar a usar SIGA-DSS. |

**No cambiar el orden ni invertir la redacción:** la alternancia de ítems positivos (impares) y negativos (pares) es parte del instrumento y el cálculo depende de ella.

Cálculo (lo realiza el script): ítems impares aportan $x - 1$, ítems pares aportan $5 - x$; la suma (0–40) se multiplica por 2,5, lo que da un puntaje en $[0, 100]$. **El puntaje SUS no es un porcentaje.**

## 7. Registro de datos

Copiar `data/evaluacion_sus/plantilla_respuestas.csv` a `data/evaluacion_sus/respuestas.csv` y agregar una fila por participante:

| Columna | Contenido | Ejemplo |
| :--- | :--- | :--- |
| `participante_id` | Código anónimo único | `P07` |
| `perfil` | `estudiante` o `staff` | `estudiante` |
| `fecha` | Fecha de la sesión | `2026-12-03` |
| `consentimiento` | `si` / `no` | `si` |
| `sus_1` … `sus_10` | Respuesta Likert 1–5 | `4` |
| `tN_exito` | `1`, `0`, `parcial` o vacío si no aplica | `parcial` |
| `tN_segundos` | Tiempo cronometrado en segundos | `142` |
| `observaciones` | Problemas observados (texto libre, sin datos personales) | `Buscó el botón exportar en el menú superior` |

Si se usa un formulario en línea, exportar las respuestas a CSV y ajustar los nombres de columna a la plantilla. El script acepta separador `,` o `;` (Excel en español).

## 8. Análisis y resultados para el informe

```bash
python scripts/evaluacion/analizar_sus.py data/evaluacion_sus/respuestas.csv \
    --markdown \
    --json docs/img/metricas_sus.json \
    --figura docs/img/fig_sus.png      # la figura requiere: pip install matplotlib
```

El script entrega:
* SUS medio, desviación estándar, mediana, mínimo y máximo, con **IC 95% bootstrap** ($B = 2.000$, semilla fija: el resultado es reproducible), igual que en la evaluación del motor de convalidación.
* Porcentaje de participantes con SUS $\ge 70$ y el rango de aceptabilidad de la media.
* Desagregación por perfil (estudiante / staff) y promedio por ítem, que sirve para detectar qué aspecto concreto falla (p. ej., ítem 4 alto = el sistema requiere ayuda técnica).
* Tasa de éxito y tiempo mediano de cada tarea.
* Una tabla Markdown (`--markdown`) lista para pegar en el informe.

El script **no inventa datos**: si no hay participantes válidos, termina con error. Si $n < 30$, lo informa para declararlo como limitación.

**Integración en el informe final (una vez obtenidos los datos reales):**
1. Agregar una subsección **5.7 Evaluación de Usabilidad (SUS)** con la tabla generada, la figura `fig_sus.png` y un análisis de las observaciones más frecuentes.
2. En la Tabla 9, cambiar la fila "Evaluación de usabilidad SUS" de *Pendiente* al resultado medido.
3. En la Tabla 10, actualizar **OE7** de *Parcial* a *Cumplido* (si SUS $\ge 70$) o reportar el resultado y las mejoras derivadas si no se alcanza.
4. Eliminar la limitación 2 de la Sección 6.2 y el punto correspondiente de la Sección 7.3 (o ajustarlos si $n < 30$).
5. En el Anexo A, cambiar "Protocolo Diseñado" por "Protocolo Aplicado", indicar fechas y $n$ reales, y corregir T1: el Anexo dice "6 asignaturas aprobadas", pero el primer semestre del Plan 12210 tiene 4; este protocolo usa el semestre completo.

## Referencias

* Bangor, A., Kortum, P. T., & Miller, J. T. (2008). An empirical evaluation of the System Usability Scale. *International Journal of Human–Computer Interaction*, 24(6), 574–594. https://doi.org/10.1080/10447310802205776
* Brooke, J. (1996). SUS: A "quick and dirty" usability scale. En P. W. Jordan, B. Thomas, B. A. Weerdmeester, & I. L. McClelland (Eds.), *Usability Evaluation in Industry* (pp. 189–194). Taylor & Francis.
