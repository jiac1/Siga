# EVALUACIÓN E1 · FORMULACIÓN Y FUNDAMENTACIÓN DEL PROYECTO
**Asignatura:** INTEGRADOR II: SEM LIC EN CS (CINF200)  
**Carrera:** Ingeniería Civil Informática  
**Universidad:** Universidad Andrés Bello  
**Fecha de Entrega:** 27 de Septiembre de 2026  
**Título del Proyecto:** *Diseño e implementación de Suite UNAB: una plataforma web unificada para la integración de aplicaciones de apoyo académico de la carrera de Ingeniería Civil Informática, desplegada en infraestructura AWS.*

---

## 1. Diagnóstico y Contexto

El proceso formativo en la educación superior chilena, particularmente en las ingenierías civiles, enfrenta un desafío histórico relacionado con la progresión académica, la retención y la titulación oportuna.

### 1.1. Evidencia Cuantitativa (Datos Oficiales SIES - Mineduc)
De acuerdo con el informe oficial del **Servicio de Información de Educación Superior (SIES)** del Ministerio de Educación de Chile (*Duración Real y en Exceso de Carreras de Pregrado*):
* La carrera de **Ingeniería Civil en Computación e Informática** presenta una **duración real promedio de 13,8 semestres**, frente a una duración formal nominal de 10 a 11 semestres.
* Esto representa una **sobreduración media de 2,91 semestres** (casi un año y medio de retraso por estudiante titulado).
* En el caso de programas afines de base tecnológica (Ingeniería en Informática), la duración en exceso promedio asciende a **3,45 semestres**.

### 1.2. Factores Operativos y Sistémicos
El análisis cualitativo y operativo al interior de la carrera de Ingeniería Civil Informática de la UNAB identifica que este retraso no responde exclusivamente a dificultades de aprendizaje, sino a **fricciones de gestión curricular**:
1. **Pérdida de continuidad por prerrequisitos:** Asignaturas clave ("cuellos de botella") del plan común y formativo que bloquean múltiples ramas curriculares posteriores si no se aprueban a tiempo.
2. **Choques horarios en la inscripción:** El estudiante debe contrastar manualmente la oferta académica (archivos Excel de programación horaria) con su avance curricular, lo que con frecuencia provoca topes de horario, obligándolo a postergar materias y dilatando su permanencia.
3. **Complejidad en convalidaciones:** Procesos de convalidación lentos y manuales para alumnos que ingresan por transferencias o vías de admisión especial, requiriendo revisiones extensas de programas de asignaturas y mallas de otras casas de estudio.

---

## 2. Definición del Problema

Actualmente, las herramientas digitales diseñadas para asistir al estudiante y a la gestión académica existen de manera **desarticulada, heterogénea y fragmentada**.

### 2.1. Manifestación de la Problemática
* **Dispersión de herramientas:** La secretaría académica ha desarrollado iniciativas valiosas (malla interactiva, generador de horarios Syaproa, mapa de calor de salas, modelos de estrés de malla y sistemas de convalidación), pero cada una opera en repositorios aislados, con tecnologías distintas, sin una identidad visual común ni persistencia transversal.
* **Carga cognitiva para el estudiante:** El alumno debe aprender a interactuar con interfaces no estandarizadas, descargar y manipular archivos de hojas de cálculo por su cuenta y volver a ingresar sus datos en cada herramienta.
* **Sobrecarga administrativa:** Las secretarías académicas y unidades de Servicio al Estudiante absorben un alto volumen de consultas operativas presenciales y por correo que podrían resolverse mediante una plataforma de autoservicio confiable y centralizada.
* **Riesgo de obsolescencia y deuda técnica:** La mantención de múltiples servidores y scripts independientes dificulta el escalamiento, la seguridad y el monitoreo de disponibilidad institucional.

---

## 3. Estado del Arte

En el ecosistema universitario conviven tres grandes paradigmas de soluciones tecnológicas, cada uno con fortalezas y limitaciones marcadas:

| Paradigma | Ejemplos | Fortalezas | Limitaciones frente a Suite UNAB |
|---|---|---|---|
| **Sistemas de Gestión Institucional (ERP Monolíticos)** | Banner (Ellucian), PeopleSoft, SAP | Centralización de registros oficiales, actas y notas consolidadas. | Interfaces rígidas, poca interactividad, simulación nula de escenarios hipotéticos ("qué pasa si repruebo"), lenta adaptación a requerimientos locales de carrera. |
| **Sistemas de Gestión de Aprendizaje (LMS)** | Canvas, Blackboard, Moodle | Gestión de cursos, tareas y comunicación docente-alumno. | Orientados al aula y a la asignatura individual; no abordan la trayectoria curricular integral ni la planificación de horarios multi-sección. |
| **Herramientas de Autoservicio Comunitarias** | Proyectos estudiantiles en GitHub, simuladores no oficiales | Ágiles, resuelven problemas puntuales de estudiantes (generar horario sin topes). | Sin respaldo institucional, vulnerables al abandono, sin integración con datos oficiales y sin arquitectura de seguridad. |
| **Soluciones de IA Curricular Emergentes** | LLMs comerciales aplicados ad-hoc (ChatGPT, Claude) | Capacidad de procesamiento de lenguaje natural para comparar textos de programas. | Falta de validación formal de equivalencias curriculares, alucinaciones y ausencia de un entorno integrado con el plan de estudios. |

