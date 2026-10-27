# Sistema de Votaciones del Festival de la Leyenda Vallenata 2027
## Informe de la Entrega 2 – Desarrollo con Python, Django y MySQL

**Institución:** Fundación Universitaria del Área Andina
**Programa:** Desarrollo WEB – 202660 – 6A – 63
**Asignatura:** Desarrollo Web
**Docente:** Deivys Morales Uribe
**Fecha de entrega:** [COMPLETAR]

**Integrantes:**
1. [COMPLETAR: nombre completo del integrante 1]
2. [COMPLETAR: nombre completo del integrante 2]
3. [COMPLETAR: nombre completo del integrante 3]
4. [COMPLETAR: nombre completo del integrante 4]

> Nota para el equipo: todo texto entre corchetes debe completarse o eliminarse antes de enviar. Este informe no incluye capturas, enlaces ni nombres inventados.

## 1. Introducción

El Festival de la Leyenda Vallenata, que se celebra en Valledupar (Cesar, Colombia), reúne concursos de acordeón, piqueria, canción inédita y desfile de piloneras, entre otras actividades. En la Entrega 1 de este proyecto se analizó el contexto del Festival, se compararon plataformas de votación digital y se diseñaron los requerimientos, los casos de uso, el modelo conceptual de datos y un prototipo de la plataforma.

Esta segunda entrega convierte ese diseño en una primera versión funcional. La aplicación permite consultar ediciones, categorías, votaciones y opciones participantes almacenadas en una base de datos MySQL, administrarlas desde Django Admin y registrar usuarios con inicio y cierre de sesión. La solución se desarrolló con Python y Django, siguiendo el patrón arquitectónico MVT (Django Software Foundation, s. f.).

Esta versión **no registra votos**. Las reglas de elegibilidad, frecuencia y publicación de resultados siguen pendientes de validación con el cliente, según las preguntas formuladas en la Entrega 1; por eso no se inventaron, y el diseño queda preparado para incorporarlas en una entrega posterior.

## 2. Objetivo general

Desarrollar una versión inicial funcional del sistema web de votaciones del Festival de la Leyenda Vallenata 2027, con Python, Django y MySQL, que permita consultar y administrar ediciones, categorías, votaciones y opciones participantes, y gestionar el acceso de usuarios.

## 3. Objetivos específicos

- Configurar un proyecto Django conectado a una base de datos MySQL mediante variables de entorno.
- Implementar los modelos Edición, Categoría, Votación y Opción participante con sus relaciones y restricciones de integridad.
- Habilitar la administración de los registros mediante Django Admin.
- Implementar el registro, el inicio y el cierre de sesión con el sistema de autenticación de Django.
- Desarrollar una interfaz responsive con HTML y CSS que muestre los datos consultados dinámicamente.
- Verificar el funcionamiento mediante pruebas automatizadas y documentar el procedimiento de instalación.

## 4. Alcance de la entrega

| Elemento | Estado |
|---|---|
| Modelos, relaciones y migraciones sobre MySQL | Incluido |
| Administración con Django Admin | Incluido |
| Registro, inicio y cierre de sesión | Incluido |
| Consulta pública de ediciones, categorías, votaciones y opciones | Incluido |
| Datos de demostración y pruebas automatizadas | Incluido |
| Emisión y registro de votos (CU-04) | No incluido: pendiente de reglas del cliente |
| Resultados y bitácora de auditoría (CU-08, RF13) | No incluido |
| Recuperación de contraseña (RF12) | No incluido: pendiente de validación |
| Despliegue en producción | No incluido |

## 5. Análisis y diseño del sistema

El análisis parte de la Entrega 1, de la cual se conservan la jerarquía Edición → Categoría → Votación → Opción (RN01 y RN10), los actores (visitante, votante y administrador), los estados de la votación y la identidad visual en verde y dorado. Las pantallas del prototipo 1 a 6 (inicio, registro, inicio de sesión, categorías, votaciones y detalle) corresponden a las páginas implementadas.

Se tomaron las siguientes decisiones respecto al diseño inicial:

- **Campo `regla_frecuencia`:** no se incluyó, porque la regla (RN04) sigue pendiente de validación; se añadirá con una migración cuando el cliente la defina.
- **Regla RN02:** se implementó la validación de que una votación necesita al menos dos opciones activas para abrirse.
- **Bootstrap:** se reemplazó por CSS propio, porque el enunciado exige no depender de servicios externos.
- **Inicio de sesión:** se hace con nombre de usuario, mecanismo estándar de Django, y el correo se exige único en el registro.
- **Roles:** se usan las banderas `is_staff` e `is_superuser` de Django; no se implementó autorización avanzada.

