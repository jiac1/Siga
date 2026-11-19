# UNIVERSIDAD ANDRÉS BELLO
**Facultad de Ingeniería · Escuela de Informática**  
**Carrera de Ingeniería Civil Informática**  
**Asignatura:** INTEGRADOR II: SEM LIC EN CS (CINF200)  
**Semestre:** Segundo Semestre 2026  

---

# SIGA-DSS: SISTEMA DE SOPORTE A LA DECISIÓN MODULAR PARA LA OPTIMIZACIÓN DE TRAYECTORIAS CURRICULARES Y GESTIÓN DE CAPACIDAD ACADÉMICA

**Informe Final Consolidado en Formato Paper (Evaluación Final E3 · Integración E1 + E2 + E3)**  
**Autores:** Felipe Riquelme Salvo · José Ignacio Amar · Maximiliano Alonso Vargas  
**Profesor Guía:** Jorge Humberto Sabattin Ortega  
**Institución:** Facultad de Ingeniería, Universidad Andrés Bello, Santiago de Chile  
**Fecha:** Noviembre de 2026  

---

## Resumen

La sobreduración académica y la deserción en ingeniería en Chile constituyen problemas estructurales con un impacto financiero superior a \$1.100 millones de dólares por cohorte quinquenal; en particular, Ingeniería Civil en Computación e Informática registra una duración real de 13,8 semestres frente a una duración nominal de 10 a 11 semestres (2,91 semestres en exceso). Bajo la hipótesis de que una fracción sustantiva de este fenómeno deriva de opacidad institucional, cuellos de botella curriculares y procesos manuales fragmentados, este trabajo diseña, implementa y evalúa **SIGA-DSS**, un Sistema de Soporte a la Decisión (DSS) web modular en ciclo cerrado que unifica cinco herramientas académicas tras un gateway único y autenticación federada sin estado (`suite-sso`, JWT HS256): (1) visualizador interactivo de mallas como Grafos Dirigidos Acíclicos (DAG), (2) análisis de estrés curricular (*MallaIQ*) basado en *Curricular Analytics*, (3) motor híbrido de convalidaciones asistido por recuperación de información y diccionario semántico curado, (4) mapa de calor espacial de salas sobre planillas Banner/Syaproa y (5) motor combinatorio de horarios (*University Course Timetabling Problem*, UCTP) con auditoría de conflictos y optimización de ventanas.

La evaluación técnica verificable demuestra: (a) **0 ciclos** en las 10 mallas oficiales de Ingeniería UNAB (486 asignaturas, 570 aristas), identificando cuantitativamente que *Introducción a la Programación* (`TDFI102`, $b=25, d=7, c=32$) bloquea el 52,1% del plan de Ingeniería Civil Informática ($C(G)=492$); (b) una mejora del motor de convalidación en ciencias básicas e ingeniería sobre un *Gold Standard* de 112 asignaturas en tres pares universitarios reales desde $F_1 = 0,029$ (línea base) y $F_1 = 0,429\text{--}0,455$ (alternativas semánticas LSA/SVD y *char n-grams* sin diccionario) hasta **$F_1 = 0,957$** ($\text{IC}_{95\%}: [0,919; 0,987]$, $P=0,944$, $R=0,971$, $\text{Top-3}=1,000$) en 752 ms, sosteniendo **$F_1 = 0,964$** en validación cruzada *Leave-One-Pair-Out* (**$F_1 = 0,925$** al podar conceptos exclusivos del par de prueba); (c) en el módulo UCTP, **100% de cumplimiento de restricciones duras ($H_1=0$)**, detección determinista de colisiones de sala ($H_2$) y docente ($H_3$), una reducción de **42,4% a 60,0%** en penalización blanda (**66,7% a 100%** en ventanas horarias) en instancias UNAB de hasta 202.500 combinaciones, una reducción pareada de **17,2% a 32,8%** en $f(x)$ (**25,7% a 44,7%** en ventanas) dentro de los perfiles factibles de tres benchmarks estándar **ITC-2019** (`muni-fi-spr16`, `muni-fsps-spr17` y `yach-fal17`), y un planificador global experimental de campus ($H_2=0$, capacidad, `NotOverlap`) que reduce conflictos estudiantiles entre **39,7% y 77,4%**; y (d) **69 pruebas automatizadas** en verde en CI/CD junto con controles formales de ciberseguridad y protección de datos (Ley 21.719). Se reconocen explícitamente como limitaciones vigentes el aprovisionamiento en vivo en AWS, la aplicación en campo del protocolo SUS, la especificidad disciplinar del glosario de ingeniería y la frontera entre el planificador global experimental y un ERP institucional completo.

**Palabras clave:** *Sistema de Soporte a la Decisión (DSS), Curricular Analytics, Grafos Dirigidos Acíclicos (DAG), Convalidación de Asignaturas, Optimización Combinatoria (UCTP), Microservicios, Arquitectura Modular.*

---

## Abstract

Academic over-duration and student attrition in Chilean engineering programs represent structural challenges costing over \$1.1 billion USD per five-year cohort; specifically, Computer Engineering averages 13.8 real semesters against a nominal duration of 10–11 semesters (2.91 excess semesters). Hypothesizing that a critical share of this delay stems from institutional opacity, curriculum bottlenecks, and fragmented manual workflows, this paper designs, implements, and evaluates **SIGA-DSS**, a closed-loop modular web Decision Support System (DSS) integrating five academic applications behind a unified reverse-proxy gateway and stateless Single Sign-On (`suite-sso`, JWT HS256): (1) an interactive Directed Acyclic Graph (DAG) curriculum visualizer, (2) a curriculum stress analyzer (*MallaIQ*) implementing *Curricular Analytics*, (3) a hybrid credit-transfer matching engine combining TF-IDF retrieval, a curated concept taxonomy, and human-in-the-loop precedents, (4) a stateless classroom utilization heatmap over Banner/Syaproa exports, and (5) a combinatorial *University Course Timetabling Problem* (UCTP) optimizer with hard-constraint auditing and idle-gap minimization.

Reproducible technical evaluation confirms: (a) **0 cycles** across all 10 official UNAB Engineering curricula (486 courses, 570 prerequisite edges), showing that *Introduction to Programming* (`TDFI102`, $b=25, d=7, c=32$) blocks 52.1% of Computer Engineering ($C(G)=492$); (b) a credit-transfer matching leap in engineering and basic sciences on a 112-course expert *Gold Standard* across three real university pairs from baseline $F_1 = 0.029$ and dense/sub-word baselines ($F_1 = 0.429\text{--}0.455$ via LSA/SVD and character $n$-grams) to **$F_1 = 0.957$** (95% Bootstrap CI: $[0.919, 0.987]$, $P=0.944$, $R=0.971$, $\text{Top-3}=1.000$) in 752 ms, maintaining **$F_1 = 0.964$** under *Leave-One-Pair-Out* cross-validation (**$F_1 = 0.925$** with test-pair-exclusive concepts pruned); (c) **100% hard-constraint feasibility ($H_1=0$)**, deterministic room ($H_2$) and faculty ($H_3$) conflict auditing, **42.4%–60.0% soft-penalty reduction** (**66.7%–100%** idle-gap reduction) on UNAB instances up to 202,500 combinations, **17.2%–32.8% paired $f(x)$ reduction** (**25.7%–44.7%** idle-gap reduction) within feasible student profiles across three standard **ITC-2019** benchmarks (`muni-fi-spr16`, `muni-fsps-spr17`, `yach-fal17`), plus an experimental campus-wide planner reducing student co-enrollment conflicts by **39.7%–77.4%**; and (d) **69 automated tests** passing in CI/CD alongside verified cybersecurity and data-privacy controls (Chilean Law 21.719). Current limitations are transparently bounded to live AWS provisioning, field execution of the SUS usability protocol, domain specificity of the engineering concept taxonomy, and the scope boundary between the experimental campus scheduler and a full institutional ERP solver.

**Keywords:** *Decision Support System (DSS), Curricular Analytics, Directed Acyclic Graphs (DAG), Credit Transfer Matching, University Course Timetabling Problem (UCTP), Microservices, Modular Suite Architecture.*

---

## 1. Introducción y Formulación del Problema

### 1.1. Diagnóstico Cuantitativo y Costo Institucional

El proceso formativo en la educación superior chilena, particularmente en carreras de ingeniería civil, enfrenta un rezago estructural persistente caracterizado por deserción tardía, sobreduración acumulada e ineficiencia en la asignación de infraestructura docente. De acuerdo con las estadísticas oficiales del **Servicio de Información de Educación Superior (SIES)** del Ministerio de Educación de Chile en su informe de *Duración Real y en Exceso de Carreras de Pregrado* (SIES, 2023):

* **Ingeniería Civil en Computación e Informática** registra una **duración real promedio de 13,8 semestres**, frente a una duración formal nominal de 10 a 11 semestres, equivalente a una **sobreduración media de 2,91 semestres** por egresado.
* En programas tecnológicos afines (*Ingeniería en Informática*), la duración en exceso alcanza **3,45 semestres**.
* En contextos equivalentes a nivel nacional, como el Departamento de Ingeniería Informática (DIINF) de la Universidad de Santiago de Chile (USACH), la deserción de primer año en Ingeniería Civil Informática fue de **28,0% en 2017** y **21,9% en 2018**, pero **hacia el tercer año se eleva a casi el 50%**, concentrando la mayor pérdida de estudiantes en etapas intermedias y tardías (Bello et al., 2020).

Esta ineficiencia produce un costo financiero y social severo: en Chile, la deserción estudiantil de primer año representa un costo directo anual estimado entre **\$128 y \$141 millones de dólares** para las instituciones de educación superior; en una ventana quinquenal, las cohortes desertoras implican una pérdida acumulada superior a **\$1.100 millones de dólares** en aranceles no devengados y subsidios de gratuidad perdidos (González & Uribe, 2018; SIES, 2023). Para los estudiantes y sus familias, exceder la duración nominal acarrea la extinción de la gratuidad o becas estatales, precipitando sobreendeudamiento o desvinculación en etapas avanzadas de la carrera.

En el plano operativo local de la **Facultad de Ingeniería de la Universidad Andrés Bello (UNAB)**, existía un conjunto valioso pero **fragmentado** de herramientas creadas desde la secretaría académica (mallas estáticas, scripts de horarios, planillas de salas, análisis aislados de reprobación y pre-evaluación de convalidaciones), operando sin autenticación unificada, sin contratos de datos compartidos, sin pruebas automatizadas y sin optimización algorítmica transversal.

### 1.2. Hipótesis Central

> **Hipótesis del Proyecto:**  
> *"La deserción universitaria, el retraso académico y la sobreduración en carreras de ingeniería no obedecen de forma exclusiva a factores individuales o socioeconómicos del estudiante, sino que están significativamente determinados por fallas de diseño estructural y opacidad institucional: la pérdida de avance en procesos manuales de convalidación, la existencia de puntos de estrés curricular (prerrequisitos rígidos y asignaturas cuello de botella) y la carencia de herramientas integradas de auditoría y planificación horaria. Consecuentemente, unificar dichas capacidades bajo un Sistema de Soporte a la Decisión (DSS) modular, auditable y basado en algoritmos reproducibles permite diagnosticar cuellos de botella, acelerar convalidaciones con alta precisión y generar horarios libres de topes con ventanas mínimas, sentando las bases cuantitativas para mitigar el rezago académico."*

### 1.3. Objetivos del Proyecto

