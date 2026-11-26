# Evidencia para la defensa — Gold Standard y Catálogo Curricular

Preguntas asignadas por el profesor guía (retroalimentación E3) a **José Ignacio Amar**. Cada respuesta se apoya en artefactos versionados del repositorio; no se afirma nada que no esté medido.

---

## Pregunta 1 · «¿Cómo se etiquetó el gold standard, quién decidió las equivalencias y cómo se evita que el glosario se haya ajustado a esos mismos pares?»

### Qué se hizo (hechos verificables)

| Aspecto | Evidencia |
| :--- | :--- |
| Archivo | `data/convalidacion/evaluacion/gold.json` (versión `2026-10-21`) |
| Criterio | Para cada asignatura de origen, el código UNAB que una Dirección de Carrera aceptaría como equivalente, o `null` si no existe equivalente en la malla UNAB. Se usa **solo el nombre**, igual que el modo catálogo del sistema. |
| Casos dudosos | **Excluidos, no forzados**: las asignaturas cuyo equivalente es discutible sin revisar el programa quedan en la lista `excluidas` (11 solo en el par USACH Informática). |
| Composición | 112 asignaturas en 3 pares reales: 69 con equivalente y 43 sin equivalente. Un caso admite dos códigos válidos (*Cálculo Diferencial e Integral* → `FMMP112` o `FMMP212`). |
| Anotador | Un solo anotador del equipo. El propio archivo declara: *«Etiquetado inicial por el autor del proyecto; DEBE ser validado por la Dirección de Carrera antes de reportarse como métrica oficial.»* |

### Cómo se mitigó el sesgo del glosario (cifras de la Tabla 2 del informe)

El glosario (`conceptos.json`) se construyó en la misma fecha y mirando los mismos pares, así que el sesgo es real. Se mitigó de tres formas:

1. **La mayor parte de la ganancia no depende del glosario.** La ablación con **0 conceptos** alcanza F1 = 0,774, frente a 0,029 de la línea base y 0,43–0,46 de las alternativas LSA y n-gramas. El glosario aporta los últimos +0,18.
2. **Validación cruzada por par universitario (LOPO).** Se calibra con 2 pares y se evalúa a ciegas en el tercero: F1 = 0,964.
3. **LOPO con poda de conceptos.** Se eliminan del glosario los conceptos que no se activan en los pares de entrenamiento (quedan 30–35 de 50): F1 = 0,925. Aun quitando el conocimiento del par de prueba, el motor supera la meta de 0,90.

### Lo que hay que reconocer

* Un solo anotador y sin acuerdo entre anotadores medido: es la debilidad que señaló el profesor y es correcta.
* La poda mitiga el sobreajuste del glosario, pero no lo elimina: los conceptos que sobreviven también se diseñaron conociendo los tres pares.

### Acción en curso: segundo anotador independiente (kappa de Cohen)

```bash
# 1. Planilla ciega ya generada: docs/defensa/Anotacion_Ciega_Gold_Standard.xlsx
#    (112 asignaturas en orden aleatorio, sin etiquetas originales, lista desplegable con los cursos UNAB)
# 2. El segundo anotador la completa sin ver gold.json (~30–40 min)
# 3. Calcular el acuerdo:
python scripts/evaluacion/acuerdo_gold.py kappa <planilla_completada.xlsx> \
    --json docs/img/metricas_acuerdo_gold.json --desacuerdos docs/defensa/desacuerdos_gold.csv
```

El script reporta el acuerdo observado, el **kappa multiclase** (código exacto) y el **kappa binario** (¿hay equivalente o no?), con IC 95% bootstrap, interpretación de Landis y Koch (1977) y la lista de desacuerdos para adjudicar.

**Resultado:** *(pendiente: completar cuando el segundo anotador entregue la planilla)*

**Cómo usarlo en la defensa:** «Para responder a esta observación, una segunda persona etiquetó a ciegas las 112 asignaturas. El kappa fue X (interpretación); los desacuerdos se concentraron en Y». Si el kappa sale bajo, también sirve: demuestra que se midió y qué tipo de casos son ambiguos (normalmente asignaturas de nivel o electivas).

---

## Pregunta 2 · «¿Cómo se verificó la transcripción de las 1.582 asignaturas desde fuentes públicas?»

### Proceso de transcripción (hechos verificables)

