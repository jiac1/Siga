# Guión de Apoyo · Defensa Final E3 — SIGA-DSS

**Duración objetivo:** 11 minutos 30 segundos (rango 10–12 min) · **12 diapositivas**  
**Expositores:** José Ignacio Amar (Slides 1–4) · Felipe Riquelme Salvo (Slides 5–7) · Maximiliano Alonso Vargas (Slides 8–12)  
**Archivo de presentación:** `docs/Presentacion_Defensa_SIGA_DSS.pptx`

---

## 1. Panel de Control de Tiempos

| Slide | Título / Tema | Expositor | Duración | Ventana Acumulada | Rol en la Narrativa |
| :---: | :--- | :--- | :---: | :---: | :--- |
| **1** | Portada y Contexto SIGA-DSS | José Ignacio | 0:30 | 00:00 – 00:30 | Apertura y presentación del equipo |
| **2** | Diagnóstico: Sobreduración y Fragmentación | José Ignacio | 1:00 | 00:30 – 01:30 | Urgencia cuantitativa SIES / USACH / UNAB |
| **3** | Hipótesis y Ciclo Cerrado SIGA-DSS | José Ignacio | 1:00 | 01:30 – 02:30 | Tesis estructural y 3 pilares |
| **4** | Suite Modular, Portal y Catálogo | José Ignacio | 1:00 | 02:30 – 03:30 | Qué hace el producto + pase a Felipe |
| **5** | Arquitectura de Contenedores (Modelo C4) | Felipe | 1:10 | 03:30 – 04:40 | Microservicios, gateway y paridad AWS |
| **6** | Seguridad OWASP, `suite-sso` y Ley 21.719 | Felipe | 1:00 | 04:40 – 05:40 | JWT sin estado, RBAC y privacidad por diseño |
| **7** | Pipeline ETL y Calidad CI/CD (69 tests) | Felipe | 1:00 | 05:40 – 06:40 | Trazabilidad de datos, CI + pase a Maximiliano |
| **8** | Curricular Analytics (DAG) en 10 Mallas | Maximiliano | 1:00 | 06:40 – 07:40 | 0 ciclos, `TDFI102` (52,1%) y `MallaIQ` |
| **9** | Motor Híbrido de Convalidaciones (IA) | Maximiliano | 1:10 | 07:40 – 08:50 | Salto `0,029 → 0,957`, ablación y LOPO CV |
| **10** | Optimización Combinatoria UCTP + ITC-2019 | Maximiliano | 1:15 | 08:50 – 10:05 | `H1=0`, B&B vs. SA, ITC-2019 y Campus |
| **11** | Cumplimiento OE1–OE7, Límites y Futuro | Maximiliano | 0:55 | 10:05 – 11:00 | Honestidad técnica y hoja de ruta |
| **12** | Cierre y Preguntas de la Comisión | Maximiliano (+ equipo) | 0:30 | 11:00 – 11:30 | 4 cifras emblema y cierre conjunto |

### Guía de Recorte Rápido (si la comisión pide ceñirse a 10:00 exactos)

* **-0:15 en Slide 2 (José Ignacio):** Mencionar solo `13,8` semestres (`+2,91` de exceso), `~50%` deserción al 3.er año y `34%–43%` créditos perdidos, omitiendo el detalle anual del costo país.
* **-0:15 en Slide 4 (José Ignacio):** Enumerar las 5 apps en una sola frase rápida y cerrar con el total (`10 mallas UNAB` + `27 externas`).
* **-0:20 en Slide 6 (Felipe):** Resumir los 4 puntos OWASP en dos frases (JWT `HttpOnly` en `126,7 µs` + aislamiento 404 cross-tenant) y enfocar la mitad derecha en la purga a `730 días` de Ley 21.719.
* **-0:15 en Slide 7 (Felipe):** Leer solo el total (`69/69 pruebas` y `Ruff 0 errores`) sin desglosar los conteos por servicio.
* **-0:25 en Slides 10 y 11 (Maximiliano):** En Slide 10 resumir ITC-2019 como `-17% a -33% pareado` sin leer cada dataset; en Slide 11 agrupar `OE1–OE5 cumplidos` y pasar directo a los 2 parciales (`AWS` y `SUS`).

---

## 2. Guión Diapositiva por Diapositiva