## 6. Arquitectura de la aplicación y patrón MVT

Django organiza la aplicación en tres componentes: modelo, plantilla y vista, enlazados por un despachador de URL (Django Software Foundation, s. f.).

- **Model (`festival/models.py`):** define las entidades, sus atributos, validaciones y relaciones.
- **View (`festival/views.py`, `accounts/views.py`):** recibe la solicitud, consulta los modelos con el ORM y elige la plantilla.
- **Template (`templates/`):** presenta la información en HTML con los datos que envía la vista.
- **URLconf (`config/urls.py` y `urls.py` de cada aplicación):** relaciona cada ruta con su vista.

Conceptualmente, el modelo de Django equivale al modelo de MVC, la plantilla cumple el papel de la vista de MVC y la vista de Django cumple el papel del controlador. La equivalencia es conceptual: Django no usa exactamente la nomenclatura de otros marcos MVC.

El proyecto se divide en dos aplicaciones: `festival` (dominio) y `accounts` (autenticación). Esta separación mantiene cada responsabilidad en su propio módulo.

## 7. Tecnologías utilizadas y justificación

| Tecnología | Justificación |
|---|---|
| Python 3.12 | Lenguaje exigido; compatible con Django 5.2 (Python Software Foundation, s. f.). |
| Django 5.2 (LTS) | Versión de soporte extendido, con ORM, autenticación, administración y protección CSRF integrados. |
| MySQL 8 | Motor relacional exigido (Oracle Corporation, s. f.). Se usa codificación `utf8mb4` para tildes y la letra ñ. |
| mysqlclient | Controlador recomendado por Django para MySQL. |
| python-dotenv | Mantiene las credenciales fuera del código. |
| Pillow | Requerido por `ImageField` para las imágenes opcionales de las opciones. |
| HTML5 y CSS3 propios | Interfaz adaptable sin dependencias externas. |
| JavaScript | Solo para el menú desplegable en pantallas pequeñas. |
| Git y GitHub | Control de versiones y publicación del código. |

## 8. Modelo de datos, entidades y relaciones

La estructura principal es **Edición → Categoría → Votación → Opción participante**.

| Entidad | Campos principales | Restricciones |
|---|---|---|
| Edición | año, nombre, descripción, fechas, publicada | Año único; fecha final no anterior a la inicial |
| Categoría | edición (FK), nombre, descripción, activa | Nombre único por edición |
| Votación | categoría (FK), título, descripción, fecha de apertura y de cierre, estado | Título único por categoría; abrir exige dos opciones activas |
| Opción participante | votación (FK), nombre, descripción, imagen, activa | Nombre único por votación |

Todas las claves foráneas usan `on_delete=PROTECT`: no es posible eliminar un registro que tenga registros hijos, lo que evita pérdidas accidentales de información. Las restricciones únicas evitan duplicados dentro de cada padre, pero permiten, por ejemplo, la misma categoría en dos ediciones distintas. Cada entidad incluye el campo `es_demo`, que identifica los datos de demostración para poder eliminarlos sin afectar datos reales.

Para la autenticación se usa el modelo `User` incorporado en Django. No se almacenan contraseñas manualmente.

**Preparación para entregas futuras.** Un modelo `Voto` se relacionaría con `User` y con `OpcionParticipante`, con una restricción única `(usuario, votación)` si el cliente define un voto por votación. Los estados y las fechas de apertura y cierre de la votación ya existen. La bitácora y los resultados se construirían con nuevos modelos y agregaciones del ORM.

## 9. Configuración de MySQL

La conexión se configura en `config/settings.py` con el motor `django.db.backends.mysql`. El nombre de la base, el usuario, la contraseña, el host y el puerto se leen desde variables de entorno definidas en un archivo `.env` que no se sube al repositorio; el archivo `.env.example` entrega valores de ejemplo sin secretos.

Crear la base de datos y el usuario se hace en MySQL; en cambio, las **tablas** las crea Django mediante las migraciones. Los pasos de creación están documentados en el README. Se usa la codificación `utf8mb4` y el modo estricto `STRICT_TRANS_TABLES`, para que MySQL no trunque datos en silencio.