| Aspecto | Evidencia |
| :--- | :--- |
| Trazabilidad | `data/universidades/fuentes.csv`: para las 27 mallas, URL de la fuente oficial (PDF o imagen de la propia universidad), fecha de consulta y método. |
| Métodos | 11 mallas: lectura visual del PDF + capa de texto (doble contraste) · 10: lectura visual del PDF · 6: imagen oficial (5 de U. de Chile) o PDF a alta resolución. |
| Fuente de verdad legible | `data/universidades/transcripciones/*.txt`: una línea por semestre, revisable por cualquier persona contra la fuente. |
| Validación automática | `scripts/catalogo/build_catalogo_universidades.py --check` valida estructura, metadatos obligatorios y áreas (pasa sin errores). |
| Composición de la cifra | **1.582 = 1.310 convalidables + 272 genéricas.** Las genéricas (electivos, minors, formación general, marcadas con `~`) se excluyen de la convalidación. 9 asignaturas tienen su semestre marcado como incierto (`?`) en vez de asignarle uno arbitrario. |

### Auditoría por muestreo contra la fuente oficial (realizada el 2026-11-26)

La validación automática revisa el **formato**, no el **contenido**. Para medir el contenido se auditó una muestra aleatoria reproducible:

```bash
python scripts/catalogo/auditar_transcripciones.py --muestra 6 --semilla 2026 --cache <carpeta> --csv <salida.csv>
```

| Malla (sorteo, semilla 2026) | Tipo de fuente | Método de verificación | Resultado |
| :--- | :--- | :--- | :---: |
| UAH · Ing. Civil Informática | PDF con texto | Búsqueda automática | 63/63 |
| U. de Chile · Ing. Civil de Minas | Imagen JPEG | Revisión visual (nombre, semestre, código y créditos) | 54/54 |
| UFT · Ing. Civil Informática y Telecom. | PDF sin capa de texto | Revisión visual (nombre y semestre) | 58/58 |
| USACH · Ing. Ejecución Computación | PDF con texto | Búsqueda automática | 39/39 |
| USACH · Ing. Civil Industrial | PDF con texto | Búsqueda automática | 55/55 |
| USM · Ing. Civil Informática | PDF con texto | Búsqueda automática | 59/59 |
| **Total** | 6 de 27 mallas, 3 tipos de fuente | | **334/334 (100%)** |

* La muestra cubre **334 de 1.582 asignaturas (21,1%)**. Las 6 fuentes siguen en línea en la URL registrada.
* **0 errores de transcripción** de nombre. En las dos mallas revisadas visualmente también coinciden el semestre y, en U. de Chile, los 54 códigos y créditos.
* **1 observación de clasificación (no de transcripción):** en UFT, *Ética* está en el bloque transversal «Finis Transforma», igual que *Antropología*, que está marcada como genérica; *Ética* quedó como convalidable. No afecta la evaluación porque UFT no es parte del Gold Standard.
* Con 0 errores en 334 asignaturas, la regla del 3 da una tasa de error poblacional **< 0,9%** con 95% de confianza (3/334), suponiendo una muestra representativa.
* Detalle por asignatura: `docs/defensa/auditoria_transcripciones_muestra.csv`.

### Limitaciones a reconocer

* La búsqueda automática confirma que cada asignatura transcrita **existe** en la fuente (no hay nombres inventados), pero no detecta por sí sola asignaturas **omitidas**. La completitud se verificó visualmente en 2 de las 6 mallas.
* Una sola persona transcribió; la auditoría es el control independiente posterior.

### Respuesta sugerida (≈1 minuto)

> «Cada malla se transcribió desde la fuente oficial publicada por la universidad, con la URL, la fecha y el método registrados en `fuentes.csv`, a un formato de texto legible que el pipeline valida automáticamente. Como esa validación revisa el formato y no el contenido, hicimos una auditoría por muestreo: sorteamos 6 de las 27 mallas con semilla fija, cubriendo PDFs con texto, PDFs sin texto e imágenes, y comparamos 334 asignaturas, el 21% del total, contra la fuente. Coincidieron todas: 216 de forma automática con la capa de texto del PDF y 118 por revisión visual, incluyendo códigos y créditos en la U. de Chile. Encontramos una sola inconsistencia, que es de clasificación y no de transcripción. Con 0 errores en 334, la tasa de error esperada es menor al 1% con 95% de confianza.»

## Referencias

* Landis, J. R., & Koch, G. G. (1977). The measurement of observer agreement for categorical data. *Biometrics*, 33(1), 159–174. https://doi.org/10.2307/2529310
* Hanley, J. A., & Lippman-Hand, A. (1983). If nothing goes wrong, is everything all right? Interpreting zero numerators. *JAMA*, 249(13), 1743–1745. https://doi.org/10.1001/jama.1983.03330370053031