#### Objetivo General
Diseñar, implementar y evaluar técnicamente **SIGA-DSS**, un Sistema de Soporte a la Decisión (DSS) web modular que integre bajo una arquitectura desacoplada, un gateway unificado e inicio de sesión único las aplicaciones de apoyo curricular y logístico para la Facultad de Ingeniería de la Universidad Andrés Bello —malla interactiva DAG, análisis de estrés curricular, convalidación asistida por IA, mapa de calor de salas y generador combinatorio de horarios (UCTP)— con contenerización reproducible e infraestructura como código orientada a AWS, a fin de aportar evidencia cuantitativa y soporte operativo para reducir la sobreduración y optimizar la capacidad académica.

#### Objetivos Específicos
1. **OE1 · Auditoría y Formalización:** Auditar y formalizar los modelos de datos, formatos de planillas institucionales (Banner/Syaproa) y requerimientos operativos de las herramientas preexistentes en la Facultad de Ingeniería UNAB.
2. **OE2 · Arquitectura Modular Unificada:** Diseñar e implementar una arquitectura de suite modular desacoplada (inspirada en el modelo *Creative Suite/Cloud*) con tokens de diseño transversales, barra compartida (`suite-bar`), licenciamiento multi-institución, gateway único y paquete SSO criptográfico (`suite-sso`).
3. **OE3 · Grafos Curriculares y *Curricular Analytics*:** Formalizar las 10 mallas oficiales UNAB como Grafos Dirigidos Acíclicos (DAG), verificando aciclicidad y computando métricas estructurales de bloqueo $b(v)$, retraso $d(v)$, complejidad $c(v)$ y estrés combinado en *MallaIQ*.
4. **OE4 · Motor Híbrido de Convalidaciones:** Implementar, calibrar y validar un motor de equivalencia curricular entre universidades chilenas y la UNAB que supere $F_1 \ge 0,90$ sobre un *Gold Standard* experto con trazabilidad *human-in-the-loop*.
5. **OE5 · Optimización Combinatoria de Horarios (UCTP):** Formular e implementar un motor de generación de horarios que garantice restricciones duras (cero topes $H_1$, auditoría de salas $H_2$ y docentes $H_3$) y minimice restricciones blandas (ventanas horarias, días activos, jornada y sobrecarga) comparando métodos exactos y metaheurísticos.
6. **OE6 · Contenerización e Infraestructura Cloud (AWS):** Diseñar y automatizar la infraestructura reproducible local (Docker Compose) y en la nube AWS mediante Terraform (VPC, ECS Fargate, RDS PostgreSQL, S3, CloudFront, ALB, WAF, OIDC) con CI/CD.
7. **OE7 · Evaluación Técnica y Diseño de Validación UX:** Validar integralmente el sistema mediante pruebas automatizadas, benchmarks de algoritmos, auditoría de ciberseguridad/eficiencia y diseño formal del protocolo de evaluación de usabilidad (SUS).

### 1.4. Estrategia de Alcance

El proyecto adoptó desde su formulación una separación explícita entre el **Track Operativo** (plataforma SIGA-DSS completa, integrada, contenerizada, con pruebas automatizadas y evaluación técnica reproducible) y el **Track de Extensión Científica / Operacional** (comparativa modular de algoritmos UCTP, aprovisionamiento en cuenta productiva AWS y estudios longitudinales de usabilidad y retención con usuarios reales).

---

## 2. Estado del Arte y Fundamentación Teórica

### 2.1. Convalidaciones y Pérdida de Avance Curricular
La evidencia internacional reporta que en procesos de transferencia y admisión especial los estudiantes pierden entre el **34% y el 43%** de los créditos previamente aprobados debido a evaluaciones manuales, lentas y heterogéneas (Government Accountability Office [GAO], 2017). Más críticamente, Monaghan & Attewell (2015) demostraron que quienes logran convalidar $\ge 90\%$ de sus créditos previos presentan **2,5 veces mayor probabilidad de graduarse** ($\text{Odds Ratio} = 2,5$) frente a quienes pierden más de la mitad de su carga académica. Automatizar la pre-evaluación con trazabilidad documental y precedentes institucionales ataca directamente esta fricción.

### 2.2. *Curricular Analytics* y Cuellos de Botella
El marco formal de *Curricular Analytics* (Heileman et al., 2018) modela un plan de estudios como un Grafo Dirigido Acíclico $G = (V, E)$ donde las aristas representan prerrequisitos formales. Dos métricas determinan la fragilidad estructural de cada curso $v \in V$: el **Factor de Bloqueo $b(v)$** (cantidad de cursos posteriores directa o indirectamente dependientes de $v$) y el **Factor de Retraso $d(v)$** (longitud del camino dirigido más largo que contiene a $v$). Slim et al. (2016) establecieron empíricamente que un aumento de 20 puntos en la complejidad estructural curricular $C(G) = \sum_{v \in V} (b(v) + d(v))$ reduce en **3,74%** la probabilidad de titulación oportuna. En Chile, Salazar-Fernández et al. (2021) evidenciaron que el **76,21%** de los desertores tardíos abandonan adeudando ramos formalmente clasificados como cuellos de botella tras casi 9 semestres de permanencia improductiva. Complementariamente, Bello et al. (2020), mediante selección de variables con *Random Forest* sobre 40 atributos en cohortes de Ingeniería Civil Informática en Chile ($n=206$), identificaron que **6 de los 7 factores con mayor poder discriminante de abandono corresponden a indicadores académicos del primer semestre** (índice académico, promedio ponderado, eficiencia semestral y tasa de aprobación), pesando sustancialmente más que el quintil de ingreso familiar.

### 2.3. Herramientas de Auditoría Curricular (*Degree Audit*)
La adopción de plataformas de auditoría de avance y trayectorias guiadas incrementa la tasa de titulación oportuna en **17 puntos porcentuales** (Jenkins & Bailey, 2017) y reduce la proporción de titulados con créditos excedentes desde un **30% hasta un 5%** (Complete College America [CCA], 2018).

### 2.4. Problema de Planificación Horaria Universitaria (UCTP)
El *University Course Timetabling Problem* (UCTP) constituye un problema clásico de optimización combinatoria $\mathcal{NP}$-difícil (Schaerf, 1999; Burke et al., 2007), estructurado en **restricciones duras** (inviolables para la factibilidad: ausencia de choques de estudiante, sala y docente) y **restricciones blandas** (calidad pedagógica y logística: minimización de ventanas horarias, compacidad semanal, balance diario y preferencias de jornada). Mientras instancias acotadas a nivel semestral admiten búsqueda exacta informada (*Branch-and-Bound* con ordenamiento *Minimum Remaining Values* — MRV y poda por cota inferior admisible), instancias de mayor combinatoria se abordan eficazmente mediante metaheurísticas de trayectoria como *Simulated Annealing* (Kirkpatrick et al., 1983).

### 2.5. Modelo de Suite Modular y Comparativa con Soluciones Existentes
Adoptando el paradigma de modularidad de *Adobe Creative Suite/Cloud*, cada aplicación conserva valor autónomo (operable en modo *standalone* o integrado) mientras comparte autenticación, diseño visual, catálogos y licenciamiento por institución. La Tabla 1 contrasta SIGA-DSS frente a los paradigmas existentes.

| Paradigma | Ejemplos | Fortalezas | Limitaciones frente al enfoque SIGA-DSS |
| :--- | :--- | :--- | :--- |
| **ERP Institucionales** | Banner (Ellucian), PeopleSoft, SAP | Registro oficial de notas, matrícula y actas consolidadas. | Interfaces rígidas, nula simulación *what-if*, sin *Curricular Analytics* ni optimización de ventanas UCTP. |
| **Plataformas LMS** | Canvas, Blackboard, Moodle | Gestión de aula, evaluaciones y comunicación por curso. | Visión aislada por asignatura; no modelan grafos de prerrequisitos ni capacidad física de campus. |
| **Scripts Ad-hoc Estudiantiles** | Simuladores en GitHub, planillas locales | Agilidad puntual para visualizar horarios básicos. | Sin respaldo institucional, sin SSO/RBAC, sin auditoría de salas/docentes ni pruebas automatizadas. |
| **LLMs Generales Aislados** | Consultas directas a ChatGPT o Claude | Flexibilidad lingüística para comparar textos libres. | Desconectados del catálogo oficial, no deterministas, propensos a alucinaciones y sin persistencia ni Ley 21.719. |
| **SIGA-DSS** | **Esta propuesta** | **Ciclo cerrado demanda–oferta, motores deterministas reproducibles ($F_1=0,957$, B&B/SA UCTP), SSO/RBAC, multi-tenant y Ley 21.719.** | **Requiere integración institucional directa con Banner y validación longitudinal en campo.** |

---

## 3. Metodología y Diseño Experimental

### 3.1. Enfoque de Ingeniería y Gestión del Proyecto

El desarrollo siguió una metodología iterativa orientada a sistemas de ingeniería de software con componentes analíticos y algorítmicos:

* **Diseño Guiado por Dominio (DDD) y Módulos Profundos:** Separación estricta de fronteras entre identidad/catálogo/convalidaciones/UCTP (`services/core`), analítica espacial sin estado (`services/mapa-calor`), analítica de estrés multi-institución (`services/estres-malla`), librería criptográfica compartida (`packages/suite-sso`) y front-end estático desacoplado (`services/portal`).
* **Ingeniería Basada en Evidencia y Líneas Base Empíricas:** Tanto el motor de convalidaciones como el motor UCTP se compararon cuantitativamente contra sus respectivas líneas base originales antes de consolidarse.
* **Integración Continua (CI/CD):** Pipeline automatizado en GitHub Actions (`.github/workflows/ci.yml`) que ejecuta análisis estático y formato (`ruff check` / `ruff format`), suite completa de pruebas `pytest` en los 4 paquetes/servicios, compuertas de regresión algorítmica (`evaluar_motor.py --min-f1 0.90` y `evaluar_uctp.py`) y validación sintáctica de infraestructura (`terraform validate`).

![Cronograma de Hitos y Trazabilidad SIGA-DSS (Agosto – Noviembre 2026)](docs/img/gantt_cronograma.png)

### 3.2. Conjuntos de Datos Verificables y Líneas Base

Todos los experimentos se ejecutan sobre artefactos versionados dentro del repositorio:

1. **Catálogo Oficial UNAB (Visualización DAG y *Curricular Analytics*):** **10 mallas oficiales** de la Facultad de Ingeniería UNAB (`services/portal/shared/mallas/*.json`), sumando **486 asignaturas** y **570 aristas** de prerrequisito auditadas.
2. **Base de Convalidación UNAB (Destino):** **9 carreras destino** (`data/unab/base-convalidacion.json`) con **400 asignaturas** (**257 códigos únicos**), contenidos programáticos y aprendizajes esperados estructurados.
3. **Catálogo Curricular Nacional (Origen):** **27 mallas curriculares** de **11 universidades chilenas** (PUC, UA, UAH, UANDES, UCHILE, UDD, UDP, UFT, UMAYOR, USACH y USM) con **1.582 asignaturas** transcritas desde fuentes públicas trazables (`data/universidades/fuentes.csv`).
4. **Glosario de Conceptos Curriculares:** Diccionario semántico curado con **50 conceptos disciplinares** y reglas de expresiones regulares (`data/convalidacion/conceptos.json`, versión `2026-10-21`).
5. **Conjunto Etiquetado (*Gold Standard*) de Convalidación:** **112 asignaturas** etiquetadas en 3 pares reales (`data/convalidacion/evaluacion/gold.json`):
   * USACH Ing. Civil Informática $\rightarrow$ UNAB Ing. Civil Informática ($n=38$: 25 positivos, 13 negativos).
   * UCHILE Ing. Civil en Computación $\rightarrow$ UNAB Ing. Civil Informática ($n=32$: 17 positivos, 15 negativos).
   * USACH Ing. Civil Industrial $\rightarrow$ UNAB Ing. Civil Industrial ($n=42$: 27 positivos, 15 negativos).
   * **Línea base (*baseline*):** Motor original de recuperación solo por similitud de contenidos textuales sobre nombres cortos ($F_1 = 0,029$, $R = 0,014$).