### Bloque 1 · Problema, Hipótesis y Producto (José Ignacio Amar · Slides 1–4 · 3:30)

#### Slide 1 · Portada (`0:30` · `00:00–00:30`)
> **Cue visual:** Mirar a la comisión, esperar silencio inicial y señalar brevemente el subtítulo.

"Buenas tardes a la comisión y a nuestro profesor guía, Jorge Sabattin. Somos Felipe Riquelme, Maximiliano Vargas y quien les habla, José Ignacio Amar. Hoy presentamos nuestro proyecto de título **SIGA-DSS**, un sistema modular de soporte a la decisión diseñado e implementado para la Facultad de Ingeniería de la Universidad Andrés Bello. Nuestra propuesta integra grafos curriculares, convalidaciones asistidas por recuperación de información y optimización combinatoria de horarios bajo una arquitectura web reproducible en ciclo cerrado."

---

#### Slide 2 · Diagnóstico: Sobreduración y Fragmentación (`1:00` · `00:30–01:30`)
> **Cue visual:** Apuntar las 4 tarjetas superiores de izquierda a derecha, luego contrastar los dos bloques inferiores.

"¿Por qué abordar este problema? Según cifras oficiales del SIES 2023, Ingeniería Civil Informática en Chile tarda en promedio **13,8 semestres** reales frente a 10 u 11 nominales: casi **3 semestres de sobreduración** (2,91). En programas afines como USACH, la deserción ronda el 22% a 28% el primer año, pero escala a **casi el 50% al tercer año**, y solo la deserción de primer año le cuesta al país entre **128 y 141 millones de dólares al año**.

La literatura demuestra que esto no es solo un problema socioeconómico, sino estructural: **el 76,2% de los desertores tardíos** abandona adeudando ramos cuello de botella, **6 de los 7 predictores críticos** de abandono aparecen ya en el primer semestre, y en traslados universitarios los estudiantes pierden entre **34% y 43%** de sus créditos por procesos manuales. En el contexto previo de Ingeniería UNAB existían scripts y planillas útiles, pero operaban aislados, sin SSO, sin contratos compartidos, con un motor base de convalidación de apenas **0,029 en F1** y sin optimización horaria."

---

#### Slide 3 · Hipótesis y Ciclo Cerrado SIGA-DSS (`1:00` · `01:30–02:30`)
> **Cue visual:** Señalar primero la caja verde izquierda (Hipótesis) y luego recorrer el diagrama de derecha: Gateway arriba → dos columnas → barra inferior de retroalimentación.

"Frente a ese diagnóstico planteamos la hipótesis de que unificar estas capacidades en un Sistema de Soporte a la Decisión modular, auditable y con algoritmos reproducibles permite diagnosticar cuellos de botella, acelerar convalidaciones con alta precisión y generar horarios sin topes ni ventanas innecesarias.

Como muestra el diagrama, SIGA-DSS opera en **ciclo cerrado** tras un gateway único. A la izquierda gestionamos la **demanda pedagógica**: qué ramos habilitan a cuáles en la malla DAG, dónde se concentra el estrés de reprobación en *MallaIQ* y qué asignaturas son convalidables. A la derecha gestionamos la **oferta operativa**: cómo se ocupan físicamente las salas de Banner o Syaproa y cómo asignar horarios sin topes ni exceso de ventanas. La barra inferior cierra el ciclo: la demanda proyectada retroalimenta la planificación de capacidad y vacantes."

---

#### Slide 4 · Suite Modular, Portal y Catálogo (`1:00` · `02:30–03:30`)
> **Cue visual:** Recorrer las tarjetas por rol (Estudiantes, Postulantes, Gestión), cerrar en la franja oscura inferior y mirar a Felipe para el pase.

"Bajo una arquitectura tipo *suite*, cada herramienta funciona de manera autónoma o integrada desde un portal común según la licencia de la institución. Para **estudiantes** entregamos el visualizador DAG de mallas y el generador combinatorio de horarios. Para **postulantes** de admisión especial ofrecemos la pre-evaluación de convalidaciones con acceso público. Y para **gestión académica**, *MallaIQ* y el mapa de calor de salas sobre planillas oficiales.

