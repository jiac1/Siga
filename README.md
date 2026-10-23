# Siga — Proyecto de Título

**Diseño e implementación de Suite UNAB:** una plataforma web unificada para la integración de aplicaciones de apoyo académico de la carrera de Ingeniería Civil Informática (Universidad Andrés Bello), preparada para despliegue en infraestructura AWS.

---

## 📁 Estructura del Repositorio

El repositorio se encuentra organizado de la siguiente manera:

```text
.
├── iniciar-suite.bat         # Script para levantar todos los servidores locales con 1 clic
├── detener-suite.bat         # Script para detener los servidores activos
├── requirements.txt          # Dependencias consolidadas de Python (Django, Pandas, etc.)
├── README.md                 # Este archivo (guía principal del repositorio)
├── .gitignore                # Reglas de exclusión de Git (caché, entornos, logs)
│
├── docs/                     # Documentación oficial del proyecto y tesis
│   ├── Suite_UNAB_Proyecto_actualizado.docx  # Documento marco de la tesis
│   ├── Suite_UNAB_Proyecto.docx              # Versión previa del documento de tesis
│   ├── FORMATOS_DE_ARCHIVOS.md               # Especificación técnica de columnas y formatos (.xlsx)
│   └── ejemplos/                             # Archivos de ejemplo para pruebas
│       └── Horario_ICINF_2SEM.xlsx
│
├── suite-unab/               # Código fuente de la plataforma integrada
│   ├── index.html            # Dashboard principal (Shell de la Suite)
│   ├── login.html            # Acceso y autenticación
│   ├── shared/               # Recursos compartidos (barra superior, estilos, tokens, auth)
│   ├── scripts/              # Utilidades y scripts de extracción
│   └── apps/                 # Módulos y aplicaciones integradas
│       ├── malla/            # Malla Curricular interactiva (HTML/JS)
│       ├── horarios/         # Generador de Horarios Syaproa (HTML/JS)
│       ├── siga/             # SIGA - Visión de producto (HTML/JS)
│       ├── convalidacion/    # Convalidación de Asignaturas con IA (HTML/JS)
│       ├── mapa-calor/       # Mapa de Calor de ocupación (Django - Backend)
│       └── estres-malla/     # Estrés de Malla MallaIQ multi-tenant (Django - Backend)
│
└── archive/                  # Archivos comprimidos originales de respaldo (.zip)
```

---

## 🚀 Cómo ejecutar la Suite en Local

### 1. Requisitos previos
- **Python 3.10+** instalado.
- Instalar dependencias requeridas para los módulos Django:
  ```bash
  pip install -r requirements.txt
  ```

### 2. Inicio rápido (Recomendado en Windows)
Haz doble clic en:
```text
iniciar-suite.bat
```
Esto levantará automáticamente en ventanas de consola independientes:
1. **Suite UNAB Shell** en `http://localhost:8791/index.html` (Servidor HTTP estático)
2. **Mapa de Calor** en `http://127.0.0.1:8792/` (Django)
3. **Estrés de Malla** en `http://127.0.0.1:8793/` (Django)

Y abrirá automáticamente tu navegador en la Suite.

### 3. Detener los servidores
Para cerrar todos los procesos asociados a la Suite de una sola vez, haz doble clic en:
```text
detener-suite.bat
```

---

## 🧩 Estado de los Módulos Integrados

| Módulo | Tipo / Stack | Puerto / URL Local | Estado |
|---|---|---|---|
| **Shell & Dashboard** | HTML5 / CSS3 / Vanilla JS | `http://localhost:8791/index.html` | ✅ Integrado |
| **Malla Curricular** | Estática (JS / LocalStorage) | `http://localhost:8791/apps/malla/index.html` | ✅ Integrado (10 mallas) |
| **Generador de Horarios** | Estática (JS / Excel parsing) | `http://localhost:8791/apps/horarios/index.html` | ✅ Integrado |
| **SIGA** | Estática (Landing institucional) | `http://localhost:8791/apps/siga/index.html` | ✅ Integrado |
| **Convalidación con IA** | Estática / Client-side DB | `http://localhost:8791/apps/convalidacion/index.html` | 🟡 Extraído en `apps/convalidacion` |
| **Mapa de Calor** | Django 4.2 / Pandas / OpenPyXL | `http://localhost:8792/` | ✅ Integrado con backend |
| **Estrés de Malla (MallaIQ)** | Django 4.2 / Multi-tenant | `http://localhost:8793/` | ✅ Integrado con backend |

---

## 📚 Documentación adicional
- Revisa [`docs/Suite_UNAB_Proyecto_actualizado.docx`](docs/Suite_UNAB_Proyecto_actualizado.docx) para el alcance, marco teórico y objetivos de la tesis.
- Revisa [`docs/FORMATOS_DE_ARCHIVOS.md`](docs/FORMATOS_DE_ARCHIVOS.md) para conocer las columnas requeridas en los archivos Excel (`.xlsx`) de entrada.