## 10. Implementación de modelos y migraciones

Los modelos se definen en `festival/models.py`. El comando `makemigrations` generó `festival/migrations/0001_initial.py` y `migrate` creó en MySQL las tablas `festival_edicion`, `festival_categoria`, `festival_votacion` y `festival_opcionparticipante`, además de las tablas de autenticación y sesiones.

En el entorno de desarrollo se comprobó con `information_schema` que las tres restricciones únicas compuestas, la restricción única del año y las tres claves foráneas existen en la base de datos. [INSERTAR CAPTURAS C03, C04 y C05]

## 11. Administración mediante Django Admin

Los cuatro modelos están registrados en `festival/admin.py` con listados, búsqueda, filtros y ordenamiento. Las categorías se editan dentro de la edición y las opciones dentro de la votación, mediante formularios en línea. Al guardar una votación como «abierta» con menos de dos opciones activas, el administrador la guarda como borrador y muestra una advertencia (regla RN02). El acceso a `/admin/` exige un usuario con permisos de administración. [INSERTAR CAPTURAS C16 y C17]

## 12. Registro, inicio y cierre de sesión

- **Registro:** `RegistroForm` extiende el formulario de creación de usuarios de Django y agrega el correo electrónico, que debe ser único, y la aceptación del tratamiento de datos (Ley 1581 de 2012).
- **Contraseñas:** se almacenan con PBKDF2 y se validan con los validadores de Django.
- **Inicio de sesión:** vista de autenticación de Django, con mensajes de éxito y de error.
- **Cierre de sesión:** solo acepta solicitudes POST, con token CSRF.
- **Páginas públicas:** inicio, ediciones, categorías, votaciones, detalle, registro e inicio de sesión.
- **Página protegida:** `/cuentas/perfil/`, que redirige al inicio de sesión si no hay sesión activa.

No se implementó autorización avanzada: solo existe la diferencia de Django entre usuario normal y personal administrativo. [INSERTAR CAPTURAS C13, C14 y C15]

## 13. Desarrollo de interfaces con HTML y CSS

La interfaz usa una plantilla base con cabecera, navegación, mensajes y pie de página con la información del proyecto académico. El diseño es de prioridad móvil, con cuadrícula adaptable y menú desplegable. La paleta, verde profundo y dorado, es la del prototipo de la Entrega 1; incluye contraste alto, enlace para saltar al contenido y estilos de foco visibles, siguiendo como referencia las pautas WCAG 2.1 (W3C, 2018). Las páginas muestran mensajes cuando no hay información y distinguen los datos de demostración con una insignia. No hay botones ni formularios sin función. [INSERTAR CAPTURAS C08 a C12 y C20]

## 14. Vistas, rutas y consultas dinámicas

| Ruta | Vista | Consulta principal |
|---|---|---|
| `/` | `inicio` | Edición publicada más reciente, sus categorías activas y votaciones abiertas |
| `/ediciones/` | `ediciones` | Ediciones publicadas, con paginación |
| `/ediciones/<año>/` | `edicion_detalle` | Edición y sus categorías activas |
| `/ediciones/<año>/categorias/` | `categorias_edicion` | Categorías activas, con paginación |
| `/categorias/<id>/votaciones/` | `votaciones_categoria` | Votaciones que no estén en borrador |
| `/votaciones/<id>/` | `votacion_detalle` | Votación y sus opciones activas |

Todos los datos se obtienen con el ORM; ningún registro está escrito en las plantillas. Las ediciones no publicadas, las categorías inactivas, las votaciones en borrador y los identificadores inexistentes responden con error 404.

## 15. Pruebas realizadas y resultados

Se escribieron 44 pruebas automatizadas con `django.test.TestCase`: 29 del dominio y 15 de autenticación. Cubren la creación de ediciones, las relaciones, las restricciones de unicidad y de eliminación, las respuestas de las páginas públicas, los casos sin registros, los identificadores inexistentes, el registro, el inicio y el cierre de sesión, la protección CSRF, el administrador y los datos de demostración.

**Resultado verificado:** la ejecución de `python manage.py test` en un entorno Linux (Ubuntu 24.04, Python 3.12.3, MySQL 8.0.46, Django 5.2.18) terminó con 44 pruebas, 0 fallos y 0 errores, usando una base de datos de pruebas en MySQL. La misma ejecución se repitió en una instalación nueva, creada desde el archivo `requirements.txt` y con una base de datos vacía, con el mismo resultado. Además, un servidor de desarrollo respondió con código 200 en todas las páginas públicas y con 404 en los identificadores inexistentes.