Todo se respalda en un catálogo real curado dentro del repositorio: **10 mallas oficiales UNAB** con **486 asignaturas y 570 aristas**, más **27 mallas externas de 11 universidades chilenas** que suman **1.582 asignaturas** trazables en `fuentes.csv`. Con esta base de datos estructurada, doy el paso a Felipe para explicar la arquitectura, la seguridad y el pipeline de ingeniería."

---

### Bloque 2 · Arquitectura, Seguridad y Calidad de Software (Felipe Riquelme Salvo · Slides 5–7 · 3:10)

#### Slide 5 · Arquitectura de Contenedores — Modelo C4 (`1:10` · `03:30–04:40`)
> **Cue visual:** Seguir el diagrama C4 de arriba hacia abajo: usuarios → Gateway Nginx/CloudFront → 4 contenedores → bases de datos y `suite-sso`.

"Gracias, José Ignacio. En el diagrama de contenedores C4 se aprecia cómo desacoplamos la plataforma en cuatro piezas detrás de un único **Gateway Reverse Proxy** por prefijo, sin reescritura de rutas.

El tráfico entra por Nginx en el puerto **8080** en desarrollo local —o por CloudFront más ALB con WAF en AWS— y se distribuye hacia: primero, el **portal web estático** con las interfaces de Malla DAG, Horarios y Convalidación; segundo, **`core`** en Django 5.2 + DRF, que centraliza identidad, licencias, catálogo, motor de convalidaciones y la API UCTP; tercero, **`estres-malla`**, un servicio multi-tenant con base de datos PostgreSQL aislada; y cuarto, **`mapa-calor`**, que es deliberadamente *stateless* y procesa planillas Banner/Syaproa en memoria. Toda esta topología levanta localmente con un solo comando `docker compose up --build` y replica exactamente la infraestructura declarada en Terraform para AWS."

---

#### Slide 6 · Seguridad OWASP, `suite-sso` y Ley 21.719 (`1:00` · `04:40–05:40`)
> **Cue visual:** Alternar entre tarjeta izquierda (`suite-sso`) y derecha (`Ley 21.719`), cerrando brevemente en la barra inferior de transparencia.

"En seguridad aplicamos dos principios clave: **autenticación sin estado** y **privacidad por diseño**. Nuestro paquete compartido `suite-sso` firma tokens **JWT HS256** emitidos por `core` en cookies `HttpOnly`, validando audiencia, emisor, expiración y secreto mínimo de 32 caracteres. Tanto `estres-malla` como `mapa-calor` verifican identidad, roles RBAC y licencias localmente en **126,7 microsegundos por ciclo**, evitando cuellos de botella contra la base de datos de `core`. Rechazamos tokens `alg=none`, bloqueamos *Open Redirect*, recalculamos puntajes de convalidación exclusivamente en el servidor y forzamos aislamiento multi-tenant devolviendo HTTP 404 ante accesos cruzados.

Por el lado normativo, alineado con la **Ley 21.719**, exigimos consentimiento explícito, validamos RUT con módulo 11, registramos auditoría inmutable y fijamos retención de **730 días** con purga automatizada que anonimiza datos personales conservando solo precedentes estadísticos. Como brecha transparente, el MFA queda delegable al IdP institucional UNAB y la firma es escalable a RS256."

---

#### Slide 7 · Pipeline ETL y Calidad CI/CD (`1:00` · `05:40–06:40`)
> **Cue visual:** Seguir el flujo del ETL de izquierda a derecha, luego señalar la tarjeta verde `69 / 69 tests` arriba a la derecha y dar el pase a Maximiliano.

"Para garantizar calidad de datos, construimos un pipeline ETL idempotente desde decretos oficiales UNAB y prospectos externos hacia transcripciones normalizadas y JSON unificado. Antes de persistir en PostgreSQL 16, el comando `cargar_catalogo` certifica **0 ciclos** en el grafo y preserva los precedentes históricos ya aprobados por Dirección de Carrera.

Toda la plataforma está protegida por integración continua en GitHub Actions con **69 pruebas automatizadas `pytest`** pasando al 100% en los cuatro módulos, **0 errores de linter en Ruff**, validación sintáctica de Terraform y prueba E2E en navegador real con Playwright. Además, el CI incluye compuertas algorítmicas bloqueantes: si el motor de convalidación cae bajo **0,90 de F1** o aparece un ciclo en una malla o un choque horario, el pipeline falla automáticamente. Ahora Maximiliano presentará los resultados cuantitativos de nuestros tres motores principales."