6. **Benchmark Combinatorio UCTP (Instancias UNAB + Estándar Internacional ITC-2019):**
   * *Suite sintética UNAB:* 4 instancias deterministas representativas de programación académica UNAB (módulos M1–M14, actividades `TEO`+`LAB`, espacios entre **256 y 202.500 combinaciones**, incluyendo instancia con colisiones inyectadas de sala $H_2$ y docente $H_3$), más validación E2E en navegador sobre `horarios_prueba.xlsx` y `malla_horarios_prueba.xlsx`.
   * *Benchmarks externos ITC-2019:* 3 instancias reales oficiales de la *International Timetabling Competition 2019* (`data/benchmarks/itc2019/`, obtenidas del repositorio oficial UniTime/DTU): **Masaryk Univ. Informática** (`muni-fi-spr16`: 228 cursos, 574 clases, 35 salas, 1.543 estudiantes), **Masaryk Univ. Cs. del Deporte** (`muni-fsps-spr17`: 226 cursos, 519 clases, 44 salas, 865 estudiantes) y **Yachay Tech Pregrado** (`yach-fal17`: 91 cursos, 415 clases, 33 salas, 821 estudiantes), evaluando perfiles reales de 3 a 8 asignaturas inscritos por estudiantes reales.
   * **Línea base (*baseline*):** Backtracking MRV con selección aleatoria de secciones sin función de penalización de ventanas.

### 3.3. Métricas, Criterios de Aceptación y Protocolo SUS Diseñado

Se definieron criterios cuantitativos verificables en cuatro dimensiones:
* **Algoritmos/IA:** Convalidación $F_1 \ge 0,90$ (bloqueante en CI), $\text{Top-3} \ge 0,95$; DAG $Cycle(G) = \emptyset$ en el 100% de las 10 mallas UNAB; UCTP 100% factibilidad ($H_1=0$), 100% detección de conflictos $H_2/H_3$ y mejora estricta de $f(x)$ y ventanas frente a línea base aleatoria.
* **Calidad:** 100% de pruebas unitarias e integración en verde, 0 errores de linter (`ruff`), paridad de despliegue local en 1 comando (`docker compose up --build`).
* **Ciberseguridad:** Rechazo de tokens alterados/expirados/`alg=none`, cookies `HttpOnly`, protección *Open Redirect*, aislamiento multi-tenant, recálculo server-side, rate limiting y anonimización conforme a Ley 21.719.
* **Eficiencia:** Evaluación de 112 asignaturas $< 1.500\text{ ms}$; optimización UCTP en instancias semestrales $< 500\text{ ms}$; verificación SSO $< 1\text{ ms}$; validación DAG de 10 mallas $< 100\text{ ms}$.
* **Protocolo de Usabilidad (SUS — Diseñado, pendiente de ejecución en campo):** Se estructuró el instrumento estandarizado *System Usability Scale* (Brooke, 1996; 10 ítems escala Likert 1–5, umbral objetivo $\ge 70$ puntos) acompañado de 4 tareas guiadas cronometradas (ver Anexo A). Su aplicación con cohorte estudiantil queda documentada explícitamente como validación de campo pendiente.

---

## 4. Arquitectura y Solución Tecnológica (SIGA-DSS)

### 4.1. Sistema de Soporte a la Decisión en Ciclo Cerrado

SIGA-DSS articula los módulos en un ciclo cerrado entre la **Gestión Curricular (Demanda Pedagógica)** —trayectoria DAG, diagnóstico de estrés y convalidaciones— y la **Gestión de Capacidad (Oferta Operativa)** —ocupación espacial de salas y optimización combinatoria de horarios— bajo un gateway unificado.

![Arquitectura del Sistema de Soporte a la Decisión (DSS) en Ciclo Cerrado](docs/img/dss_ciclo_cerrado.png)

### 4.2. Arquitectura de Contenedores (Modelo C4) y Decisiones de Diseño

La topología implementa paridad exacta entre el entorno local (`docker-compose.yml` con gateway Nginx en `:8080`) y la arquitectura declarada en AWS Terraform (`infra/terraform/` con CloudFront + ALB + ECS Fargate + RDS PostgreSQL 16 + S3).

![Modelo C4: Diagrama de Contenedores de la Plataforma SIGA-DSS](docs/img/c4_contenedores.png)

Las decisiones arquitectónicas clave responden a cuatro pilares de calidad:
1. **Desacoplamiento por Microservicios y Licenciamiento Comercial:** Cada aplicación Django (`core`, `mapa-calor`, `estres-malla`) mantiene configuración, dependencias, pruebas y despliegue independientes; los front-ends estáticos (`malla`, `horarios`, `convalidacion`, `siga`) se sirven desde el portal sin acoplarse al ciclo de vida del backend. Cada servicio opera tanto en `SUITE_MODE=suite` (integrado con SSO) como en `standalone`.
2. **Autenticación Federada Sin Estado (`packages/suite-sso`):** El servicio `core` emite la cookie `suite_sso` firmada con JWT **HMAC-SHA256** (`iss="suite-unab-core"`, `aud="suite-unab"`, `exp`, `iat`, `sub`, `organizacion`, `roles`, `modulos`), exigiendo un secreto mínimo de 32 caracteres. Los demás servicios verifican la firma y las licencias vigentes localmente sin consultas síncronas a la base de datos de `core`, evitando puntos únicos de cuello de botella.
3. **Resiliencia y Protección de Datos (Ley 19.628 / Ley 21.719):** En `core`, el flujo de convalidación exige consentimiento explícito, valida RUT mediante algoritmo módulo 11, registra eventos inmutables en `EventoAuditoria`, fija fecha de retención (`eliminar_desde = +730 días`) y dispone del comando automatizado `purgar_datos_vencidos` (programable vía AWS EventBridge a las 04:00 UTC) que anonimiza datos personales preservando los precedentes académicos estadísticos.
4. **Infraestructura como Código (Terraform AWS) con Paridad Local:** El directorio `infra/terraform/` declara una VPC en 2 zonas de disponibilidad (subredes públicas, privadas y de datos aisladas), Endpoint Gateway S3, RDS PostgreSQL 16 cifrado con `rds.force_ssl=1` y rotación en Secrets Manager, ECS Fargate con *Circuit Breaker* de rollback automático y autoescalado por CPU, CloudFront con *Origin Access Control* (OAC) y cabecera secreta `X-Origen-Suite` validada en el ALB, AWS WAFv2 opcional y despliegue OIDC sin credenciales estáticas (`.github/workflows/desplegar.yml`).

### 4.3. Pipeline ETL y Modelamiento Real de Datos

El flujo de ingestión transforma resoluciones oficiales y mallas externas en catálogos estructurados validados topológicamente:

![Pipeline de Transformación y Normalización de Datos (ETL)](docs/img/pipeline_etl.png)

El esquema relacional implementado en el código fuente se organiza por dominio acotado:
* **Servicio `core` — App `identidad` (`services/core/identidad/models.py`):** `Organizacion` (tenant multi-institución y dominios de correo permitidos), `Usuario` (`AbstractUser` con correo como `USERNAME_FIELD` y roles `superadmin`, `admin_institucion`, `staff`, `docente`, `estudiante`), `Modulo`, `Licencia` (contratos por institución con vigencia temporal y plan `piloto`/`estandar`/`suite`) y `EventoAuditoria`.
* **Servicio `core` — App `catalogo` (`services/core/catalogo/models.py`):** `Universidad`, `Carrera` (con trazabilidad `fuente_url`, `fuente_consultada`, `fuente_metodo`) y `Asignatura` (código, semestre, créditos, contenidos y aprendizajes esperados JSON).
* **Servicio `core` — App `convalidaciones` (`services/core/convalidaciones/models.py`):** `Solicitud` (folio `CV-*`, datos personales sujetos a retención `eliminar_desde`, estado y verificación de certificado), `Item` (nota, sugerencia del motor, fuente `motor` o `precedente`, decisión final) y `Equivalencia` (base de precedentes aprobados por la Dirección de Carrera).
* **Servicio `estres-malla` (`services/estres-malla/malla/models.py`):** `Organization` y `User` (aislamiento multi-tenant), `Carrera` (con umbrales configurables verde/amarillo/naranjo: 85%/70%/55%), `Asignatura` y `AnalisisMalla` (respaldo de archivos o slug del catálogo compartido, HTML generado y estadísticas).
* **Servicio `mapa-calor` (`services/mapa-calor/heatmap/procesador.py`):** Arquitectura estrictamente sin estado (*stateless*, sin base de datos) que parsea planillas Banner/Syaproa en memoria y entrega la matriz web más el libro `.xlsx` descargable.

### 4.4. Formulación Algorítmica Implementada

#### 4.4.1. Grafos Curriculares (DAG) y *Curricular Analytics* (`estres-malla/malla/engine.py`, `test_mallas_dag.py`)
Cada malla se formaliza como $G = (V, E)$, donde $(u, v) \in E$ indica que $u$ es prerrequisito de $v$. La aciclicidad ($Cycle(G) = \emptyset$) se certifica en $\mathcal{O}(|V| + |E|)$ mediante orden topológico de Kahn y DFS de tres estados. Sobre el orden topológico se computan exactamente las métricas de Heileman et al. (2018):

$$b(v) = |\{w \in V \mid \exists\text{ camino dirigido } v \rightsquigarrow w\}|$$

$$d(v) = L_{\text{hasta}}(v) + L_{\text{desde}}(v) - 1, \qquad c(v) = b(v) + d(v), \qquad C(G) = \sum_{v \in V} c(v)$$

donde $L_{\text{hasta}}(v)$ y $L_{\text{desde}}(v)$ son las longitudes máximas de caminos entrantes y salientes calculadas por programación dinámica en $\mathcal{O}(|V| + |E|)$. Al cruzar la topología con las tasas reales de reprobación de actas en *MallaIQ*, el sistema calcula el **índice de estrés combinado**:

$$e(v) = c(v) \cdot \left(1 - \frac{\text{aprob}(v)}{100}\right)$$

permitiendo priorizar asignaturas que simultáneamente bloquean la malla y presentan alta reprobación histórica.

#### 4.4.2. Motor Híbrido de Convalidaciones (`services/core/convalidaciones/motor.py`)
Implementado con paridad exacta entre servidor y cliente, el motor unifica dos modos operativos y una capa de precedentes institucionales:

1. **Similitud sobre Contenidos (TF-IDF Global + Cobertura de Términos Clave):** Cada asignatura destino UNAB pondera su nombre $3\times$ junto a sus contenidos tras normalización, eliminación de *stop-words* curriculares y *stemming* conservador de plurales del español. Sobre el IDF global del catálogo UNAB se computa el coseno TF-IDF ($\cos$) y la cobertura ($\text{cov}$) de los 12 términos más discriminantes ($\text{IDF} \ge \text{mediana}$):
   $$S_{\text{cont}}(q, a) = \text{cov}(q, a) + \bigl(1 - \text{cov}(q, a)\bigr) \cdot \cos(\vec{v}_q, \vec{v}_a)$$
2. **Alineación Semántica y Léxica por Nombre (Modo Catálogo):** Cuando el postulante selecciona asignaturas desde el catálogo nacional sin adjuntar syllabus PDF, el motor combina el diccionario curado de 50 conceptos (`conceptos.json`), la similitud de **coeficiente de Dice ponderado por IDF** ($S_{\text{Dice}}$) y la señal de contenido ($S_{\text{cont}}$):
   $$S_{\text{concepto}} = \begin{cases} 0,90 + 0,10 \cdot S_{\text{Dice}} & \text{si } \mathcal{C}(q) \cap \mathcal{C}(a) \neq \emptyset \\ 0 & \text{en otro caso} \end{cases}, \qquad S_{\text{texto}} = 0,70 \cdot S_{\text{Dice}} + 0,30 \cdot S_{\text{cont}}$$
   $$S_{\text{bruto}} = \max\bigl(S_{\text{cont}},\; S_{\text{concepto}},\; S_{\text{texto}}\bigr)$$
