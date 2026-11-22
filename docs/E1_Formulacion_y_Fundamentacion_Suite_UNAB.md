# EVALUACIÓN E1 · FORMULACIÓN Y FUNDAMENTACIÓN DEL PROYECTO
**Asignatura:** INTEGRADOR II: SEM LIC EN CS (CINF200)  
**Carrera:** Ingeniería Civil Informática  
**Universidad:** Universidad Andrés Bello  
**Fecha de Entrega:** Septiembre de 2026  
**Título del Proyecto:** *Diseño e implementación de Suite UNAB: un Sistema de Soporte a la Decisión (DSS) integrado para la optimización de trayectorias curriculares y gestión de capacidad académica en la Facultad de Ingeniería de la Universidad Andrés Bello, desplegado en infraestructura AWS.*

---

## 1. Diagnóstico y Contexto

El proceso formativo en la educación superior chilena, particularmente en las carreras de ingeniería civil, enfrenta un desafío estructural histórico relacionado con la deserción, el retraso académico acumulativo y la sobreduración de los planes de estudio.

### 1.1. Evidencia Cuantitativa Oficial (Datos SIES - Mineduc)
De acuerdo con las estadísticas oficiales del **Servicio de Información de Educación Superior (SIES)** del Ministerio de Educación de Chile en su informe sobre *Duración Real y en Exceso de Carreras de Pregrado*:
* La carrera de **Ingeniería Civil en Computación e Informática** registra una **duración real promedio de 13,8 semestres**, frente a una duración formal nominal de 10 a 11 semestres.
* Esto representa una **sobreduración media de 2,91 semestres** (prácticamente un año y medio de permanencia adicional por cada egresado).
* En programas afines de base tecnológica (Ingeniería en Informática), la duración en exceso promedio asciende a **3,45 semestres**.

### 1.2. Costo Financiero del Abandono y la Sobreduración
La literatura especializada revela que la ineficiencia curricular tiene un impacto financiero devastador:
* En Chile, la deserción estudiantil en primer año genera un costo directo anual estimado entre **128 y 141 millones de dólares** para las instituciones de educación superior.
* Analizado en una ventana formativa de cinco años, la cohorte de estudiantes desertores representa para el sistema una pérdida acumulada superior a **1.100 millones de dólares** en aranceles no percibidos y pérdida de subsidios de gratuidad.
* Para el estudiante y su núcleo familiar, la pérdida de gratuidad o créditos del Estado al sobrepasar la duración nominal genera un sobreendeudamiento forzoso o la desvinculación definitiva en etapas avanzadas de la carrera.

---

## 2. Formulación de la Hipótesis del Proyecto

Tradicionalmente, las instituciones atribuyen el rezago y la deserción a factores intrínsecos del estudiante (brechas de capital cultural, nivel socioeconómico o hábitos de estudio). Sin embargo, este proyecto plantea como tesis central que una fracción crítica de este fenómeno obedece a deficiencias de diseño del sistema:

> **Hipótesis del Proyecto:**  
> *"La deserción universitaria, el retraso académico y la sobreduración de las carreras no obedecen de forma exclusiva a factores individuales o socioeconómicos del estudiante, sino que están significativamente determinados por fallas de diseño y opacidad institucional: la pérdida de avance en las convalidaciones de asignaturas, la presencia de puntos de estrés curricular (prerrequisitos rígidos y cursos cuello de botella) y la ausencia de herramientas tecnológicas de auditoría y planificación (como mallas interactivas).*  
>  
> *Consecuentemente, la carencia de estas herramientas de soporte a la toma de decisiones genera un costo financiero crítico tanto para los estudiantes (agotamiento de beneficios y desvinculación) como para las universidades (ingresos millonarios no devengados por deserción)."*

---

## 3. Fundamentación Teórica y Estado del Arte

La hipótesis formulada encuentra un sólido respaldo empírico en la literatura científica nacional e internacional:

### 3.1. Convalidación y Pérdida de Avance Curricular
* En procesos de transferencia y admisión especial, los estudiantes pierden en promedio entre el **34% y el 43%** de los créditos aprobados con anterioridad debido a revisiones lentas, manuales y discrecionales.
* La evidencia empírica demuestra que aquellos estudiantes que logran convalidar $\ge 90\%$ de sus asignaturas previas tienen **2,5 veces más probabilidades de graduarse** ($Odds\ Ratio = 2,5$) en comparación con aquellos que pierden más de la mitad de su carga académica anterior.

### 3.2. Puntos de Estrés Curricular (*Curricular Analytics*)
* Mediante la modelación de planes de estudio como Grafos Dirigidos Acíclicos ($G = (V, E)$), el marco de *Curricular Analytics* (Heileman et al.) formalizó que las asignaturas con un alto **Factor de Bloqueo ($b$)** (número de materias subsecuentes que dependen de ella) y un alto **Factor de Retraso ($d$)** (longitud del camino crítico más largo) estrangulan la progresión estudiantil.
* Un incremento de 20 puntos en la complejidad estructural de una malla curricular reduce en un **3,74%** la probabilidad de graduación a tiempo.
* En el contexto nacional chileno, **Salazar-Fernández et al. (2021)** demostraron empíricamente que el **76,21% de los estudiantes que desertan tardíamente** lo hacen adeudando ramos calificados formalmente como "cuellos de botella", tras una permanencia improductiva promedio de casi 9 semestres.