---

### Bloque 3 · Motores Algorítmicos, Resultados y Cierre (Maximiliano Alonso Vargas · Slides 8–12 · 4:50)

#### Slide 8 · Curricular Analytics (DAG) en 10 Mallas UNAB (`1:00` · `06:40–07:40`)
> **Cue visual:** Apuntar Panel A (barra roja de Ing. Civil Informática), luego Panel B (`TDFI102` c=32) y finalmente la tarjeta verde inferior de `MallaIQ`.

"Gracias, Felipe. Al modelar las **10 mallas oficiales de Ingeniería UNAB** como Grafos Dirigidos Acíclicos —486 asignaturas y 570 aristas—, el análisis con Kahn y DFS certificó **0 ciclos** en apenas **16,1 milisegundos**.

En el panel izquierdo vemos la complejidad estructural total `C(G)` por carrera, destacando **Ingeniería Civil Informática con 492 puntos**. Y en el panel derecho está el hallazgo clave para gestión docente: el ramo **`TDFI102` (Introducción a la Programación)** de primer semestre tiene un factor de bloqueo de **25** y retraso **7** (`c = 32`), lo que significa que reprobar ese único curso bloquea el **52,1%** de la carrera completa; mientras que la línea matemática encabezada por **`FMMP012`** fija el camino crítico más largo de **8 semestres**. Esto explica topológicamente por qué los indicadores del primer semestre dominan el riesgo de deserción tardía. En *MallaIQ*, multiplicamos esa complejidad por la tasa de reprobación de actas (`e(v)`) para priorizar intervenciones."

---

#### Slide 9 · Motor Híbrido de Convalidaciones (`1:10` · `07:40–08:50`)
> **Cue visual:** Señalar primero el salto de barras en Panel A, luego la meseta de estabilidad en τ=0,45 en Panel B y la tarjeta verde `F1 = 0,957`.

"En convalidación evaluamos el motor sobre un *Gold Standard* experto de **112 asignaturas** en tres pares reales entre USACH, Universidad de Chile y UNAB. En consultas de catálogo donde solo llega el nombre corto del ramo de origen, la línea base textual caía a **F1 = 0,029**. Modelos vectoriales sin diccionario como **LSA/SVD** o **n-gramas de caracteres** solo llegan a **0,429** y **0,455**, porque confunden niveles como *Cálculo I* con *Cálculo II*.

Nuestro motor híbrido —que combina similitud Dice ponderada por IDF, penalización explícita de nivel (`×0,60`) y un glosario curado de **50 conceptos**— alcanza **F1 = 0,957** con intervalo Bootstrap 95% de **[0,919; 0,987]**, **Top-3 de 1,000** y una latencia de **752 ms**, sin costos ni alucinaciones de LLMs externos. La tabla de ablación prueba que el núcleo léxico aporta hasta **0,774** y el glosario completa el salto; más importante aún, en validación cruzada **Leave-One-University-Pair-Out** sostiene **0,964**, e incluso podando los conceptos exclusivos del par retenido mantiene **0,925**. Los precedentes humanos aprobados siempre prevalecen con puntaje 1,00."

---

#### Slide 10 · Optimización Combinatoria UCTP + ITC-2019 (`1:15` · `08:50–10:05`)
> **Cue visual:** Comparar brevemente los dos gráficos superiores (A: UNAB, B: ITC-2019) y luego bajar por las 4 KPI cards de izquierda a derecha.

"Nuestro tercer motor ataca el problema de horarios UCTP en dos niveles. En tiempo real para estudiantes, garantizamos **100% de factibilidad sin topes (`H1 = 0`)** y auditamos colisiones de sala (`H2`) y docente (`H3`). Comparando contra backtracking aleatorio en instancias UNAB de hasta **202.500 combinaciones**, **Branch-and-Bound** con cota inferior admisible alcanza el óptimo global explorando solo el **1,76%** del espacio en **199,7 ms**, reduciendo la penalización compuesta `f(x)` entre **42,4% y 60,0%** y eliminando entre **66,7% y 100%** de las ventanas horarias. **Recocido Simulado**, por su parte, resuelve en ~22–29 ms constantes.