3. **Penalización de Nivel y Clasificación por Umbrales:** Si se detectan niveles romanos o arábigos finales distintos (por ejemplo, *Cálculo I* vs. *Cálculo II* o *Inglés I* vs. *Inglés II*), el puntaje se penaliza multiplicándolo por $\lambda_{\text{nivel}} = 0,60$. La clasificación opera con $\tau_{\text{convalidable}} = 0,45$ y zona de revisión manual $\tau_{\text{rev}} = 0,25$ ($0,35$ en modo solo nombre).
4. **Prioridad de Precedentes (*Human-in-the-Loop*):** Cualquier par previamente aprobado por la Dirección de Carrera en la tabla `Equivalencia` prevalece automáticamente ($S = 1,00$, `fuente = "precedente"`) por sobre la inferencia estadística.

#### 4.4.3. Motor de Optimización Combinatoria UCTP (`services/core/horarios/motor.py` y `uctp-solver.js`)
Para completar integralmente el módulo de horarios (OE5) con paridad cliente–servidor y API REST (`/core/api/v1/horarios/optimizar`), el problema UCTP se formaliza sobre el conjunto de asignaturas $K$ del semestre y sus opciones de cobertura exacta de actividades (`TEO`, `AYU`, `LAB`, `TAL`) libres de choques internos:

* **Restricciones Duras ($H_1, H_2, H_3$):**
  * $H_1$ (inviolable en generación): para todo par de cursos elegidos $c_i \neq c_j$, sus conjuntos de bloques $(d, m)$ son estrictamente disjuntos ($\text{slots}(x_i) \cap \text{slots}(x_j) = \emptyset$).
  * $H_2$ y $H_3$ (auditoría determinista de la oferta): detección automática de toda tupla `(sala_física, día, módulo)` o `(RUT_docente, día, módulo)` asignada a más de un NRC simultáneamente, ignorando salas virtuales o por definir.
* **Función Objetivo de Restricciones Blandas ($f(x)$):**
  $$f(x) = w_1 \cdot W(x) + w_2 \cdot D(x) + w_3 \cdot P(x) + w_4 \cdot B(x)$$
  con pesos calibrados $w_1 = 3,0$ (ventanas horarias $W(x)$: módulos libres intermedios entre el primer y último bloque de cada día por banda diurna M1–M14 / vespertina M15–M20), $w_2 = 2,0$ (días activos en campus $D(x)$), $w_3 = 1,5$ (bloques fuera de la jornada preferida $P(x)$: mañana M1–M6, tarde M7–M14 o vespertino M15–M20) y $w_4 = 1,0$ (exceso de carga diaria $B(x)$ sobre 6 módulos/día).
* **Algoritmos Implementados:**
  1. **Línea Base Aleatoria:** Backtracking MRV con barajado de candidatos.
  2. **Branch-and-Bound con Cota Inferior Admisible:** Ordenamiento MRV (*Minimum Remaining Values*), exploración de opciones por costo incremental y poda mediante cota inferior matemáticamente admisible:
     $$LB(\text{parcial}) = w_1 \cdot \max\bigl(0,\; W_{\text{actual}} - S_{\text{restante}}\bigr) + w_2 \cdot D_{\text{actual}} + w_3 \cdot P_{\text{actual}} + w_4 \cdot B_{\text{actual}}$$
     donde $S_{\text{restante}}$ es el máximo de bloques que podrían aportar los cursos aún no asignados (acotando el máximo número de huecos potencialmente rellenables). Esta propiedad garantiza que **ningún óptimo global es podado erróneamente**.
  3. **Recocido Simulado (*Simulated Annealing*):** Búsqueda local estocástica que parte de una asignación factible MRV y ejecuta movimientos de vecindario de 1 curso (80%) y 2 cursos simultáneos (20%) preservando estrictamente $H_1 = 0$, con criterio de aceptación de Metropolis $\exp(-\Delta / T)$ y enfriamiento geométrico ($T_0 = 12,0$, $\alpha = 0,996$, 2.500 iteraciones).
  4. **Vacantes sin Tope:** Verificación combinatoria de qué NRCs pueden pertenecer al menos a un horario semestral factible para calcular la capacidad real efectiva por asignatura.

---

## 5. Resultados y Evaluación Técnica Verificable

Todos los resultados de esta sección fueron ejecutados y verificados directamente mediante los scripts reproducibles `scripts/evaluacion/evaluar_suite.py`, `evaluar_motor.py`, `evaluar_uctp.py`, `pytest` y Playwright sobre la versión vigente del repositorio (Anexo B).

### 5.1. Evaluación del Motor de Convalidación Asistido por IA

Dado que el *Gold Standard* comprende **112 asignaturas** (69 positivos, 43 negativos) en tres pares universitarios de ingeniería y ciencias básicas, la evaluación mediante `scripts/evaluacion/evaluar_motor.py` incorpora: (1) comparación contra dos alternativas semánticas sin diccionario manual (*Latent Semantic Analysis* / Truncated SVD $k=32$ y *Character $n$-gram* TF-IDF de 3 a 5 gramas); (2) ablación del diccionario de conceptos (`0 conceptos`); (3) **intervalos de confianza Bootstrap no paramétricos al 95%** ($B=2.000$ réplicas); (4) **separación estricta entre calibración y evaluación** mediante validación cruzada *5-Fold Stratified* y *Leave-One-University-Pair-Out* (LOPO, tanto con glosario completo como podando cualquier concepto exclusivo del par de prueba); y (5) análisis de sensibilidad frente al umbral de decisión $\tau \in [0,25; 0,60]$.

| Escenario / Variante Evaluada | Umbral $\tau$ | $n$ (Pos/Neg) | TP / FP | Precisión | Exhaustividad | **$F_1$-Score ($\text{IC}_{95\%}$)** | Especif. | Top-3 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Línea base** (TF-IDF solo contenidos) | 0,45 | 112 (69/43) | 1 / 0 | 1,000 | 0,014 | **0,029** ($[0,000; 0,090]$) | 1,000 | 0,913 |
| **Semántica densa LSA / SVD ($k=32$)** | 0,38* | 112 (69/43) | 38 / 70 | 0,352 | 0,551 | **0,429** ($[0,331; 0,531]$) | 0,093 | 0,913 |
| **Sub-léxica Char $n$-gram (3–5 gramas)** | 0,18* | 112 (69/43) | 23 / 9 | 0,719 | 0,333 | **0,455** ($[0,333; 0,577]$) | 0,884 | 0,942 |
| **Ablación léxica** (Dice-IDF + nivel, 0 conceptos) | 0,45 | 112 (69/43) | 48 / 7 | 0,873 | 0,696 | **0,774** ($[0,687; 0,853]$) | 0,907 | 0,986 |
| **Motor híbrido producción** (global) | **0,45** | **112 (69/43)** | **67 / 4** | **0,944** | **0,971** | **0,957 ($[0,919; 0,987]$)** | **0,907** | **1,000** |
| **Validación 5-Fold Stratified CV** (*out-of-sample*) | $\tau^*_{\text{train}}$ | 112 (69/43) | 66 / 3 | 0,957 | 0,957 | **0,957** ($\mu=0,956 \pm 0,033$) | 0,930 | 1,000 |
| **Validación LOPO CV** (3 pares retenidos) | $\tau^*_{\text{train}}$ | 112 (69/43) | 66 / 2 | 0,971 | 0,957 | **0,964** ($F_1 \in [0,941; 0,980]$) | 0,953 | 1,000 |
| **Validación LOPO CV + Poda de Conceptos** | $\tau^*_{\text{train}}$ | 112 (69/43) | 62 / 3 | 0,954 | 0,899 | **0,925** ($F_1 \in [0,898; 0,971]$) | 0,953 | 1,000 |
| ↳ Par 1: USACH Civil Inf $\rightarrow$ UNAB Civil Inf | 0,45 | 38 (25/13) | 25 / 2 | 0,926 | 1,000 | **0,962** (LOPO podado: **0,898**) | 0,846 | 1,000 |
| ↳ Par 2: UCHILE Civil Comp $\rightarrow$ UNAB Civil Inf | 0,45 | 32 (17/15) | 17 / 1 | 0,944 | 1,000 | **0,971** (LOPO podado: **0,971**) | 0,933 | 1,000 |
| ↳ Par 3: USACH Civil Ind $\rightarrow$ UNAB Civil Ind | 0,45 | 42 (27/15) | 25 / 1 | 0,962 | 0,926 | **0,943** (LOPO podado: **0,920**) | 0,933 | 1,000 |

![Evaluación Estadística del Motor de Convalidación sobre Gold Standard](docs/img/fig_eval_convalidacion.png)

* **Descomposición del Desempeño y Comparación con Alternativas Semánticas:** En consultas de catálogo compuestas únicamente por el título corto de la asignatura de origen (2 a 5 palabras), los modelos vectoriales densos sin supervisión (`LSA/SVD k=32`, $F_1=0,429$) sufren alta tasa de falsos positivos (especificidad $0,093$) al proyectar ramos distintos de una misma área (p. ej., *Cálculo I* vs. *Cálculo II* o *Física General* vs. *Física Moderna*) hacia el mismo subespacio latente, mientras que `Char n-gram TF-IDF` ($F_1=0,455$) captura raíces morfológicas pero falla ante sinónimos curriculares (*Intro. a la Programación* vs. *Fundamentos de Computación*). La ablación demuestra que el **núcleo léxico Dice-IDF con penalización explícita de nivel romano/arábigo aporta la mayor ganancia estructural** ($\Delta F_1 = +0,745$, llegando a **$F_1 = 0,774$** y **$\text{Top-3} = 0,986$** sin usar un solo concepto manual), mientras que el diccionario curado de 50 conceptos aporta el salto complementario ($\Delta F_1 = +0,183$, hasta **$0,957$**) al resolver equivalencias terminológicas propias del dominio.
* **Separación Calibración/Evaluación y Generalización entre Universidades (LOPO CV):** Al calibrar el umbral $\tau^*$ en 2 pares universitarios y evaluar a ciegas en el 3.er par retenido, el motor alcanza **$F_1 = 0,964$**. Más aún, en la prueba estricta **LOPO con poda de conceptos** —donde se eliminan del diccionario todos los conceptos que no se activen en los 2 pares de entrenamiento (conservando solo 30–35 de los 50 conceptos)— el desempeño fuera de muestra se mantiene en **$F_1 = 0,925$** ($P=0,954, R=0,899, \text{Top-3}=1,000$), confirmando que el motor generaliza entre mallas de ingeniería de distintas universidades chilenas y no depende de sobreajuste al par evaluado. Aun así, dado el tamaño muestral ($n=112$) y la especialización del glosario en ciencias básicas e ingeniería, **no se afirma generalización directa a otras disciplinas (salud, derecho o humanidades)** sin extender la taxonomía conceptual.
* **Sensibilidad al Umbral $\tau$:** El barrido $\tau \in [0,25; 0,60]$ (Panel B de la figura) demuestra una meseta de alta estabilidad en todo el rango $\tau \in [0,40; 0,60]$, donde $F_1$ permanece entre **$0,918$ y $0,963$** ($\tau=0,40 \rightarrow F_1=0,918$; $\tau=0,45 \rightarrow F_1=0,957$; $\tau=0,50 \rightarrow F_1=0,957$; $\tau=0,55 \rightarrow F_1=0,963$; $\tau=0,60 \rightarrow F_1=0,955$). El punto operativo $\tau = 0,45$ maximiza la exhaustividad ($0,971$) manteniendo una especificidad superior al 90% ($0,907$).
* **Análisis de los 6 Errores Residuales en $\tau = 0,45$ (5,4% del conjunto):**
  * *4 Falsos Positivos:* *Bases de Datos Avanzadas* $\rightarrow$ `TDFI103` (0,479), *Proyecto de Ingeniería de Software* $\rightarrow$ `PTEC105` (0,678), *Proyecto de Software* $\rightarrow$ `PTEC105` (0,512) y *Física Moderna* $\rightarrow$ `CFIS310` (0,501), producto de cursos avanzados/electivos que comparten núcleo léxico con el curso troncal.
  * *2 Falsos Negativos:* *Introducción a la Innovación* $\rightarrow$ `ACAD101` (0,332) y *Análisis de Decisiones* $\rightarrow$ `CIND212` (0,225); en ambos casos **el ramo UNAB correcto aparece en el Top-3 sugerido** (`Top-3 = 1,000`).
