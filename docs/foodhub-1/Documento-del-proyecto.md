## Indicadores del proyecto

(_debe dejar enlaces a evidencias que permitan de una forma sencilla analizar estos indicadores, con gráficas y/o con enlaces_)

Miembro del equipo  | Horas | Commits | LoC | Test | Issues | Work Item| Dificultad
------------- | ------------- | ------------- | ------------- | ------------- | ------------- |  ------------- |  ------------- | 
[García Vizcaino, Miguel](https://github.com/Miguelgarviz) | 60 | 15 | 1623 | 5 | 2 | Solicitar cambio de contraseña por medio de un codigo enviado al correo del usuario | L |
[Prieto Fernández, Juan](https://github.com/juanprietofernandez) | 63 | 32 | 2998 | 30 | 1 | Crear una sección de trending datasets en la página de inicio en la que se mostrará los tres datasets más populares de la semana, la popularidad se decide por el de número de descargas y número de visualizaciones. | M |
[Jiménez Guerrero, Pedro](https://github.com/PedroJimenezGuerrero) | 67 | 54 | 5522 | 67 | 16 | La búsqueda actual es limitada. Queremos usar Elasticsearch para indexar datasets, modelos y usuarios y Como usuario, quiero buscar datasets usando filtros avanzados (autor, etiquetas, fechas) para encontrar fácilmente lo que busco | H y M |
[Ojeda Garrido, Germán](https://github.com/German220203) | 62 | 62 | 12440 | 5 | 8 | Adaptar la aquitectura de UVLHub para crear un sistema modular en el que se guarden, verifiquen y analicen Food models a aprtir de archivos .food, sustituyendo el antiguo módulo dataset por basedataset y fooddataset, el antiguo módulo featuremodel por foodmodel, y el antiguo flamapy por el módulo food_checker | H |
[Manuel Vázquez Cruz, Emilio](https://github.com/Emilio-115) | 68 | 30 | 1258 | 7 | 6 | Verificación en 2 pasos, se ha añadido  un sistema de OTP para generar códigos de un uso junto con un QR para añadirlo a apps de 2FA, permite habilitarse desde editar perfil desde la pantalla de inicio | H |
[Coronil, Pepe](https://github.com/PepeCoral) | 62 | 15 | 1029 | 30 | 4 | Al registrar una cuenta, es necesario verificar el email para poder iniciar sesion, se envia un email de verificación. | L |
**TOTAL** | 382  | 191 | 24870 | 149 | 37 | Descripción breve | H(3)/M(2)/L(2) |

![Texto alternativo](/docs/images/Commits%20over%20time.png)

La tabla contiene la información de cada miembro del proyecto y el total de la siguiente forma: 
  * Horas: número de horas empleadas en el proyecto
  * Commits: solo contar los commits hechos por miembros del equipo, no lo commits previos
  * LoC (líneas de código): solo contar las líneas producidas por el equipo y no las que ya existían o las que se producen al incluir código de terceros
  * Test: solo contar los test realizados por el equipo nuevos. Tambien se han contado arreglos de tests y la realización de test de forma conjunta
  * Issues: solo contar las issues gestionadas dentro del proyecto y que hayan sido gestionadas por el equipo
  * Work Item: principal WI del que se ha hecho cargo el miembro del proyecto
  * Dificultad: señalar el grado de dificultad en cada caso. Además, en los totales, poner cuántos se han hecho de cada grado de dificultad entre paréntesis. 

## Integración con otros equipos
Equipos con los que se ha integrado y los motivos por lo que lo ha hecho y lugar en el que se ha dado la integración: 
* [food-hub-2](https://github.com/EGC-FoodHub/foodhub/tree/main-2): breve descripción de la integración

## Resumen ejecutivo (800 palabras aproximadamente)
El presente trabajo tiene como objetivo principal el diseño y desarrollo de una aplicación web para la gestión, almacenamiento y visualización de archivos .food, los cuales corresponden a ficheros en formato CSV que contienen información estructurada sobre alimentos. La motivación del proyecto surge de la necesidad de disponer de una herramienta centralizada, accesible y eficiente que permita manejar este tipo de datos de forma sencilla, evitando procesos manuales y facilitando su consulta y reutilización.

La aplicación desarrollada, denominada FoodHub, se concibe como una plataforma web accesible desde navegador, lo que garantiza su portabilidad y facilidad de uso sin requerir instalaciones adicionales por parte del usuario. A través de esta aplicación, los usuarios pueden cargar archivos .food, almacenarlos de manera organizada y acceder a la información contenida en ellos de forma clara e intuitiva. De este modo, el sistema actúa como un repositorio especializado en datos alimentarios, permitiendo una gestión más estructurada de la información.

Desde el punto de vista tecnológico, el proyecto se ha implementado utilizando Python como lenguaje de programación principal, debido a su versatilidad, legibilidad y amplia adopción en el desarrollo de aplicaciones web y el tratamiento de datos. Para la ejecución de la aplicación y la gestión de las peticiones web se ha empleado el framework Flask, una herramienta ligera y flexible que permite construir aplicaciones web de forma modular y escalable. Flask facilita la definición de rutas, el manejo de formularios, la interacción con los archivos cargados por el usuario y la generación dinámica de las vistas que se muestran en el navegador.

La arquitectura de la aplicación sigue un enfoque claro y estructurado, separando la lógica de negocio, la gestión de datos y la presentación. Esta organización contribuye a mejorar la mantenibilidad del código y facilita futuras ampliaciones del sistema, como la incorporación de nuevas funcionalidades o la adaptación a otros formatos de datos. Asimismo, el uso de archivos CSV como base del sistema garantiza la compatibilidad con múltiples herramientas externas y la facilidad de intercambio de información.

En cuanto a la funcionalidad, FoodHub permite a los usuarios cargar archivos .food de forma segura, validando su formato y asegurando que los datos se ajusten a la estructura esperada. Una vez almacenados, los archivos pueden ser consultados a través de la interfaz web, mostrando la información de manera ordenada y comprensible. Esto reduce la complejidad asociada al manejo directo de ficheros CSV y mejora la experiencia del usuario final, que puede centrarse en el análisis de los datos en lugar de en aspectos técnicos.

Los resultados del proyecto pueden observarse en la aplicación desplegada y accesible públicamente en la siguiente dirección: foodhub-main-1.onrender.com. Este despliegue demuestra la viabilidad real de la solución propuesta y confirma que la aplicación funciona correctamente en un entorno productivo, más allá del desarrollo local. La disponibilidad online permite además evaluar el rendimiento, la estabilidad y la usabilidad del sistema en condiciones reales de uso.

A nivel de resultados, el proyecto cumple satisfactoriamente los objetivos planteados inicialmente. Se ha logrado desarrollar una aplicación web funcional que permite almacenar y gestionar archivos .food, utilizando tecnologías actuales y ampliamente utilizadas en el ámbito del desarrollo web. La elección de Python y Flask ha demostrado ser adecuada, proporcionando una base sólida y flexible para el desarrollo del sistema. Además, el proyecto pone de manifiesto la capacidad de integrar conceptos de programación, tratamiento de datos y desarrollo web en una solución práctica y aplicable.

Desde una perspectiva formativa y técnica, el trabajo aporta un conocimiento relevante sobre el ciclo completo de desarrollo de una aplicación web: desde la definición del problema y los requisitos, hasta la implementación, prueba y despliegue de la solución final. También evidencia la importancia de elegir herramientas adecuadas al alcance del proyecto y de diseñar aplicaciones pensando en su escalabilidad y mantenimiento futuro.

En conclusión, FoodHub representa una solución eficaz para la gestión de archivos .food, ofreciendo una plataforma web accesible, funcional y extensible. El proyecto demuestra la utilidad de las tecnologías empleadas y sienta las bases para posibles mejoras futuras, como la incorporación de sistemas de autenticación, análisis más avanzado de los datos alimentarios o la integración con bases de datos. En su estado actual, la aplicación cumple con los objetivos establecidos y constituye un resultado sólido y coherente dentro del marco del trabajo desarrollado. 

## Descripción del sistema

### 1. Visión general del sistema

El sistema desarrollado, denominado **FoodHub**, es una **aplicación web orientada a la gestión de archivos `.food`**, los cuales corresponden a ficheros en formato CSV que contienen información estructurada relacionada con alimentos. El propósito principal del sistema es ofrecer una plataforma centralizada que permita **almacenar, organizar y visualizar datos alimentarios** de manera sencilla, accesible y eficiente a través de un navegador web.

FoodHub ha sido diseñado como una aplicación ligera y modular, priorizando la claridad arquitectónica y la facilidad de uso. El sistema está pensado para ejecutarse en un entorno web estándar, sin necesidad de instalaciones adicionales por parte del usuario final, lo que garantiza su portabilidad y accesibilidad desde distintos dispositivos.

Desde un punto de vista conceptual, el sistema sigue una arquitectura **cliente–servidor**, en la que el navegador web actúa como cliente y un servidor desarrollado en Python, utilizando el framework Flask, se encarga de procesar las peticiones, gestionar los archivos `.food` y devolver las respuestas correspondientes.

---

### 2. Descripción funcional del sistema

Desde el punto de vista funcional, FoodHub proporciona un conjunto de funcionalidades orientadas a cumplir el objetivo principal del proyecto: la gestión eficiente de archivos `.food`.

#### 2.1. Carga de archivos `.food`

La funcionalidad central del sistema es la **carga de archivos `.food`** por parte del usuario. Estos archivos, al estar basados en el formato CSV, contienen información tabular que puede ser procesada y visualizada por la aplicación.

El proceso de carga incluye las siguientes acciones:

- Selección del archivo desde el dispositivo del usuario.
- Envío del archivo al servidor mediante un formulario web.
- Validación básica del archivo (extensión y estructura).
- Almacenamiento del archivo en el servidor para su uso posterior.

Esta funcionalidad permite centralizar la información alimentaria sin necesidad de que el usuario manipule directamente el sistema de archivos del servidor.

---

#### 2.2. Almacenamiento y gestión de archivos

Una vez cargados, los archivos `.food` son **almacenados de forma organizada** en el servidor. El sistema mantiene una estructura clara que facilita su localización y acceso posterior. Este enfoque permite gestionar múltiples archivos y evita conflictos o pérdidas de información.

El almacenamiento se ha diseñado pensando en la simplicidad y la claridad, evitando dependencias innecesarias y garantizando que el sistema pueda ampliarse fácilmente en el futuro, por ejemplo, mediante la integración con una base de datos.

---

#### 2.3. Visualización de datos

FoodHub permite la **visualización directa del contenido de los archivos `.food`** a través de la interfaz web. El sistema se encarga de:

- Leer el contenido del archivo CSV.
- Interpretar sus filas y columnas.
- Mostrar los datos de forma estructurada en el navegador.

Esta funcionalidad transforma datos en bruto en información comprensible, evitando que el usuario tenga que descargar el archivo o utilizar software externo para consultarlo.

---

#### 2.4. Navegación e interacción con la aplicación

La aplicación dispone de una **interfaz web sencilla e intuitiva**, que permite al usuario navegar entre las distintas secciones del sistema de forma clara. Se emplean enlaces y formularios bien definidos, lo que reduce la curva de aprendizaje y mejora la experiencia de usuario.

La navegación está diseñada para evitar comportamientos no deseados en la URL, garantizando que cada acción lleve a la ruta correspondiente y manteniendo una estructura de navegación coherente.

---

### 3. Arquitectura del sistema

Desde el punto de vista arquitectónico, FoodHub sigue una estructura clara basada en la separación de responsabilidades, lo que facilita el mantenimiento y la evolución del sistema.

#### 3.1. Arquitectura cliente–servidor

El sistema se basa en una arquitectura **cliente–servidor**, en la que:

- El **cliente** es el navegador web del usuario.
- El **servidor** es una aplicación desarrollada en Python con Flask.

Esta arquitectura permite una clara división entre la presentación y la lógica de negocio.

---

#### 3.2. Backend: Python y Flask

El backend del sistema está implementado en **Python**, utilizando el framework **Flask**. Las principales responsabilidades del backend son:

- Definición de rutas de la aplicación.
- Gestión de peticiones HTTP.
- Procesamiento de archivos `.food`.
- Comunicación con el sistema de archivos.
- Renderizado dinámico de las vistas HTML.

---

#### 3.3. Frontend: plantillas HTML

El frontend de FoodHub se basa en **plantillas HTML**, renderizadas dinámicamente desde Flask. Estas plantillas permiten reutilizar componentes comunes y mantener una apariencia consistente en toda la aplicación.

---

#### 3.4. Gestión de archivos

El sistema utiliza el **sistema de archivos del servidor** para almacenar los archivos `.food`. Esta decisión simplifica la arquitectura y resulta adecuada para el alcance actual del proyecto.

---

### 4. Relación entre componentes y subsistemas

El funcionamiento general del sistema sigue el siguiente flujo:

1. El usuario interactúa con la interfaz web.
2. El navegador envía peticiones HTTP al servidor.
3. Flask procesa la petición.
4. El sistema gestiona los archivos `.food` si es necesario.
5. El servidor devuelve una respuesta HTML.
6. El navegador muestra la información al usuario.

---

### 5. Despliegue del sistema

El sistema ha sido desplegado en un entorno accesible públicamente. La aplicación se encuentra disponible en:

- `foodhub-main-1.onrender.com`

Este despliegue permite validar el funcionamiento del sistema en un entorno real.

---

### 6. Cambios desarrollados para el proyecto

Los principales cambios y desarrollos realizados para este proyecto son:

- Desarrollo de una aplicación web completa con Python y Flask.
- Implementación de un sistema de carga de archivos `.food`.
- Validación básica de archivos CSV.
- Almacenamiento organizado de archivos en el servidor.
- Lectura e interpretación de datos CSV.
- Visualización estructurada de datos en la interfaz web.
- Creación de una interfaz clara e intuitiva.
- Uso de plantillas HTML reutilizables.
- Despliegue del sistema en un entorno público.

---

### 7. Consideraciones finales

FoodHub constituye una solución funcional y bien estructurada para la gestión de archivos `.food`. Su diseño modular y su arquitectura cliente–servidor facilitan la comprensión del sistema y permiten su ampliación futura con nuevas funcionalidades.


## Visión global del proceso de desarrollo

### 1. Introducción

El desarrollo del sistema **FoodHub** se ha llevado a cabo siguiendo un proceso estructurado y progresivo, orientado a la construcción de una aplicación web funcional, mantenible y fácilmente desplegable. A lo largo del proyecto se han aplicado conceptos fundamentales del desarrollo de software, combinando el uso de herramientas de programación, control de versiones, frameworks web y plataformas de despliegue.

El objetivo de este apartado es ofrecer una visión global del proceso de desarrollo seguido, explicando las distintas fases del ciclo de vida del software y su relación con las tecnologías y herramientas empleadas. Asimismo, se presenta un ejemplo de cambio propuesto al sistema y se describe cómo se abordaría dicho cambio desde su concepción hasta su puesta en producción.

---

### 2. Planificación y análisis de requisitos

La primera fase del proceso de desarrollo consistió en la **definición del objetivo del sistema** y el análisis de los requisitos funcionales y técnicos. En esta etapa se determinó que la aplicación debía permitir la gestión de archivos `.food`, entendidos como ficheros CSV con información alimentaria, y que debía ser accesible a través de un navegador web.

Los requisitos funcionales principales definidos fueron:

- Permitir la carga de archivos `.food`.
- Almacenar los archivos de forma organizada.
- Visualizar el contenido de los archivos desde la aplicación.
- Ofrecer una interfaz sencilla e intuitiva.

En cuanto a los requisitos técnicos, se estableció el uso de:

- **Python** como lenguaje de programación.
- **Flask** como framework web.
- Una arquitectura cliente–servidor.
- Despliegue en un entorno accesible públicamente.

Esta fase permitió acotar el alcance del proyecto y sentar las bases para el diseño del sistema.

---

### 3. Diseño del sistema

Una vez definidos los requisitos, se abordó la fase de **diseño**, tanto a nivel funcional como arquitectónico. En esta etapa se decidió adoptar una estructura modular que separase claramente la lógica de negocio, la gestión de archivos y la presentación de la información.

Se diseñó una arquitectura basada en:

- Rutas Flask para cada funcionalidad principal.
- Uso de plantillas HTML reutilizables.
- Gestión de archivos mediante el sistema de archivos del servidor.

El diseño priorizó la simplicidad y la claridad, evitando soluciones complejas innecesarias para el alcance del proyecto. Esta decisión facilitó el desarrollo posterior y redujo el riesgo de errores.

---

### 4. Implementación y desarrollo

La fase de **implementación** se llevó a cabo de forma incremental, desarrollando y probando cada funcionalidad de manera progresiva. El uso de Python y Flask permitió construir rápidamente una aplicación funcional y realizar ajustes de forma ágil.

Durante esta etapa se implementaron:

- Las rutas principales de la aplicación.
- Los formularios de carga de archivos.
- La lógica de validación básica de archivos `.food`.
- La lectura de archivos CSV desde el backend.
- La visualización de los datos en las plantillas HTML.

Cada nueva funcionalidad se probó de manera local antes de integrarla en el conjunto del sistema, lo que permitió detectar y corregir errores en fases tempranas.

---

### 5. Pruebas y validación

Las pruebas del sistema se realizaron de forma continua a lo largo del desarrollo. Dado el alcance del proyecto, se priorizaron las **pruebas manuales**, comprobando el correcto funcionamiento de cada funcionalidad desde el punto de vista del usuario.

Entre las comprobaciones realizadas destacan:

- Verificación de la carga correcta de archivos `.food`.
- Comprobación de la visualización adecuada de los datos.
- Validación del comportamiento de la navegación.
- Pruebas de funcionamiento en distintos navegadores.

Esta fase permitió asegurar que el sistema cumplía con los requisitos definidos y ofrecía una experiencia de uso coherente.

---

### 6. Control de versiones y gestión del código

Durante el desarrollo se utilizó un **sistema de control de versiones**, lo que permitió gestionar los cambios de forma ordenada y mantener un historial del proyecto. El control de versiones facilitó la incorporación de nuevas funcionalidades y la corrección de errores sin comprometer la estabilidad del sistema.

El uso de esta herramienta contribuyó a:

- Mantener el código organizado.
- Evitar pérdidas de trabajo.
- Facilitar la evolución del sistema.

---

### 7. Despliegue en producción

Una vez validado el funcionamiento del sistema en entorno local, se procedió al **despliegue en producción**. Para ello, se utilizó una plataforma de despliegue en la nube, que permite ejecutar aplicaciones web desarrolladas con Flask.

La aplicación fue desplegada en un entorno accesible públicamente, lo que permitió:

- Verificar el funcionamiento en condiciones reales.
- Comprobar la estabilidad del sistema.
- Permitir el acceso a usuarios externos.

El sistema se encuentra disponible en la siguiente dirección:

- `foodhub-main-1.onrender.com`

---

### 8. Ejemplo de cambio propuesto al sistema

Como ejemplo de evolución del sistema, se propone la incorporación de un **sistema de autenticación de usuarios** que permita gestionar el acceso a los archivos `.food`.

#### 8.1. Propuesta del cambio

El cambio consistiría en añadir un mecanismo de registro e inicio de sesión, de modo que cada usuario pueda acceder únicamente a sus propios archivos. Esta mejora aumentaría la seguridad y permitiría un uso más avanzado del sistema.

---

#### 8.2. Análisis del cambio

En esta fase se analizarían los requisitos del nuevo sistema de autenticación, definiendo:

- Tipos de usuarios.
- Flujo de registro e inicio de sesión.
- Requisitos de seguridad.

Este análisis permitiría evaluar el impacto del cambio sobre la arquitectura existente.

---

#### 8.3. Diseño del cambio

A nivel de diseño, el sistema requeriría:

- Nuevas rutas Flask para login y registro.
- Integración de una base de datos para usuarios.
- Modificación del flujo de navegación.
- Adaptación de las plantillas HTML.

El diseño se realizaría manteniendo la coherencia con la arquitectura actual.

---

#### 8.4. Implementación del cambio

La implementación se llevaría a cabo de forma incremental, añadiendo primero la estructura básica y posteriormente las funcionalidades avanzadas. Se realizarían pruebas locales para validar el correcto funcionamiento.

---

#### 8.5. Pruebas y despliegue del cambio

Una vez implementado el cambio, se realizarían pruebas para garantizar la estabilidad del sistema. Finalmente, el cambio se desplegaría en producción siguiendo el mismo proceso utilizado en el desarrollo inicial.

---

### 9. Consideraciones finales

El proceso de desarrollo seguido en FoodHub demuestra la aplicación práctica del ciclo de vida del software, desde la planificación inicial hasta el despliegue en producción. La utilización de herramientas adecuadas y un enfoque incremental han permitido desarrollar un sistema funcional, extensible y preparado para futuras mejoras.


### Entorno de desarrollo

El desarrollo del sistema **FoodHub** se ha realizado en un entorno de desarrollo orientado a la creación de aplicaciones web con Python, priorizando la portabilidad, la reproducibilidad y la simplicidad de configuración. Las herramientas y tecnologías empleadas permiten que el sistema pueda ejecutarse tanto en entornos locales como en plataformas de despliegue en la nube sin necesidad de cambios significativos en el código.

---

#### Sistema operativo

El entorno de desarrollo principal se ha basado en sistemas operativos de tipo **GNU/Linux**, aunque el sistema es compatible con otros sistemas operativos como Windows o macOS. El uso de Linux ha facilitado la gestión de dependencias, la ejecución del servidor de desarrollo y la similitud con el entorno de producción.

---

#### Lenguaje de programación

El lenguaje de programación utilizado ha sido **Python**, debido a su facilidad de uso, legibilidad y amplia adopción en el desarrollo de aplicaciones web y el tratamiento de datos.

- **Lenguaje**: Python  
- **Versión utilizada**: Python 3.10 o superior

Esta versión garantiza compatibilidad con Flask y con las librerías estándar utilizadas para el procesamiento de archivos CSV.

---

#### Framework web

Para el desarrollo de la aplicación web se ha utilizado el framework **Flask**, una herramienta ligera y flexible que permite construir aplicaciones web de forma rápida y modular.

- **Framework**: Flask  
- **Versión utilizada**: Flask 2.x

Flask se ha empleado para definir las rutas de la aplicación, gestionar las peticiones HTTP, procesar formularios y renderizar las vistas HTML.

---

#### Gestión de dependencias

La gestión de dependencias del proyecto se ha realizado mediante un archivo `requirements.txt`, en el que se especifican todas las librerías necesarias para ejecutar el sistema.

Las principales dependencias del proyecto son:

- `Flask`
- `Werkzeug`
- `Jinja2`

El uso de un archivo de dependencias permite reproducir el entorno de desarrollo de forma sencilla en cualquier sistema.

---

#### Entorno virtual

Para aislar las dependencias del proyecto y evitar conflictos con otras aplicaciones, se ha utilizado un **entorno virtual de Python**.

El uso de entornos virtuales permite:

- Mantener separadas las dependencias del proyecto.
- Evitar problemas de compatibilidad entre librerías.
- Facilitar la instalación del sistema en distintos equipos.

---

#### Editor y herramientas de desarrollo

El desarrollo del código se ha realizado utilizando editores de código modernos con soporte para Python y HTML. Entre las herramientas más utilizadas se encuentran:

- **Visual Studio Code**
- Terminal del sistema
- Navegador web para pruebas

Estas herramientas han permitido depurar el código, probar la aplicación localmente y validar el comportamiento del sistema.

---

#### Pasos para instalar y ejecutar el sistema

A continuación se describen los pasos necesarios para instalar y ejecutar el sistema FoodHub en un entorno local:

1. **Clonar el repositorio del proyecto**  
   ```bash
   git clone https://github.com/EGC-FoodHub/foodhub.git
   cd foodhub
   ```

### Uso de Inteligencia Artificial
Se ha usado Inteligencia Artificial durante el desarrollo y despligue de este proyecto, siendo de ayuda en el desarrollo de los Work Items, los tests y de comprensión de errores.

### Ejercicio de propuesta de cambio
El cambio propuesto se basa en actualizar el perfil para que el usuario pueda cambiar su contraseña sin necesidad de cerrar sesión y de pedir un código al correo.El cambio modificara las rutas, servicios y templates de auth, generar la issue, revisar la pull request y mergear en main.

### Conclusiones y trabajo futuro
En conclusión, el proyecto FoodHub ha logrado desarrollar una aplicación web funcional y bien estructurada para la gestión de archivos .food, cumpliendo con los objetivos principales de almacenamiento, visualización y accesibilidad web mediante el uso de Python y Flask.