### 3.3. Impacto de las Herramientas de Auditoría (*Degree Audit*) y Mallas Interactivas
* Estudios en instituciones universitarias evidencian que la adopción de plataformas de auditoría de avance (*Degree Audit*) y trayectorias guiadas incrementa la titulación oportuna en **17 puntos porcentuales**.
* Simultáneamente, reduce la proporción de graduados con créditos sobrantes o improductivos desde un **30% a tan solo un 5%**.

### 3.4. Comparativa con Soluciones Existentes

| Paradigma | Ejemplos | Fortalezas | Limitaciones frente al enfoque Suite UNAB |
|---|---|---|---|
| **Sistemas ERP Institucionales** | Banner (Ellucian), PeopleSoft, SAP | Centralización de registros oficiales, actas y notas consolidadas. | Interfaces rígidas, poca usabilidad, nula simulación de escenarios (*what-if*), incapacidad de proyectar demanda de salas. |
| **Plataformas LMS** | Canvas, Blackboard, Moodle | Gestión de cursos, tareas y comunicación de aula. | Centrados exclusivamente en la asignatura individual; no visualizan la trayectoria curricular completa ni optimizan horarios. |
| **Iniciativas Estudiantiles Ad-hoc** | Scripts en GitHub, simuladores no oficiales | Ágiles para armar horarios puntuales. | Sin respaldo institucional, vulnerables al abandono, sin integración con datos oficiales y sin arquitectura de seguridad. |
| **Modelos de IA Aislados** | Consultas a ChatGPT o Claude | Análisis de lenguaje natural para comparar textos. | Desconectados del catálogo curricular oficial, propensos a alucinaciones sin supervisión y sin persistencia de datos. |

---

## 4. Definición del Problema y la Solución Propuesta

Actualmente, las herramientas diseñadas para asistir al estudiante y a la gestión académica en la facultad existen de manera **desarticulada, heterogénea y fragmentada**, operando como islas tecnológicas.

### 4.1. La Arquitectura de la Solución: Suite DSS Académica
Frente a esta dispersión, **Suite UNAB** se diseña como un **Sistema de Soporte a la Decisión (DSS)** que opera en un **ciclo cerrado de retroalimentación**, unificando la *Gestión Curricular* (Demanda Pedagógica) con la *Gestión de Capacidad* (Oferta Operativa del Campus):

```
                   ┌───────────────────────────────────────────┐
                   │               SUITE UNAB                  │
                   │        (Orquestador y Gateway)            │
                   └─────────────────────┬─────────────────────┘
                                         │
            ┌────────────────────────────┴───────────────────────────┐
            ▼                                                        ▼
  [ DEMANDA CURRICULAR ]                                   [ OFERTA OPERATIVA ]
  1. Malla Interactiva (DAG)                               4. Mapa de Calor de Salas
     - Trayectoria y what-if                                  - Detección de sobrecupo/ociosidad
  2. Estrés de Malla (MallaIQ)                             5. Generador de Horarios (UCTP)
     - Detección de cuellos de botella                        - Asignación libre de choques
  3. Convalidaciones con IA                                  - Minimización de ventanas
     - Cruce de syllabi de transferencias
            │                                                        ▲
            └──────────────────── Feedback Continuo ─────────────────┘
                   (Proyección de vacantes vs. Capacidad física)
```

### 4.2. Matriz de Módulos de la Suite

| Módulo | Enfoque Técnico | Problema que Resuelve |
| :--- | :--- | :--- |
| **1. Malla Interactiva** | Teoría de Grafos (DAG), recorrido recursivo BFS/DFS, simulación *what-if*. | Opacidad en la trayectoria del alumno, toma desinformada de asignaturas y rezago accidental. |
| **2. Estrés de Malla (MallaIQ)** | *Curricular Analytics* (factores de bloqueo, criticidad y atraso por ramo). | Identificación formal de asignaturas filtro y riesgo de deserción tardía institucional. |
| **3. Convalidaciones con IA** | Procesamiento de Lenguaje Natural (NLP/LLM) aplicado a *syllabi*. | Reducción del dictamen de equivalencia de semanas a minutos, preservando créditos aprobados. |
| **4. Mapa de Calor de Salas** | Analítica espacial matricial de ocupación por campus, edificio y módulo. | Erradicación de salas sobrevendidas y visualización de franjas horarias con capacidad ociosa. |
| **5. Generador de Horarios** | Optimización combinatoria en UCTP (*University Course Timetabling Problem*). | Creación automatizada de combinaciones de horario compatibles, sin topes duros y con ventanas mínimas. |
| **6. El Orquestador Central** | Middleware unificado, gateway de proxy inverso y logging centralizado (*sznLogger*). | Conecta la demanda proyectada por la analítica curricular con la oferta logística de cursos y salas. |