* **Latencia Medida:** La evaluación productiva de las 112 asignaturas toma **752,0 ms** (~6,7 ms por asignatura), sin costos ni dependencia de APIs externas.

### 5.2. Evaluación de *Curricular Analytics* (DAG) sobre las 10 Mallas Oficiales UNAB

La Tabla 3 reporta las métricas estructurales reales obtenidas en **16,1 ms** sobre las 10 mallas de la Facultad de Ingeniería UNAB (`services/portal/shared/mallas/*.json`).

| Carrera (Facultad de Ingeniería UNAB) | $\|V\|$ Ramos | $\|E\|$ Aristas | Períodos | Ciclos | Complejidad $C(G)$ | $c_{\text{prom}}$ | Ramo más Crítico ($b / d / c$) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| Ingeniería Civil | 55 | 81 | 11 | 0 | **1.076** | 19,56 | `FMMP012` Intro. Matemáticas ($36 / 11 / 47$) |
| Ingeniería Civil Industrial 2.0 | 67 | 78 | 15 | 0 | **1.007** | 15,03 | `FMMV012` Intro. Matemáticas ($33 / 11 / 44$) |
| Ingeniería en Construcción | 50 | 48 | 10 | 0 | **582** | 11,64 | `FMMP012` Intro. Matemáticas ($21 / 9 / 30$) |
| Ingeniería Civil Industrial | 51 | 68 | 10 | 0 | **552** | 10,82 | `FMMP012` Intro. Matemáticas ($32 / 9 / 41$) |
| **Ingeniería Civil Informática** | **48** | **61** | **10** | **0** | **492** | **10,25** | **`TDFI102` Intro. Programación ($25 / 7 / 32$)** |
| Ingeniería Civil Eléctrica | 49 | 44 | 10 | 0 | **488** | 9,96 | `FMMP012` Intro. Matemáticas ($25 / 9 / 34$) |
| Ing. en Automatización y Robótica | 43 | 62 | 8 | 0 | **478** | 11,12 | `TDFI102` Intro. Programación ($25 / 7 / 32$) |
| Ingeniería Civil en Minas | 49 | 54 | 10 | 0 | **465** | 9,49 | `ICMI121` Geología I ($23 / 8 / 31$) |
| Ing. en Computación e Informática | 40 | 45 | 8 | 0 | **332** | 8,30 | `TDFI102` Intro. Programación ($19 / 7 / 26$) |
| Ingeniería Industrial | 34 | 29 | 8 | 0 | **192** | 5,65 | `FMMA015` Fund. Matemáticas ($14 / 5 / 19$) |
| **Total / Promedio Facultad (10 mallas)** | **486** | **570** | **—** | **0** | **5.664** | **11,65** | — |

![Diagnóstico Curricular Analytics (DAG) en la Facultad de Ingeniería UNAB](docs/img/fig_curricular_analytics.png)

En el caso focal de **Ingeniería Civil Informática (Plan 12210)**, el análisis revela dos cadenas críticas convergentes: la **línea de programación y computación** encabezada por `TDFI102` (*Introducción a la Programación*, S1, $b=25, d=7, c=32$, bloqueando el **52,1%** de la carrera) y `PTEC101` (*Algoritmos y Estructuras de Datos*, S3, $b=22, d=7, c=29$), y la **línea matemática** encabezada por `FMMP012` (*Introducción a las Matemáticas*, S1, $b=14, d=8, c=22$) y `FMMP112` (*Cálculo Diferencial*, S2, $b=12, d=8, c=20$), que constituyen el camino crítico de mayor profundidad ($d=8$ semestres).

### 5.3. Evaluación del Motor Combinatorio de Horarios (UCTP)

#### 5.3.1. Instancias Representativas UNAB y Auditoría $H_2/H_3$

La Tabla 4 reporta el benchmark reproducible ejecutado mediante `scripts/evaluacion/evaluar_uctp.py` comparando la línea base aleatoria contra *Branch-and-Bound* y *Simulated Annealing* en cuatro instancias escaladas.

| Instancia (Espacio Combinatorio) | Algoritmo | Factibles ($H_1=0$) | $f(x)$ | $\Delta f(x)$ vs. Base | Ventanas ($W$) | Días ($D$) | Exc. Carga | Nodos (Podados) | Tiempo (ms) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Pequeña** (4 ramos TEO · 256) | Aleatorio (base) | 5/5 | 37,0 | — | 6 | 5 | 0 | 25 (0) | 0,56 |
| | **Branch & Bound** | **5/5** | **20,0** | **-45,9%** | **2 (-66,7%)** | **4** | **0** | 155 (2) | 7,53 |
| | Recocido Simulado | 5/5 | 20,0 | -45,9% | 2 (-66,7%) | 4 | 0 | 2.505 (0) | 28,78 |
| **Mediana** (5 ramos TEO+LAB · 7.040) | Aleatorio (base) | 5/5 | 78,0 | — | 16 | 5 | 2 | 40 (0) | 1,08 |
| | **Branch & Bound** | **5/5** | **40,0** | **-48,7%** | **4 (-75,0%)** | **5** | **0** | 663 (13) | 46,79 |
| | Recocido Simulado | 5/5 | 40,0 | -48,7% | 6 (-62,5%) | 5 | 0 | 2.510 (0) | 28,16 |
| **Grande** (6 ramos TEO+LAB · 202.500) | Aleatorio (base) | 5/5 | 40,0 | — | 8 | 5 | 6 | 35 (0) | 1,40 |
| | **Branch & Bound** | **5/5** | **16,0** | **-60,0%** | **2 (-75,0%)** | **5** | **0** | 3.564 (490) | 199,69 |
| | Recocido Simulado | 5/5 | 18,0 | -55,0% | 0 (-100%) | 4 | 10 | 2.507 (0) | 22,55 |
| **Auditada** (5 ramos + $H_2/H_3$ · 3.840) | Aleatorio (base) | 5/5 | 33,0 | — | 4 | 5 | 2 | 30 (0) | 0,81 |
| | **Branch & Bound** | **5/5** | **19,0** | **-42,4%** | **0 (-100%)** | **5** | **0** | 416 (8) | 26,08 |
| | Recocido Simulado | 5/5 | 21,0 | -36,4% | 0 (-100%) | 4 | 4 | 2.506 (0) | 23,62 |

![Benchmark del Motor Combinatorio UCTP](docs/img/fig_benchmark_uctp.png)

* **Hallazgos Clave:** *Branch-and-Bound* alcanza el óptimo exacto en todas las instancias explorando únicamente el **1,76%** del espacio en la instancia grande (3.564 nodos de 202.500 combinaciones en 199,7 ms) gracias a MRV y a la cota inferior admisible. *Simulated Annealing* demuestra un tiempo casi constante (**22,6–28,8 ms**, casi **9× más rápido** en la instancia grande), reduciendo ventanas a cero a cambio de concentrar mayor carga diaria (trade-off multi-objetivo explícito en $f(x)$).
* **Auditoría $H_2/H_3$ y Verificación E2E en Navegador:** La instancia auditada detectó exactamente el conflicto de sala ($H_2=1$) y el conflicto de docente ($H_3=1$) inyectados. Adicionalmente, una prueba E2E con Chromium/Playwright sobre `services/portal/apps/horarios/index.html` cargando `horarios_prueba.xlsx` y `malla_horarios_prueba.xlsx` generó 8 horarios libres de topes (`0 ventanas`, `2 días activos`, $f(x)=4,0$, `0 conflictos H2/H3`) con **0 errores de consola JavaScript**.

#### 5.3.2. Validación Externa sobre Benchmarks Estándar ITC-2019

Para verificar la capacidad de generalización más allá de instancias sintéticas propias, se evaluaron los tres algoritmos mediante `scripts/evaluacion/evaluar_itc2019.py` sobre **80 perfiles estudiantiles reales** (3 a 8 cursos) extraídos de tres datasets oficiales de la *International Timetabling Competition 2019* (`muni-fi-spr16`, `muni-fsps-spr17` y `yach-fal17`), mapeando los bloques de 5 minutos y hasta tres candidatos temporales de menor penalización por clase al dominio modular de SIGA-DSS.

| Dataset ITC-2019 (Cursos · Clases · Perfiles) | Algoritmo | Factibles ($H_1=0$) | $f(x)$ Prom. | $\Delta f(x)$ vs. Base | Ventanas Prom. | $\Delta W$ vs. Base | Tiempo Prom. (ms) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Masaryk Univ. · Informática** (`muni-fi-spr16`) · 228 cursos · 574 clases · $n=30$ | Aleatorio (base) | 9/30 (30,0%) | 26,11 | — | 5,22 | — | 152,97 |
| | **Branch & Bound** | 8/30 (26,7%) | **19,25** | **-26,3%** | **3,38** | **-35,2%** | 104,31 |
| | Recocido Simulado | **9/30 (30,0%)** | 21,22 | -18,7% | 3,67 | -29,7% | **86,55** |
| **Masaryk Univ. · Cs. Deporte** (`muni-fsps-spr17`) · 226 cursos · 519 clases · $n=20$ | Aleatorio (base) | 7/20 (35,0%) | 28,71 | — | 6,71 | — | 1.288,54 |
| | **Branch & Bound** | **7/20 (35,0%)** | **19,29** | **-32,8%** | **3,71** | **-44,7%** | 574,05 |
| | **Recocido Simulado** | **7/20 (35,0%)** | **19,29** | **-32,8%** | **3,71** | **-44,7%** | **502,44** |
| **Yachay Tech · Pregrado** (`yach-fal17`) · 91 cursos · 415 clases · $n=30$ | Aleatorio (base) | 3/30 (10,0%) | 52,33 | — | 11,67 | — | 2.214,94 |
| | **Branch & Bound** | **3/30 (10,0%)** | **43,33** | **-17,2%** | **8,67** | **-25,7%** | **89,89** |
| | **Recocido Simulado** | **3/30 (10,0%)** | **43,33** | **-17,2%** | **8,67** | **-25,7%** | 108,44 |

![Evaluación Externa UCTP sobre Benchmarks Estándar ITC-2019](docs/img/fig_benchmark_itc2019.png)

Para interpretar con rigor metodológico la Tabla de ITC-2019, es indispensable distinguir **tres dimensiones ortogonales** del experimento:

1. **Tasa de Factibilidad Estructural del Perfil (`% Factibles`, $H_1=0$) vs. Optimización de $f(x)$:** Una reducción en la penalización blanda $f(x)$ mide la mejora de calidad **dentro de los perfiles que admiten horario libre de topes**, pero no incrementa por sí misma la proporción de perfiles factibles. Las tasas de factibilidad observadas —**30,0%** en `muni-fi-spr16` (`9/30`), **35,0%** en `muni-fsps-spr17` (`7/20`) y **10,0%** en `yach-fal17` (`3/30`)— están determinadas por la rigidez intrínseca de las demandas reales de los estudiantes al discretizar bloques continuos de 5 minutos (con hasta tres candidatos temporales por clase) a la grilla fija de 20 módulos de SIGA-DSS. Por ello, la línea base aleatoria y *Recocido Simulado* hallan solución exactamente para los mismos perfiles factibles (`9/30`, `7/20` y `3/30`). En `muni-fi-spr16`, *Branch-and-Bound* resuelve **8/30 (26,7%)** debido al truncamiento preventivo en `max_nodos = 20.000` sobre un noveno perfil de alta ramificación.
2. **Calidad de las Soluciones Factibles (Comparación Pareada Estricta vs. Subconjunto Completo):**
   * En `muni-fsps-spr17` ($n=7$ factibles comunes) y `yach-fal17` ($n=3$ factibles comunes), los tres algoritmos resuelven exactamente el mismo subconjunto de perfiles: tanto *Branch-and-Bound* como *Recocido Simulado* reducen de forma idéntica la penalización $f(x)$ en **-32,8%** ($28,71 \rightarrow 19,29$) y **-17,2%** ($52,33 \rightarrow 43,33$), y las ventanas horarias en **-44,7%** ($6,71 \rightarrow 3,71$) y **-25,7%** ($11,67 \rightarrow 8,67$).
   * En `muni-fi-spr16`, al evaluar de forma **estrictamente pareada sobre los 8 perfiles factibles comunes** a los tres métodos, la línea base promedia $f(x)=24,00$ y $W=4,88$, mientras que **tanto *Branch-and-Bound* como *Recocido Simulado* alcanzan exactamente el mismo óptimo: $f(x)=19,25$ (-19,8% pareado) y $W=3,38$ (-30,7% pareado)**. El noveno perfil adicional resuelto por la línea base ($f=43,0, W=8$) y por *Recocido Simulado* ($f=37,0, W=6$) posee mayor carga intrínseca, lo que explica que el promedio sobre 9 perfiles de SA sea $21,22$ (-18,7% respecto a los $26,11$ de la línea base en $n=9$) frente a $19,25$ de B&B sobre $n=8$.
3. **Tiempo de Ejecución y Poda de Infactibilidad:** En instancias altamente restringidas donde el 90% de los perfiles carece de solución sin tope (`yach-fal17`), el backtracking aleatorio agota su búsqueda explorando ramas estériles (**2.214,94 ms** en promedio), mientras que el ordenamiento MRV y la poda de *Branch-and-Bound* certifican infactibilidad o hallan el óptimo en **89,89 ms** (**24,6× más rápido**) y *Recocido Simulado* en **108,44 ms**.

#### 5.3.3. Extensión Experimental: Planificación Global de Campus (*Master Timetabling*) sobre ITC-2019

Mientras que el solver de la Subsección 5.3.1–5.3.2 opera en **tiempo real (< 1 s)** para que un estudiante arme su horario sobre una oferta ya publicada, `services/core/horarios/campus.py` y los endpoints asíncronos `/core/api/v1/horarios/campus/planificar` + `trabajos/<uuid>` (`TrabajoPlanificacionCampus`) implementan un **planificador global experimental de unidad académica** con presupuesto configurable de hasta **300 segundos** y **notificación automática por correo** al término. La evaluación mediante `scripts/evaluacion/evaluar_campus_itc2019.py` sobre los tres campus ITC-2019 (garantizando $H_2=0$, capacidad física respetada y restricciones binarias duras `NotOverlap` / `SameAttendees`) muestra mejoras consistentes frente a la asignación constructiva aleatoria:

| Campus ITC-2019 (Clases · Salas · Estudiantes) | Algoritmo | Clases Asignadas | $H_2$ / Cap. / Dist. | Conflictos Est. ($\Delta$) | Objetivo Global ($\Delta$) | Tiempo (ms) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **Masaryk Univ. · Informática** (`muni-fi-spr16`) · 574 clases · 35 salas · 1.543 est. | Aleatorio (base) | 501/574 (87,3%) | 0 / 0 / 0 | 10.949 | 62.758,0 | 90,6 |
| | **Global MRV + SA** | **521/574 (90,8%)** | **0 / 0 / 0** | **6.602 (-39,7%)** | **41.982,0 (-33,1%)** | 3.910,6 |
| **Masaryk Univ. · Cs. Deporte** (`muni-fsps-spr17`) · 519 clases · 44 salas · 865 est. | Aleatorio (base) | 447/519 (86,1%) | 0 / 0 / 0 | 5.437 | 47.415,0 | 68,0 |
| | **Global MRV + SA** | **470/519 (90,6%)** | **0 / 0 / 0** | **1.227 (-77,4%)** | **27.271,0 (-42,5%)** | 695,2 |
| **Yachay Tech · Pregrado** (`yach-fal17`) · 415 clases · 33 salas · 821 est. | Aleatorio (base) | 352/415 (84,8%) | 0 / 0 / 0 | 6.985 | 46.522,0 | 135,0 |
| | **Global MRV + SA** | **370/415 (89,2%)** | **0 / 0 / 0** | **2.802 (-59,9%)** | **29.012,0 (-37,6%)** | 956,9 |

En los tres campus, la combinación de constructivo MRV con reubicación 1-a-1 (*bumping*), *swap* de pares y *Simulated Annealing* global eleva las clases asignadas sin colisión a **89,2%–90,8%** y reduce los **conflictos estudiantiles agregados entre 39,7% y 77,4%** en **0,70 s a 3,91 s**. Como se delimita en la Sección 6.2, este módulo constituye un **asistente táctico de planificación de facultad** (y cuenta con adaptador directo `construir_campus_desde_secciones` para planillas Banner/Syaproa), sin pretender sustituir un motor ERP institucional completo de *timetabling* corporativo.

### 5.4. Calidad de Software, Pruebas Automatizadas y Reproducibilidad

La Tabla 5 detalla la cobertura de pruebas automatizadas verificada localmente y en CI (`pytest`).

| Paquete / Servicio | Tests | Cobertura Funcional y de Seguridad Validada | Estado |
| :--- | :---: | :--- | :---: |
| `packages/suite-sso` | 6 | Firma JWT HS256, expiración, rechazo de otra audiencia, rechazo `alg=none`, longitud mínima secreto (≥32 chars). | ✅ 6/6 |
| `services/core` (Identidad & Convalid.) | 24 | Login SSO `HttpOnly`, RBAC por rol, licencias parciales/vencidas, *Open Redirect*, validación RUT mod-11, recálculo server-side, precedentes, purga Ley 21.719. | ✅ 24/24 |
| `services/core` (Motor IA & DAG) | 9 | Stemming/tokenización, conceptos, simetría Dice-IDF, umbral CI ($F_1 \ge 0,85$/$0,90$), aciclicidad y cascada en las 10 mallas UNAB. | ✅ 9/9 |
| `services/core` (Motor UCTP, Campus & API) | 13 | Auditoría $H_2/H_3$, B&B vs. fuerza bruta, SA, vacantes sin tope, modo disjunto, API `/horarios/optimizar`, solver global de campus (`H2=0`, `H3=0`, capacidad, `NotOverlap`) y API asíncrona `/horarios/campus/planificar` con envío de correo. | ✅ 13/13 |
| `services/mapa-calor` | 6 | Salud *stateless*, parseo Banner/Syaproa `.xlsx`, rechazo extensiones inválidas, exigencia SSO y licencia en modo suite. | ✅ 6/6 |
| `services/estres-malla` | 11 | Multi-tenant isolation (404 cross-org), *Open Redirect*, catálogo JSON, sincronización dinámica de rol SSO, cálculo exacto $b(v), d(v), c(v)$ y detección de ciclos. | ✅ 11/11 |
| **Total Suite Automatizada** | **69** | **Pruebas unitarias, integración, seguridad, DAG, IA y optimización UCTP/Campus + Ruff 0 errores** | **✅ 69/69** |

### 5.5. Evaluación de Ciberseguridad y Privacidad

La Tabla 6 sintetiza los controles de seguridad implementados y verificados en código e infraestructura, junto con las brechas residuales identificadas con transparencia técnica.

| Dominio OWASP / Cumplimiento | Control Implementado y Verificado | Evidencia en Código / Test | Brecha Residual / Mitigación Futura |
| :--- | :--- | :--- | :--- |
| **A01 · Control de Acceso** | RBAC en 5 roles, licencias con expiración por tenant y aislamiento cross-tenant (HTTP 404). | `test_identidad.py`, `test_estres_malla.py`, `test_mapa_calor.py`. | Sin MFA nativo; delegable al IdP institucional SAML/OIDC en integración UNAB. |
| **A02 · Criptografía y Sesiones** | JWT HS256 (`iss`, `aud`, `exp`, `iat`), rechazo `alg=none`, secreto $\ge 32$ chars, cookies `HttpOnly`, `SameSite`, `Secure` y HSTS (1 año) en producción. | `packages/suite-sso/src/suite_sso/tokens.py`, `test_tokens.py`, `settings.py`. | Secreto simétrico compartido entre servicios; escalable a firmas asimétricas RS256/JWKS. |
| **A03/A04 · Integridad y Abuso** | Recálculo obligatorio de convalidaciones en servidor (cero confianza en puntajes del cliente), validación RUT mod-11, protección *Open Redirect*, DRF Throttling (`60/min` anon, `240/min` user, `10/h` solicitudes). | `convalidaciones/views.py`, `test_convalidaciones.py`, `test_identidad.py`. | Validación de tamaño/formato de Excel reforzable mediante inspección de *magic bytes* ZIP y cuotas de memoria en workers. |
| **A05 · Endurecimiento Web e IaC** | Cabeceras `X-Content-Type-Options: nosniff`, `X-Frame-Options: SAMEORIGIN`, `Referrer-Policy`; S3 bloqueo público + `Deny` sobre HTTP sin TLS + OAC; ALB restringido a CloudFront + cabecera secreta `X-Origen-Suite`; RDS `force_ssl=1` cifrado; OIDC sin llaves estáticas; ECR `scan_on_push`; WAFv2 rate-limiting opcional. | `deploy/nginx/gateway.conf`, `infra/terraform/*.tf`, `.github/workflows/desplegar.yml`. | Sin prueba de penetración (DAST) en ambiente productivo vivo al no haberse aprovisionado AWS aún. |
| **Privacidad (Ley 19.628 / 21.719)** | Consentimiento explícito obligatorio, auditoría inmutable (`EventoAuditoria`), retención a 730 días y purga/anonimización diaria automatizada. | `purgar_datos_vencidos.py`, `test_purga_anonimiza_solicitudes_vencidas`, `computo.tf`. | Requiere formalización de política de privacidad institucional y registro de encargado de datos UNAB. |

### 5.6. Eficiencia Computacional y Cumplimiento de Criterios de Aceptación

