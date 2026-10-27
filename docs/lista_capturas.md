# Lista de evidencias gráficas por capturar (las debe tomar el equipo)

No se incluyen capturas inventadas. Cada una debe tomarse del sistema real, ejecutándose en el equipo del grupo, y comentarse en el informe (sección 16 del informe). **No muestres contraseñas ni el archivo `.env`.**

| N.º | Evidencia | Qué debe verse |
|---|---|---|
| C01 | Versiones instaladas | `python --version`, `pip freeze` y `mysql --version` |
| C02 | Base de datos creada | `SHOW DATABASES;` con `festival_vallenato` |
| C03 | Migraciones | Salida de `python manage.py migrate` |
| C04 | Tablas en MySQL | `SHOW TABLES;` con las tablas `festival_*` |
| C05 | Estructura de una tabla | `DESCRIBE festival_votacion;` o Workbench |
| C06 | Carga de datos demo | Salida de `cargar_demo` |
| C07 | Servidor en ejecución | `runserver` sin errores |
| C08 | Inicio | `/` con edición 2027 |
| C09 | Ediciones y detalle | `/ediciones/` y `/ediciones/2027/` |
| C10 | Categorías | `/ediciones/2027/categorias/` |
| C11 | Votaciones | `/categorias/<id>/votaciones/` con estados |
| C12 | Detalle de votación | `/votaciones/<id>/` con opciones |
| C13 | Registro | Formulario y mensaje de error de validación |
| C14 | Login y logout | Inicio de sesión, mensaje de bienvenida y cierre de sesión |
| C15 | Página protegida | Redirección a login al abrir `/cuentas/perfil/` sin sesión |
| C16 | Admin: listados | Listado de votaciones con filtros y búsqueda |
| C17 | Admin: alta | Formulario de votación con opciones en línea |
| C18 | Datos en MySQL | `SELECT * FROM festival_votacion;` coincide con lo que muestra el sitio |
| C19 | Pruebas automatizadas | `python manage.py test` con el resultado final |
| C20 | Vista móvil | El sitio en ancho de teléfono (herramientas del navegador) |
| C21 | Repositorio | Página del repositorio de GitHub con los archivos |