Para validar fuera de instancias propias, evaluamos **80 perfiles estudiantiles reales** de tres datasets internacionales **ITC-2019** (Masaryk y Yachay Tech). Dentro de los perfiles factibles, nuestra optimización reduce `f(x)` entre **17,2% y 32,8%** pareado, baja ventanas hasta **44,7%** y certifica infactibilidad hasta **24,6 veces más rápido**. Como extensión experimental, implementamos además un planificador global de campus que con `H2 = 0` y capacidad física respetada reduce conflictos estudiantiles entre **39,7% y 77,4%** en menos de 4 segundos."

---

#### Slide 11 · Cumplimiento OE1–OE7, Limitaciones y Futuro (`0:55` · `10:05–11:00`)
> **Cue visual:** Mostrar los 5 verdes arriba y los 2 amarillos abajo en la tabla izquierda, luego señalar los puntos clave de la derecha.

"En síntesis de cumplimiento, cinco de los siete objetivos específicos (**OE1 a OE5**) están cumplidos con evidencia ejecutable en el repositorio, y dos (**OE6 y OE7**) tienen estado parcial claramente delimitado.

Declaramos cuatro limitaciones con total transparencia: primero, la infraestructura Terraform y el CI/CD OIDC están completos y validados, pero el aprovisionamiento en una cuenta AWS productiva está pendiente; segundo, el protocolo de usabilidad **SUS** (`n ≥ 30`) está diseñado, pero falta aplicarlo en terreno; tercero, el glosario de 50 conceptos está acotado a ciencias básicas e ingeniería; y cuarto, el planificador global de campus es un asistente táctico que asigna el **89%–91%** de las clases, sin sustituir un ERP maestro como UniTime. Nuestro trabajo futuro inmediato apunta precisamente a ejecutar el piloto AWS + SUS, integrar SAML/OIDC con Banner UNAB y restringir apoyo LLM solo a la zona gris de convalidación."

---

#### Slide 12 · Cierre y Preguntas (`0:30` · `11:00–11:30`)
> **Cue visual:** Mirar a toda la comisión; señalar brevemente las 4 cifras clave y el comando `docker compose up --build`.

"Para cerrar, SIGA-DSS entrega evidencia verificable sobre cuatro resultados concretos: **0 ciclos** en 10 mallas UNAB identificando que `TDFI102` bloquea el 52,1% de nuestra carrera; **F1 = 0,957** determinista en convalidaciones; hasta **60% menos penalización** y **cero topes** en UCTP validado hasta en ITC-2019; y **69 pruebas automatizadas** en verde. Todo es reproducible localmente con un comando `docker compose up --build`. Muchas gracias, quedamos atentos a las preguntas de la comisión."

---

## 3. Banco de Respuestas Rápidas para Preguntas de la Comisión (Q&A)

### 1. ¿Por qué no usar un LLM comercial o embeddings de OpenAI directamente para convalidaciones?
**Respuesta sugerida (~30 s · Maximiliano):**  
"Evaluamos la complejidad operacional de usar LLMs directos: tienen latencia variable, costo por token, riesgo de alucinación al distinguir niveles cercanos como *Cálculo I* vs. *Cálculo II*, y restricciones de privacidad bajo la **Ley 21.719** al enviar antecedentes estudiantiles a APIs externas. En cambio, nuestro motor híbrido es **100% determinista, auditable y corre en 752 ms locales** alcanzando **F1 = 0,957** y **Top-3 = 1,000**. Además, dejamos explícito como trabajo futuro acotar el apoyo de LLM únicamente a la **zona gris (`0,25 ≤ S < 0,45`)** para desambiguar los pocos casos fronterizos."

### 2. ¿No existe riesgo de sobreajuste al haber calibrado 50 conceptos sobre un *Gold Standard* de 112 ramos?
**Respuesta sugerida (~30 s · Maximiliano):**  
"Para descartar sobreajuste diseñamos tres pruebas independientes: primero, **ablación con 0 conceptos**, donde el núcleo léxico Dice-IDF más penalización de nivel ya alcanza **F1 = 0,774** y **Top-3 = 0,986**; segundo, **validación cruzada Leave-One-University-Pair-Out (LOPO)** calibrando el umbral en dos pares y evaluando a ciegas el tercero, donde logra **F1 = 0,964**; y tercero, **LOPO con poda estricta**, eliminando del diccionario cualquier concepto exclusivo del par de prueba, sosteniendo **F1 = 0,925**. Por rigor, declaramos que no generaliza automáticamente a salud o derecho sin extender el glosario."

