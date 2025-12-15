# Diario del Equipo

> *Este documento sirve como registro oficial del seguimiento del proyecto **foodhub-2**. En él se recogen las decisiones estratégicas, la evolución de la gestión de la configuración y los acuerdos fundamentales adoptados por el equipo durante el desarrollo de la asignatura. Su objetivo es garantizar la trazabilidad de las decisiones y el cumplimiento de las recomendaciones del proyecto de curso.*

## foodhub-2

* **Grupo:** 1
* **Curso escolar:** 2025/2026
* **Asignatura:** Evolución y gestión de la configuración

### Miembros del grupo

1. ÁLVAREZ RAYA, Miguel
2. BARAC PLOAE, Enrique Nicolae
3. CHABRERA RUBIO, Adrián Miguel
4. CIRIA GONZALEZ, Guillermo
5. EL HAKIMY ETTORABI, Salma
6. GONZALEZ MACIAS, Alejandro

---

## Resumen de total de reuniones empleadas en el equipo

* **Total de reuniones:** 3
* **Total de reuniones presenciales:** 1
* **Total de reuniones virtuales:** 2
* **Total de tiempo empleado en reuniones presenciales:** 1 hora
* **Total de tiempo empleado en reuniones virtuales:** 5 horas

---

## Actas de acuerdos de las reuniones

### ACTA 2025-01
*Reunión inicial de constitución y metodología*

* **Fecha:** 25 de septiembre de 2025
* **Asistentes:** Miembros del grupo FoodHub-2
* **Acuerdos tomados:**
    * **Acuerdo 2025-01-01:** Constitución del equipo y establecimiento de las normas básicas de colaboración y canales de comunicación interna.
    * **Acuerdo 2025-01-02:** Designación de **Adrián Miguel Chabrera Rubio** como Responsable del Grupo (Team Lead) para la coordinación general.
    * **Acuerdo 2025-01-03:** Decisión estratégica de colaborar con otro grupo para el desarrollo conjunto del proyecto, compartiendo repositorio y objetivos globales.
    * **Acuerdo 2025-01-04:** Definición de la metodología de trabajo preliminar y herramientas a utilizar.

### ACTA 2025-02
*(Reunión de coordinación con el grupo FoodHub-1)*

* **Fecha:** 1 de octubre de 2025
* **Asistentes:** Miembros de FoodHub-2 y FoodHub-1
* **Acuerdos tomados:**
    * **Acuerdo 2025-02-01:** Selección del dominio de datos del proyecto. Se trabajará con Datasets relacionados con alimentación (`.food`).
    * **Acuerdo 2025-02-02:** Selección y asignación de los *Work Items* a implementar. Se ha realizado la división de tareas específicas entre FoodHub-1 y FoodHub-2 para evitar solapamientos.
    * **Acuerdo 2025-02-03:** Establecimiento de la estrategia de gestión de la configuración y ramas (*Branching Strategy*) en el repositorio común:
        * Se mantendrá una rama `main` como línea base de producción.
        * Se crearán ramas de estabilización/integración por grupo: `main-1` (FoodHub-1) y `main-2` (FoodHub-2).
        * El desarrollo se realizará mediante ramas `trunk-1` y `trunk-2` (o *feature branches* asociadas a cada grupo) antes de integrar en sus respectivas ramas principales.

### ACTA 2025-03
*(Reunión de revisión final y cierre de entrega)*

* **Fecha:** 14 de diciembre de 2025
* **Asistentes:** Miembros del grupo FoodHub-2
* **Acuerdos tomados:**
    * **Acuerdo 2025-03-01:** Revisión y validación de los *Work Items* asignados al grupo. Se confirma su correcto funcionamiento según los requisitos.
    * **Acuerdo 2025-03-02:** Corrección de errores (*bug fixing*) detectados en las últimas pruebas de integración para asegurar la calidad de la entrega final.
    * **Acuerdo 2025-03-03:** Verificación de los *Workflows* (flujos de trabajo de CI/CD). Se confirma que las automatizaciones se ejecutan correctamente sin fallos.
    * **Acuerdo 2025-03-04:** Cierre formal de *Issues* pendientes y últimos retoques a la documentación para la entrega del proyecto.