---

## 5. Objetivos del Proyecto

### 5.1. Objetivo General
**Diseñar e implementar Suite UNAB**, un Sistema de Soporte a la Decisión (DSS) web modular que integre bajo una arquitectura desacoplada y un puerto público unificado las aplicaciones de apoyo curricular y logístico para las carreras de la Facultad de Ingeniería de la Universidad Andrés Bello —abarcando sus 10 programas de pregrado, con foco inicial y validación piloto en Ingeniería Civil Informática—, incluyendo la malla interactiva, el generador de horarios, el mapa de calor, el análisis de estrés curricular y la convalidación asistida por IA, desplegada en infraestructura de Amazon Web Services (AWS), con el propósito de mitigar la sobreduración académica, optimizar la asignación de recursos y sentar las bases para una gestión universitaria basada en datos.

### 5.2. Objetivos Específicos
1. **Auditar y formalizar** los modelos de datos, flujos de trabajo y requerimientos operativos de las herramientas preexistentes en la Facultad de Ingeniería de la UNAB.
2. **Diseñar una arquitectura modular unificada** basada en micro-frontends/servicios desacoplados con tokens de diseño transversales (*Design System*), barra compartida (`suite-bar`) y un orquestador reverse proxy centralizado.
3. **Refactorizar y optimizar la lógica algorítmica** de las aplicaciones base, incorporando teoría de grafos para la propagación de requisitos en la malla curricular y modelos de *Curricular Analytics* para el diagnóstico de estrés.
4. **Implementar y calibrar el módulo de convalidaciones asistido por IA**, utilizando procesamiento de lenguaje natural semántico para contrastar descriptores curriculares y programas de asignaturas externas.
5. **Formular el motor de planificación horaria (UCTP)** mediante técnicas de optimización combinatoria que garanticen el cumplimiento de restricciones duras (topes de sección, sala y docente) y minimicen restricciones blandas (ventanas horarias).
6. **Diseñar y automatizar la infraestructura Cloud en AWS** (S3, CloudFront, ECS/EC2, Application Load Balancers) para garantizar alta disponibilidad, aislamiento de procesos y escalamiento de cada módulo.
7. **Validar la plataforma mediante pruebas cuantitativas y evaluación de experiencia de usuario (UX)** con estudiantes y autoridades académicas, contrastando tiempos de resolución de trámites frente a los métodos tradicionales.

---

## 6. Alcance y Estrategia de Mitigación de Riesgos

Para asegurar la culminación exitosa de la memoria de titulación dentro de los plazos académicos establecidos, el proyecto adopta una **estrategia de desacoplamiento operativo y experimental**:

1. **Entregable Principal de Titulación (Track Operativo):**
   * Puesta en marcha de la Suite DSS completa, funcional e integrada en el puerto unificado, con pruebas unitarias y de integración continuas (81+ tests automatizados en CI).
   * Evaluación de usabilidad empírica con estudiantes y secretaría académica de la facultad.
2. **Línea de Extensión Científica (Track de Investigación Avanzada):**
   * El estudio comparativo profundo de metaheurísticas continuas avanzadas para el problema UCTP se formula como un marco metodológico modular, permitiendo experimentar con diversas técnicas de optimización sin comprometer la entrega operativa del producto de titulación.

---

## 7. Estructura de la Exposición Oral (Defensa E1)

* **Slide 1 · Portada:** Título del proyecto, alumno memorista, profesor guía, institución y fecha.
* **Slide 2 · El Problema Real:** Datos oficiales SIES (13,8 semestres de duración real, 2,91 semestres de exceso) y costo financiero de la deserción (\$1.100M USD en 5 años).
* **Slide 3 · La Hipótesis Central:** La sobreduración como consecuencia de fallas de diseño curricular, cuellos de botella y opacidad en la toma de decisiones.
* **Slide 4 · Evidencia del Estado del Arte:** *Curricular Analytics* (Heileman), Salazar-Fernández (2021) y el impacto del 76,2% en ramos cuello de botella.
* **Slide 5 · La Solución: Suite UNAB:** Concepto de Sistema de Soporte a la Decisión (DSS) en ciclo cerrado (Demanda Pedagógica $\leftrightarrow$ Oferta Logística).
* **Slide 6 · Módulos Curriculares:** Malla Interactiva (Grafos DAG), Estrés de Malla (MallaIQ) y Convalidaciones con IA.
* **Slide 7 · Módulos Logísticos:** Mapa de Calor de Salas y Generador de Horarios (UCTP).
* **Slide 8 · Arquitectura Técnica y Gateway:** Orquestador central, puerto unificado 8791, logging centralizado (*sznLogger*) y despliegue Cloud en AWS.
* **Slide 9 · Metodología y Pruebas:** Plan de trabajo hito a hito y suite de pruebas automatizadas (81 tests en CI).
* **Slide 10 · Conclusiones y Preguntas:** Impacto esperado en la retención, graduación oportuna y eficiencia operativa de la facultad.