**Pendiente de ejecución por el equipo:** repetir las 44 pruebas en Windows y realizar las pruebas manuales M01 a M06 (conexión, administración en navegador, imágenes, diseño responsive, flujo de usuario e instalación desde cero). El detalle está en `docs/tabla_pruebas.md`. [COMPLETAR: resultado de la ejecución del equipo en Windows]

## 16. Evidencias gráficas comentadas

[INSERTAR AQUÍ las capturas reales C01 a C21 de `docs/lista_capturas.md`, cada una con un pie de figura y un comentario de dos o tres líneas que explique qué demuestra.]

## 17. Enlace al repositorio

[COMPLETAR: enlace al repositorio de GitHub una vez publicado]

## 18. Enlace al video de demostración

[COMPLETAR: enlace al video una vez grabado y publicado]

## 19. Dificultades, soluciones y limitaciones

**Dificultades y soluciones**

- *Reglas del cliente sin definir:* varias reglas siguen pendientes de validación. Se implementó solo lo confirmado por el enunciado y se documentó cómo se incorporará el resto.
- *Validar la regla de las dos opciones al crear una votación:* en Django Admin las opciones se guardan después de la votación. Se resolvió comprobando la regla al terminar de guardar las opciones.
- *Dependencia externa de la Entrega 1:* el prototipo mencionaba Bootstrap; se reemplazó por CSS propio.
- *Instalación del controlador de MySQL en Windows:* si `mysqlclient` no se instala, el README documenta la alternativa con PyMySQL.

**Limitaciones**

- No se registran votos ni se publican resultados.
- No hay recuperación de contraseña ni verificación de correo.
- No hay autorización avanzada.
- No se desplegó la aplicación; para producción faltaría configurar HTTPS y HSTS.
- Las imágenes subidas se muestran solo con `DEBUG=True`.

## 20. Distribución de responsabilidades

Cada integrante debe confirmar y ajustar su tarea real; lo siguiente es una propuesta.

| Integrante | Responsabilidad propuesta |
|---|---|
| [COMPLETAR: nombre] | Entorno, configuración de MySQL, migraciones y repositorio |
| [COMPLETAR: nombre] | Modelos, relaciones, Django Admin y datos de demostración |
| [COMPLETAR: nombre] | Autenticación, formularios y pruebas automatizadas |
| [COMPLETAR: nombre] | Vistas, plantillas, CSS, informe y video |

## 21. Conclusiones

- La jerarquía Edición → Categoría → Votación → Opción, definida en la Entrega 1, se implementó con relaciones e integridad verificadas en MySQL.
- Django Admin permite administrar los datos sin programar interfaces adicionales, y las páginas públicas los muestran dinámicamente.
- La autenticación se apoyó en los mecanismos de Django, que evitan almacenar contraseñas en texto plano e incluyen protección CSRF.
- Las pruebas automatizadas respaldan el comportamiento y facilitarán incorporar el registro de votos sin romper lo existente.
- El paso siguiente es validar con el cliente las reglas pendientes: registro del votante, frecuencia de voto y publicación de resultados.

## 22. Referencias bibliográficas

[VERIFICAR: abra cada enlace y agregue la fecha de consulta si su docente lo exige.]

Congreso de la República de Colombia. (2012). *Ley Estatutaria 1581 de 2012, por la cual se dictan disposiciones generales para la protección de datos personales.*

Django Software Foundation. (s. f.). *Django documentation* (versión 5.2). https://docs.djangoproject.com/en/5.2/

Oracle Corporation. (s. f.). *MySQL 8.0 reference manual.* https://dev.mysql.com/doc/refman/8.0/en/

OWASP Foundation. (s. f.). *OWASP Top Ten.* https://owasp.org/www-project-top-ten/

PyMySQL. (s. f.). *mysqlclient* [Repositorio de código]. GitHub. https://github.com/PyMySQL/mysqlclient

Python Software Foundation. (s. f.). *Python 3 documentation.* https://docs.python.org/3/

W3C. (2018). *Web content accessibility guidelines (WCAG) 2.1.* https://www.w3.org/TR/WCAG21/