| Criterio Definido | Meta Establecida | Resultado Verificado | Estado |
| :--- | :--- | :--- | :---: |
| Calidad motor IA convalidación | $F_1 \ge 0,90$ (CI gate) | **$F_1 = 0,957$** ($P=0,944, R=0,971$, Top-3 $= 1,000$) | ✅ Cumplido |
| Latencia convalidación (112 ramos) | $< 1.500\text{ ms}$ | **752,0 ms** solo mejorado (1.095,5 ms ambas variantes) | ✅ Cumplido |
| Integridad DAG 10 mallas UNAB | $Cycle(G) = \emptyset$, $< 100\text{ ms}$ | **0 ciclos** en 10/10 mallas (**16,1 ms**) | ✅ Cumplido |
| Optimización UCTP ($H_1, H_2, H_3$ + $f(x)$) | $H_1=0$, reducción estricta $f(x)$, $< 500\text{ ms}$ | **$H_1=0$ (100%)**, $f(x)$ **-42,4% a -60,0%**, ventanas **-66,7% a -100%**, **7,5–199,7 ms** | ✅ Cumplido |
| Latencia SSO HS256 (emisión + verificación) | $< 1.000\;\mu\text{s}$ | **126,7 $\mu$s/ciclo** (~7.890 ops/s en 1 núcleo) | ✅ Cumplido |
| Procesamiento Mapa de Calor / Estrés de Malla | $< 1.000\text{ ms}$ | **267,5 ms** (`mapa-calor`) / **20,7 ms** (`estres-malla`) | ✅ Cumplido |
| Suite automatizada + Linter | 100% verde, 0 errores | **69/69 tests pasados**, **Ruff 0 errores**, E2E Chromium OK | ✅ Cumplido |
| Despliegue productivo vivo en AWS | Staging activo en cuenta AWS | IaC Terraform completa + paridad local Docker Compose; cuenta AWS pendiente | ⚠️ Parcial |
| Evaluación de usabilidad SUS (30 usuarios) | $\text{SUS} \ge 70$ en campo | Protocolo e instrumento diseñados (Anexo A); aplicación en campo pendiente | ⚠️ Pendiente |

---

## 6. Discusión Crítica e Impacto

### 6.1. Interpretación de Resultados y Contraste con Antecedentes

Los resultados empíricos respaldan la tesis de diseño estructural planteada al inicio del proyecto:

1. **Validación Local de *Curricular Analytics*:** La medición directa sobre la malla real de Ingeniería Civil Informática UNAB ($C(G)=492$) confirma cuantitativamente el mecanismo descrito por Heileman et al. (2018), Slim et al. (2016) y Salazar-Fernández et al. (2021): dos asignaturas de primer semestre —`TDFI102` ($b=25$) y `FMMP012` ($d=8$)— concentran una fracción desproporcionada del riesgo de rezago. Este hallazgo explica desde la topología del currículo la evidencia empírica de Bello et al. (2020), donde 6 de las 7 variables críticas de deserción temprana provienen del rendimiento del primer semestre: reprobar un nodo con $b=25$ colapsa de inmediato la eficiencia y el factor de progreso del estudiante. Integrar el cálculo de $b(v), d(v), c(v)$ directamente dentro de *MallaIQ* y cruzarlo con las tasas históricas de reprobación de actas (`indice_estres`) transforma esta relación en una herramienta accionable para la dirección de carrera.
2. **Eficacia de Enfoques Híbridos Deterministas frente a LLMs Aislados:** En convalidaciones, pasar de $F_1=0,029$ a $F_1=0,957$ sin llamadas a APIs externas de modelos generativos demuestra que, en dominios estructurados con taxonomía acotada, la combinación de recuperación TF-IDF, un diccionario de 50 conceptos disciplinares, Dice ponderado por IDF y penalización de nivel ofrece **determinismo, auditabilidad, latencia sub-segundo (752 ms) y costo marginal nulo**, superando las limitaciones de alucinación y privacidad de consultas directas a LLMs. A su vez, el 100% de acierto Top-3 y la capa de precedentes aprobados aseguran que el sistema asista —sin reemplazar— el criterio normativo de las comisiones académicas, abordando directamente la pérdida del 34%–43% de créditos reportada por GAO (2017) y Monaghan & Attewell (2015).
3. **Complementariedad Exacto vs. Metaheurístico en UCTP (UNAB e ITC-2019):** El benchmark UCTP evidencia empíricamente la frontera entre algoritmos exactos y metaheurísticos tanto en instancias propias como en benchmarks internacionales ITC-2019: en instancias semestrales típicas de un estudiante (4 a 6 asignaturas, hasta $\sim 2\times 10^5$ combinaciones), *Branch-and-Bound* con ordenamiento MRV y cota inferior admisible garantiza optimalidad global bajo los 200 ms, eliminando entre 66,7% y 100% de las ventanas horarias. Al validar externamente sobre 80 perfiles estudiantiles reales de Masaryk University y Yachay Tech (`muni-fi-spr16`, `muni-fsps-spr17` y `yach-fal17`), la ventaja se mantiene (**-17,2% a -32,8%** en $f(x)$, **-25,7% a -44,7%** en ventanas, y hasta **24,6×** mayor rapidez frente a la línea base), confirmando además que bajo presupuestos estrictos de nodos *Simulated Annealing* complementa a B&B al sostener la mayor cobertura de factibilidad en tiempos sub-segundo.

### 6.2. Limitaciones Reconocidas

Con rigor metodológico, se declaran cinco limitaciones objetivas del estado actual:
1. **Aprovisionamiento en Vivo en AWS:** Aunque toda la infraestructura Terraform (`infra/terraform/`) y el pipeline OIDC (`.github/workflows/desplegar.yml`) están implementados y la arquitectura se valida localmente en paridad mediante Docker Compose, el despliegue productivo en una cuenta institucional AWS no ha sido ejecutado aún.
2. **Validación Empírica con Usuarios Finales (SUS):** El instrumento SUS y los escenarios cronometrados fueron diseñados, pero no se han aplicado todavía sobre una muestra real de estudiantes y secretaría académica; por tanto, las métricas de percepción de usabilidad y reducción real de tiempos administrativos en campo permanecen pendientes.
3. **Cobertura Muestral y Disciplinar del Motor de Convalidación:** Aunque la validación cruzada *Leave-One-Pair-Out* ($F_1=0,964$ global; $F_1=0,925$ podando conceptos exclusivos del par de prueba) y la ablación sin conceptos ($F_1=0,774$) demuestran robustez fuera de muestra entre carreras de ingeniería, el *Gold Standard* ($n=112$) y el diccionario `conceptos.json` (50 conceptos) están circunscritos al dominio de ciencias básicas e ingeniería. Por tanto, los resultados no permiten afirmar que el mismo nivel de desempeño ($F_1=0,957$) se mantendrá automáticamente en facultades de salud, derecho o humanidades sin ampliar la taxonomía conceptual para esos dominios.
4. **Frontera entre el Planificador Global Experimental (`campus.py`) y un Motor Maestro Institucional (ERP):** El módulo de asignación global de campus (Subsección 5.3.3) resuelve la asignación táctica `(bloque, sala)` de una unidad académica garantizando $H_2=0$ (salas), $H_3=0$ (docentes), capacidad física y restricciones binarias `NotOverlap`/`SameAttendees`. Sin embargo, **no reemplaza un sistema ERP de *timetabling* institucional corporativo** (como UniTime o solvers MILP multi-facultad), ya que deja fuera del alcance: (a) la garantía de asignación del 100% de las secciones mediante cadenas de Kempe multi-salto o relajación jerárquica asistida (actualmente asigna el **89,2%–90,8%** bajo discretización rígida a 20 módulos UNAB, dejando ~9%–11% para resolución manual); (b) calendarios multi-semana heterogéneos (`weeks` bitmasks); (c) matrices de tiempos de traslado entre campus/edificios distantes (*travel times*); y (d) el catálogo completo de 19 restricciones de distribución y reglas contractuales docentes.
5. **Acoplamiento a Exportaciones Excel de Banner/Syaproa:** Los analizadores de *Mapa de Calor*, *Estrés de Malla* y *Horarios* dependen de la estabilidad estructural de las planillas exportadas por Banner/Syaproa (p. ej., fila 11 de encabezados en `mapa-calor`), lo que demanda pruebas de regresión ante actualizaciones del ERP.

### 6.3. Impacto en Procesos, Usuarios y Sociedad

* **Impacto en Procesos Institucionales:** Unifica herramientas dispersas bajo SSO, licenciamiento y formatos documentados; reduce la revisión inicial de convalidaciones desde búsquedas manuales repetitivas hacia sugerencias con precedente auditable; y entrega a la dirección de carrera visibilidad conjunta sobre cuellos de botella curriculares, subutilización de salas y choques $H_2/H_3$ de programación.
* **Impacto en Usuarios (Estudiantes y Postulantes):** Brinda transparencia total sobre prerrequisitos, avance en créditos y vacantes efectivas sin tope, además de horarios con menos ventanas y menor carga de desplazamiento al campus.
* **Impacto Social y Normativo:** Al orientar decisiones tempranas sobre asignaturas críticas y preservar créditos aprobados en transferencias, la plataforma contribuye al objetivo público de reducir la sobreduración (2,91 semestres en exceso) y proteger la vigencia de la gratuidad y financiamiento familiar. Asimismo, incorpora desde el diseño (*privacy by design*) consentimiento informado y anonimización periódica alineada a la nueva **Ley 21.719** de protección de datos personales en Chile.

---

## 7. Conclusiones y Trabajo Futuro

### 7.1. Respuesta Trazable a los Objetivos

| Objetivo | Estado | Evidencia Verificable |
| :--- | :---: | :--- |
| **OE1 · Auditoría y formalización** | ✅ Cumplido | Formatos Banner/Syaproa formalizados (`docs/FORMATOS_DE_ARCHIVOS.md`) y catálogos estructurados (10 UNAB + 27 externos). |
| **OE2 · Arquitectura Suite modular + SSO** | ✅ Cumplido | Monorepo con 3 microservicios Django, portal estático, `suite-sso` (JWT HS256), RBAC, multi-tenant y gateway unificado `:8080`. |
| **OE3 · Grafos DAG y** ***Curricular Analytics*** | ✅ Cumplido | 0 ciclos en 10 mallas UNAB (`test_mallas_dag.py`); cálculo de $b(v), d(v), c(v)$ e índice de estrés integrado en `estres-malla/malla/engine.py`. |
| **OE4 · Motor híbrido de convalidaciones** | ✅ Cumplido | $F_1 = 0,957$ ($\text{IC}_{95\%}: [0,919; 0,987]$, Top-3 $= 1,000$), validación LOPO CV ($F_1=0,964$; podado $0,925$), ablación y sensibilidad $\tau$ en 112 asignaturas. |
| **OE5 · Motor combinatorio UCTP** | ✅ Cumplido | `motor.py` + `campus.py` + `uctp-solver.js`: $H_1=0$, auditoría $H_2/H_3$, B&B + SA estudiante (-42% a -60% UNAB; -17,2% a -32,8% ITC-2019), campus global asíncrono (13 tests + E2E). |
| **OE6 · Contenerización e IaC AWS** | ⚠️ Parcial | Docker Compose 1-comando operativo, Terraform completo y CI/CD OIDC listos; aprovisionamiento vivo en cuenta AWS pendiente. |
| **OE7 · Evaluación técnica y UX** | ⚠️ Parcial | Evaluación técnica integral verificada (69 tests, benchmarks, validación cruzada, seguridad, eficiencia); aplicación en campo del protocolo SUS pendiente. |

### 7.2. Síntesis de Aportes

Este trabajo entrega: (1) una arquitectura reproducible y portable de suite académica multi-institución; (2) un diagnóstico cuantitativo original de complejidad curricular sobre las 10 carreras de Ingeniería UNAB; (3) un motor determinista de convalidaciones de alto desempeño en ingeniería ($F_1=0,957$, LOPO CV $F_1=0,964$) con aprendizaje institucional basado en precedentes; (4) un motor UCTP en dos niveles que combina búsqueda exacta con cota inferior admisible y recocido simulado tanto para toma de ramos estudiantil como para planificación táctica de campus; y (5) un estándar verificable de calidad, ciberseguridad y privacidad respaldado por 69 pruebas automatizadas.

