# Historial de versiones

| Versión | Fecha       | Autor  | Descripción del cambio |
|---------|------------|--------|-----------------------|
| 1.0     | 20/10/2025 | Emilio y Germán | Documento inicial creado |

# Metodología de gestión de la configuración

Este documento describe la metodología de gestión de la configuración adoptada por el grupo, detallando cómo se implementarán las buenas prácticas en cada área y proporcionando referencias adecuadas del material utilizado.

## Índice

1. [Coding standards](#1-coding-standards)  
   1.1 [Estructura del código](#11-estructura-del-código)  
   1.2 [Formato y legibilidad](#12-formato-y-legibilidad)  
   1.3 [Buenas prácticas de código](#13-buenas-prácticas-de-código)  
   1.4 [Documentación y estilo](#14-documentación-y-estilo)  
2. [Política de commits](#2-política-de-commits)  
   2.1 [Estructura del mensaje de commit](#21-estructura-del-mensaje-de-commit)  
   2.2 [Tipos de commits](#22-tipos-de-commits)  
   - [Ejemplos](#ejemplos)  
3. [Estructura de los repositorios y ramas por defecto](#3-estructura-de-los-repositorios-y-ramas-por-defecto)  
4. [Estrategia de branching](#4-estrategia-de-branching)  
   4.1 [Cómo desarrollar las ramas de funcionalidad](#41-cómo-desarrollar-las-ramas-de-funcionalidad)  
   4.2 [Cómo preparar los lanzamientos (releases)](#42-cómo-preparar-los-lanzamientos-releases)  
       4.2.1 [Comenzar un lanzamiento](#421-comenzar-un-lanzamiento)  
       4.2.2 [Terminar un lanzamiento](#422-terminar-un-lanzamiento)  
       4.2.3 [Reglas de versionado y lanzamiento](#423-reglas-de-versionado-y-lanzamiento)  
   4.3 [Corrección de bugs en producción](#43-corrección-de-bugs-en-producción)  
5. [Políticas de versionado](#5-políticas-de-versionado)  
   5.1 [Versión del proyecto](#51-versión-del-proyecto)  
6. [Referencias](#6-referencias)  

---

## 1. Coding standards

Estos estándares garantizan un código más limpio, legible y mantenible, reduciendo errores y facilitando la colaboración en equipo.

### 1.1 Estructura del código

- Clases: `PascalCase`  
- Funciones, variables y métodos: `snake_case`  
- Constantes: `SCREAMING_SNAKE_CASE`  
- Archivos y carpetas organizados por funcionalidad  
- Evitar métodos gigantes y números mágicos

### 1.2 Formato y legibilidad

- Límite de caracteres: 80-100  
- Indentación: 4 espacios  
- Comentarios solo si es estrictamente necesario  
- Eliminar código y variables no utilizadas

### 1.3 Buenas prácticas de código

- Evitar duplicación de código  
- Métodos responsables de una única tarea

### 1.4 Documentación y estilo

- Seguir estándares como `mypy`, `Flake8`, `Pylint`

---

## 2. Política de commits

- Commits atómicos, claros, en inglés  
- Primera letra mayúscula, imperativo, sin punto final
- Se recomienda el uso de la extensión 'Conventional Commits' creado por vivaxy.

### 2.1 Estructura del mensaje de commit
[tipo]: [emoji] [Verbo en imperativo] [descripción]


### 2.2 Tipos de commits

| Tipo | Emoji | Descripción |
|------|-------|-------------|
| feat | ✨ | Agregar nueva funcionalidad |
| fix | 🐛 | Corregir un error |
| chore | 🔧 | Mantenimiento rutinario |
| test | ✅ | Agregar o corregir pruebas |
| docs | 📝 | Actualizar documentación |
| ci | 🔄 | Cambios CI |
| style | 💄 | Actualizar UI o estilos |
| refactor | ♻️ | Cambios que no alteran funcionalidad |
| revert | ⏪ | Revertir commit |

### Ejemplos

ci: 🔄 Create commits validation
feat: ✨ Improve view dataset GUI
fix: 🐛 Resolve bug in create dataset


---

## 3. Estructura de los repositorios y ramas por defecto

- Archivos raíz: `README.md`, `.env.example`, `requirements.txt`  
- Carpetas raíz: `/github/workflows`, `/app`, `/core`, `/docker`, `/migrations`, `/rosemary`, `/scripts`, `/vagrant`  

**Ramas principales:**  
- `main`: release, no se destruye  
- `trunk`: desarrollo ágil, merge frecuente, no se destruye

**Ramas de características:**  
feature/Issue-identifier-[nombre_del_elemento_de_trabajo]

**Ramas de bugfix:**  
bugfix/Issue_identifier-[nombre_del_elemento_de_trabajo]

**Pautas:**  
- No usar ramas por persona  
- Destruir ramas tras merge exitoso  
- Merge frecuente  
- Despliegues automáticos en `trunk` y `main`

---

## 4. Estrategia de branching

### 4.1 Cómo desarrollar las ramas de funcionalidad

- Crear rama según formato definido  
- Desarrollar tarea  
- Hacer merge y cerrar rama  
- PR solo entre equipos si es necesario

### 4.2 Cómo preparar los lanzamientos (releases)

- Verificar estabilidad y pasar pruebas antes de lanzar

#### 4.2.1 Comenzar un lanzamiento

- Fusionar en `main` hasta commit deseado de `trunk`  
- Solo modificaciones necesarias para estabilidad; nuevas características en desarrollo

#### 4.2.2 Terminar un lanzamiento

- Registrar cambios con etiqueta de versión  
- Workflows CD despliegan automáticamente

#### 4.2.3 Reglas de versionado y lanzamiento

- Partir siempre de `trunk`  
- Documentar y probar cada lanzamiento  
- Nombrar versión: `VX.Y.Z` (Versionado Semántico)

### 4.3 Corrección de bugs en producción

1. Crear rama `bugfix/...` desde `main`  
2. Aplicar y probar corrección  
3. Pasar pruebas unitarias e integración  
4. Merge en `main` y `trunk`  
5. Desplegar en producción y notificar al equipo

---

## 5. Políticas de versionado

- Seguimiento de modificaciones para trazabilidad

### 5.1 Versión del proyecto

Versionado Semántico `X.Y.Z`:

- **X (MAJOR)**: cambios rompedores, incompatibles  
- **Y (MINOR)**: nuevas funcionalidades, compatible hacia atrás  
- **Z (PATCH)**: correcciones menores

---

## 6. Referencias

- [Conventional Commits](https://www.conventionalcommits.org/)  
- [Gitmoji](https://gitmoji.dev/)  
- Estrategia de ramas

---

**Última modificación:** 20/10/2025