### 3. ¿Por qué la tasa de perfiles factibles en ITC-2019 es solo 10% a 35% (`yach-fal17` 3/30)?
**Respuesta sugerida (~30 s · Maximiliano):**  
"Es una distinción metodológica clave que documentamos en la Sección 5.3.2: la tasa de factibilidad depende de la rigidez del perfil inscrito por el estudiante al discretizar bloques continuos de 5 minutos de UniTime hacia la grilla fija de **20 módulos UNAB** tomando hasta 3 candidatos temporales por clase. Como `H1 = 0` es inviolable, ni la línea base aleatoria ni *Simulated Annealing* inventan soluciones donde los bloques colisionan; por eso resuelven exactamente los mismos `9/30`, `7/20` y `3/30` perfiles. Lo que demuestra la mejora algorítmica es la comparación **pareada dentro de los factibles**: `-17,2% a -32,8%` en `f(x)` y hasta `24,6×` más velocidad al podar ramas infactibles."

### 4. ¿El planificador global de campus (`campus.py`) puede reemplazar el sistema oficial de programación de salas de la UNAB?
**Respuesta sugerida (~25 s · Maximiliano / Felipe):**  
"No, y lo delimitamos explícitamente como un **asistente táctico de unidad académica**. Garantiza `H2 = 0` en salas, `H3 = 0` en docentes, capacidad física y restricciones `NotOverlap` reduciendo conflictos estudiantiles entre **39,7% y 77,4%**, asignando entre **89,2% y 90,8%** de las clases en menos de 4 segundos. Pero no incluye cadenas de Kempe multi-salto para forzar el 100%, ni matrices de tiempo de traslado entre campus, ni calendarios semanales heterogéneos propios de un ERP corporativo como UniTime."

### 5. ¿Por qué quedaron pendientes el despliegue vivo en AWS y la prueba de usabilidad SUS?
**Respuesta sugerida (~25 s · Felipe / José Ignacio):**  
"Desde la formulación de E1 separamos explícitamente el *Track Operativo* del *Track de Extensión Operacional*. Toda la infraestructura Terraform —VPC, ECS Fargate, RDS SSL, S3 OAC, WAFv2 y despliegue OIDC— está implementada y validada sintácticamente con `terraform validate`, replicando localmente la misma topología en Docker Compose. No se ejecutó el `apply` vivo por no contar con una cuenta institucional AWS asignada ni aprobación de presupuesto de hosting. De igual modo, el protocolo **SUS** con 4 tareas cronometradas (Anexo A) está listo para aplicarse en piloto con `n ≥ 30` estudiantes y secretaría académica."

### 6. ¿Cómo aseguran aislamiento multi-tenant y cumplimiento real de la Ley 21.719?
**Respuesta sugerida (~25 s · Felipe):**  
"Cada organización opera como *tenant* aislado: en `estres-malla` cualquier consulta cruzada entre organizaciones retorna **HTTP 404** verificada por test automático; los tokens JWT de `suite-sso` viajan en cookie `HttpOnly` firmada y se validan por audiencia y rol RBAC sin consultar la BD central. Respecto a **Ley 21.719**, toda solicitud de convalidación exige consentimiento explícito, valida RUT con módulo 11, deja rastro en `EventoAuditoria`, fija retención a **730 días** y ejecuta `purgar_datos_vencidos` para anonimizar datos personales conservando estadísticas académicas."

### 7. ¿Qué faltaría para llevar SIGA-DSS a producción real dentro de la UNAB?
**Respuesta sugerida (~25 s · José Ignacio / Felipe):**  
"Tres integraciones acotadas sobre la arquitectura ya construida: primero, conectar `core` al proveedor de identidad UNAB (**Azure AD / SAML 2.0 / OIDC**) migrando los tokens internos a firma asimétrica **RS256/JWKS**; segundo, reemplazar la carga manual de planillas Excel por un ETL programado o vista API desde **Banner**; y tercero, aprovisionar la cuenta AWS con los módulos Terraform ya escritos para ejecutar el piloto **SUS** y seguimiento longitudinal."