### 7.3. Límites de las Afirmaciones

Los resultados presentados **acreditan desempeño algorítmico, corrección funcional, eficiencia computacional y controles de seguridad en entorno reproducible**, pero **no permiten afirmar todavía** una disminución empírica medida de las tasas de deserción ni una puntuación SUS validada con usuarios reales, fenómenos que exigen operación institucional sostenida y seguimiento longitudinal de cohortes.

### 7.4. Trabajo Futuro Pertinente

1. **Despliegue Productivo en AWS y Piloto SUS:** Provisionar el entorno `staging` mediante los manifiestos Terraform ya escritos, activar monitoreo CloudWatch/WAF y ejecutar la evaluación SUS planificada ($n \ge 30$ estudiantes y secretaría académica).
2. **Integración Institucional Nativa:** Conectar `core` con el proveedor de identidad institucional (Azure AD / SAML 2.0 / OIDC UNAB), migrar firma de tokens a **RS256/JWKS** e ingerir directamente vistas de programación y actas desde Banner vía API/ETL programado.
3. **Evolución del Motor de Convalidaciones:** Incorporar *embeddings* multilingües densos y validación asistida por LLM restringida exclusivamente a la zona gris ($0,25 \le S < 0,45$) o a diferenciación de nivel cognitivo (curso introductorio vs. avanzado) para eliminar los 4 falsos positivos detectados.
4. **Extensión UCTP a Escala Facultad:** Escalar el solver a *timetabling* maestro multi-carrera con asignación conjunta de aulas desde el *Mapa de Calor* y metaheurísticas híbridas (*Tabu Search* / programación por restricciones CP-SAT).
5. **Modelos Predictivos de Riesgo Temprano Acoplados a *MallaIQ*:** Cruzar las métricas topológicas por asignatura ($b(v), d(v), c(v)$ e índice de estrés $e(v)$) con las 6 variables académicas de primer semestre identificadas por Bello et al. (2020) mediante modelos regularizados con validación fuera de muestra (evitando el sobreajuste reportado en árboles de decisión pequeños, donde la exactitud cae de 97,21% en entrenamiento a 81,01% en prueba sobre $n=206$), a fin de medir longitudinalmente el impacto de intervenciones tempranas sobre la retención al tercer año.

---

## 8. Autoría, Contribución Individual y Declaración de Uso de IA

### 8.1. Matriz de Contribución Individual

| Integrante | Componentes y Decisiones Principales Asignadas | Evidencia / Artefactos Asociados |
| :--- | :--- | :--- |
| **Felipe Riquelme Salvo** | Arquitectura de microservicios, paquete `suite-sso`, integración Docker/Nginx, CI/CD, IaC Terraform AWS y modelado DAG de mallas. | `packages/suite-sso/`, `infra/terraform/`, `.github/workflows/`, `services/core/`, `test_mallas_dag.py`. |
| **José Ignacio Amar** | Catálogo curricular nacional (11 universidades / 27 mallas), diseño del portal estático y UI/UX compartida, calibración del *Gold Standard* y documentación base. | `data/universidades/`, `services/portal/`, `data/convalidacion/evaluacion/gold.json`. |
| **Maximiliano Alonso Vargas** | Implementación integral del módulo combinatorio UCTP (backend + API REST + solver cliente), integración de *Curricular Analytics* en *MallaIQ*, suite de evaluación integral y generación/revisión de informes y figuras consolidadas. | `services/core/horarios/`, `services/portal/apps/horarios/uctp-solver.js`, `services/estres-malla/malla/engine.py`, `scripts/evaluacion/evaluar_*.py`, `scripts/generar_*.py`, `docs/Memoria_Suite_UNAB_E1_E2_E3_Paper_Final.*`. |

### 8.2. Declaración Formal de Uso de Inteligencia Artificial

En cumplimiento de las exigencias de integridad académica y transparencia de la asignatura CINF200, los autores declaran que durante el desarrollo del proyecto y la elaboración de este informe se utilizaron asistentes de Inteligencia Artificial generativa (como GitHub Copilot y asistentes agénticos de programación) exclusivamente como **herramientas de apoyo** para:
1. Asistencia en refactorización de código, escritura de pruebas unitarias, higiene de estilo (*linting* Ruff) y depuración guiada.
2. Apoyo en estructuración redaccional, consistencia de formato académico y generación automatizada de gráficos reproducibles a partir de datos reales del repositorio.

**Control de Autoría y Verificación Humana:** Todas las decisiones de arquitectura, la formulación matemática, la curaduría del *Gold Standard*, la validación de restricciones UCTP y la interpretación crítica de resultados fueron dirigidas, revisadas y verificadas por los autores. Ninguna métrica reportada en este documento fue generada sintéticamente ni estimada por IA: el 100% de las cifras emana de la ejecución real y reproducible de `pytest`, `evaluar_motor.py`, `evaluar_uctp.py` y `evaluar_suite.py` sobre el código fuente del proyecto.

---

## 9. Referencias Bibliográficas

* Bello, F. A., Köhler, J., Hinrechsen, K., Araya, V., Hidalgo, L., & Jara, J. L. (2020). Using machine learning methods to identify significant variables for the prediction of first-year Informatics Engineering students dropout. En *2020 39th International Conference of the Chilean Computer Science Society (SCCC)* (pp. 1–5). IEEE. https://doi.org/10.1109/SCCC51225.2020.9281280
* Biblioteca del Congreso Nacional de Chile. (2024). *Ley N.º 21.719: Regula la protección y el tratamiento de los datos personales y crea la Agencia de Protección de Datos Personales*. Diario Oficial de la República de Chile.
* Brooke, J. (1996). SUS: A "quick and dirty" usability scale. En P. W. Jordan, B. Thomas, I. L. McClelland, & B. Weerdmeester (Eds.), *Usability Evaluation in Industry* (pp. 189–194). Taylor & Francis.
* Burke, E. K., McCollum, B., Meisels, A., Petrovic, S., & Qu, R. (2007). A graph-based hyper-heuristic for educational timetabling problems. *European Journal of Operational Research*, 176(1), 177–192. https://doi.org/10.1016/j.ejor.2005.08.012
* Complete College America. (2018). *Guided Pathways to Success: Boosting On-Time Graduation and Reducing Excess Credits*. Complete College America Reports.
* Cormen, T. H., Leiserson, C. E., Rivest, R. L., & Stein, C. (2022). *Introduction to Algorithms* (4th ed.). MIT Press.
* González, L. E., & Uribe, D. (2018). Estimación del impacto financiero y social del abandono en la educación superior en Chile. *Revista Calidad en la Educación*, (48), 125–156.
* Government Accountability Office. (2017). *Higher Education: Students Need More Information to Help Lower Costs and Transfer Credits* (Informe N.º GAO-17-574). U.S. Government Accountability Office.
* Heileman, G. L., Abdallah, C. T., Slim, A., & Hickman, M. (2018). Curricular analytics: A framework for quantifying the impact of curricular reforms and pedagogical innovations. *arXiv preprint arXiv:1811.09676*.
* Jenkins, D., & Bailey, T. (2017). *Early Momentum Metrics: Why They Matter for Community Colleges*. Community College Research Center Research Brief, Columbia University.
* Kirkpatrick, S., Gelatt, C. D., & Vecchi, M. P. (1983). Optimization by simulated annealing. *Science*, 220(4598), 671–680. https://doi.org/10.1126/science.220.4598.671
* Manning, C. D., Raghavan, P., & Schütze, H. (2008). *Introduction to Information Retrieval*. Cambridge University Press.
* Monaghan, D. B., & Attewell, P. (2015). The continuing significance of degree completion: The case of community college transfers. *American Educational Research Journal*, 52(1), 54–87. https://doi.org/10.3102/0002831214553654
* Müller, T., Rudová, H., & Müllerová, Z. (2025). Real-world university course timetabling at the International Timetabling Competition 2019. *Journal of Scheduling*, 28, 267–289. https://doi.org/10.1007/s10951-024-00832-1
* OWASP Foundation. (2021). *OWASP Top Ten Web Application Security Risks*. https://owasp.org/www-project-top-ten/
* Salazar-Fernández, J. P., Sepúlveda, M., & Nussbaum, M. (2021). Curricular Analytics to Characterize Educational Trajectories in High-Failure Rate Courses That Lead to Late Dropout. *Applied Sciences*, 11(3), 1034. https://doi.org/10.3390/app11031034
* Schaerf, A. (1999). A survey of automated timetabling. *Artificial Intelligence Review*, 13(2), 87–127. https://doi.org/10.1023/A:1006576209967
* Servicio de Información de Educación Superior. (2023). *Informe de Duración Real y en Exceso de Carreras de Pregrado en Chile*. Subsecretaría de Educación Superior, Ministerio de Educación de Chile.
* Slim, A., Cosman, B., Abdallah, C. T., & Heileman, G. L. (2016). Quantifying the structural complexity of college curricula. *Proceedings of the 9th International Conference on Educational Data Mining (EDM 2016)*, 521–526.

---

## Anexo A · Protocolo Diseñado de Evaluación de Usabilidad (SUS)

Con miras a su ejecución futura con una muestra objetivo de $n = 30$ estudiantes de Ingeniería Civil Informática y personal de secretaría académica, se ha diseñado un protocolo de sesiones individuales de 10 minutos compuesto por:

1. **Tarea T1 (Malla DAG):** Marcar 6 asignaturas aprobadas en el plan 12210, identificar ramos habilitados y verificar el cálculo de créditos SCT.
2. **Tarea T2 (Convalidaciones IA):** Seleccionar una carrera de origen externa, evaluar 5 asignaturas aprobadas y revisar las sugerencias Top-3 y el folio generado.
3. **Tarea T3 (Generador UCTP):** Cargar programación semestral, elegir preferencia de jornada *Mañana* con criterio *Branch & Bound*, verificar `0 topes`, minimizar ventanas y exportar el archivo Excel.
4. **Tarea T4 (Gestión Académica — Directivos):** Cargar actas en *Estrés de Malla* e identificar el ramo con mayor índice combinado de bloqueo y reprobación; cargar planilla en *Mapa de Calor* e identificar bloques ociosos.
5. **Instrumento:** Cuestionario estándar SUS de 10 ítems (escala Likert 1 a 5), calculando la puntuación normalizada en $[0, 100]$ y comparando contra el umbral aceptable de referencia ($\text{SUS} \ge 70$).

---

## Anexo B · Guía de Reproducibilidad Técnica

Cualquier evaluador puede reproducir íntegramente el producto y la totalidad de las métricas reportadas en este paper mediante los siguientes comandos desde la raíz del repositorio:

```bash
# 1. Levantar la plataforma SIGA-DSS completa en puerto único (:8080)
cp .env.example .env
docker compose up --build

# 2. Ejecutar las 69 pruebas automatizadas en los 4 módulos
export SUITE_SSO_SECRET="pruebas-ci-suite-unab-secreto-de-al-menos-32-caracteres"
export DATABASE_URL="sqlite://:memory:"
(cd packages/suite-sso && python -m pytest -q)
(cd services/core && python -m pytest -q)
(cd services/mapa-calor && python -m pytest -q)
(cd services/estres-malla && python -m pytest -q)

# 3. Verificar calidad de código (Ruff) y reproducir benchmarks empíricos
python -m ruff check packages services/core scripts
python scripts/evaluacion/evaluar_motor.py
python scripts/evaluacion/evaluar_uctp.py
python scripts/evaluacion/evaluar_itc2019.py --max-perfiles 30 --json docs/img/metricas_itc2019.json
python scripts/evaluacion/evaluar_campus_itc2019.py --iteraciones 2500 --json docs/img/metricas_campus_itc2019.json
python scripts/evaluacion/evaluar_suite.py
```