### 3.1. La Propuesta de Suite UNAB: Modelo "Creative Suite / Cloud"
Inspirándose en la evolución del software hacia plataformas integradas (popularizado por Adobe con Creative Suite en 2003 y Creative Cloud en 2013, o Microsoft 365), **Suite UNAB** adopta una arquitectura modular desacoplada:
* Cada módulo conserva su valor funcional específico (Malla, Horarios, Mapa de Calor, Estrés de Malla, Convalidación).
* Comparten componentes transversales comunes: sistema de diseño unificado (*Design System* con tokens CSS), barra de navegación transversal (`suite-bar`), esquema de autenticación único y catálogo central de planes de estudio.
* Infraestructura en la nube (AWS) que permite mantener, escalar o desplegar cada módulo de forma independiente, sentando las bases para un modelo multi-tenant transferible a otras instituciones.

---

## 4. Objetivos del Proyecto

### 4.1. Objetivo General
**Diseñar e implementar Suite UNAB**, una plataforma web que integre bajo una arquitectura común y desacoplada las aplicaciones de apoyo académico desarrolladas para la carrera de Ingeniería Civil Informática de la Universidad Andrés Bello —incluyendo la malla curricular interactiva, el generador de horarios, el mapa de calor, el analizador de estrés curricular y el sistema de convalidación de ramos basado en inteligencia artificial—, siguiendo el modelo de integración modular de suites de software, desplegada en infraestructura de Amazon Web Services (AWS), con el fin de optimizar la experiencia digital del estudiante y sentar las bases para el mantenimiento y escalamiento independiente de cada módulo a futuro.

### 4.2. Objetivos Específicos
1. **Levantar y documentar** las aplicaciones y prototipos ya desarrollados por la secretaría académica de la carrera, identificando su arquitectura base, dependencias tecnológicas, formatos de datos de entrada (.xlsx, .pdf) y estado funcional.
2. **Diseñar una arquitectura de integración modular**, inspirada en el modelo de suite (estilo Adobe/Microsoft 365), que permita la operación desacoplada de cada aplicación mientras comparten servicios transversales (identidad de marca, navegación, autenticación e infraestructura).
3. **Migrar, refactorizar e integrar** las aplicaciones existentes dentro de la nueva plataforma unificada, implementando mejoras de usabilidad (algoritmos de grafos recursivos para prerrequisitos en cascada, aprobación por bloques y filtros de periodo) sin degradar sus capacidades originales.
4. **Diseñar, configurar y desplegar la infraestructura Cloud en Amazon Web Services (AWS)** (mediante servicios como S3, CloudFront, ECS/EC2 y RDS/ALB) requerida para hospedar la plataforma de forma escalable, segura y bajo un dominio unificado.
5. **Integrar y evaluar el módulo de convalidación de asignaturas asistido por Inteligencia Artificial**, validando experimentalmente que sus tiempos de respuesta y precisión en el cruce de planes de estudio cumplan con los estándares de apoyo al secretario académico.
6. **Evaluar empíricamente la experiencia de usuario (UX)** de la plataforma integrada mediante pruebas de usabilidad con estudiantes de la carrera, contrastando métricas de facilidad de uso, tiempos de tarea y percepción frente al uso de herramientas dispersas.
7. **Elaborar la documentación técnica de arquitectura y guía de transferencia**, estructurando el proyecto bajo un enfoque multi-tenant que permita su mantenimiento futuro y la eventual comercialización o adopción independiente de sus módulos por otras universidades.

---

## 5. Estructura de la Presentación Inicial (Defensa E1)

A continuación se detalla la propuesta de diapositivas (10 slides) para la exposición ante el docente y comisión:

* **Slide 1 · Portada:** Título del proyecto, integrantes, profesor guía, carrera y fecha.
* **Slide 2 · Contexto y Diagnóstico:** El problema de la permanencia estudiantil en ingeniería. Cita del SIES: 13,8 semestres de duración real y 2,91 semestres de sobreduración en Civil Informática.
* **Slide 3 · Definición del Problema:** Fragmentación de herramientas académicas, interfaces dispares, errores en toma de ramos y sobrecarga en secretaría académica.
* **Slide 4 · Estado del Arte:** Comparativa entre ERPs tradicionales (Banner), LMS (Canvas) y herramientas no oficiales. Vacío existente en el autoservicio estudiantil integrado.
* **Slide 5 · La Propuesta: Suite UNAB:** Concepto de "Suite de Software" (análogo a Adobe / Microsoft). Modularidad, consistencia visual y desacoplamiento.
* **Slide 6 · Módulos de la Suite:**
  1. Malla Curricular Interactiva (con lógica de grafos y cascada inteligente).
  2. Generador de Horarios Syaproa (optimización de secciones sin choques).
  3. Mapa de Calor (análisis de ocupación física en Django).
  4. Estrés de Malla - MallaIQ (detección de cuellos de botella multi-tenant).
  5. Convalidación Asistida por IA (análisis semántico de mallas externas).
* **Slide 7 · Objetivo General y Específicos:** Presentación clara del alcance de titulación.
* **Slide 8 · Arquitectura y Despliegue Cloud (AWS):** Visión de frontend estático (S3/CloudFront) y servicios de backend (Django en ECS/Fargate o EC2) unificados bajo un proxy inverso.
* **Slide 9 · Metodología y Plan de Trabajo:** Fases del proyecto alineadas a los hitos del curso (E1: Formulación, E2: Avance y MVP, E3: Producto final y evaluación de usabilidad).
* **Slide 10 · Conclusiones y Ronda de Preguntas.**
