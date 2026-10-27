# Tabla de pruebas

## Condiciones del entorno donde se ejecutaron las pruebas automatizadas

- Ejecutadas con `python manage.py test` por **Claude** en un entorno Linux: Ubuntu 24.04, Python 3.12.3, **MySQL 8.0.46**, Django 5.2.18, mysqlclient 2.3.0.
- Resultado de la corrida: **44 pruebas, 0 fallos, 0 errores** (base temporal `test_festival_vallenato` en MySQL).
- **Pendiente:** el equipo debe repetir la corrida en su equipo con Windows y registrar su propio resultado en la columna «Resultado obtenido (equipo)».
- Las pruebas manuales (M01–M06) **no se han ejecutado**; las debe hacer el equipo.

## Pruebas automatizadas

| Código | Funcionalidad | Procedimiento | Resultado esperado | Resultado obtenido (entorno de Claude) | Estado |
|---|---|---|---|---|---|
| T01 | Creación de ediciones | Crear `Edicion` con el ORM | Se guarda; `__str__` correcto; no publicada por defecto | Coincide con lo esperado (OK) | Verificada en entorno de Claude; pendiente de repetir en Windows |
| T02 | Unicidad del año | Crear dos ediciones con el mismo año | `IntegrityError` | Coincide con lo esperado (OK) | Verificada en entorno de Claude; pendiente de repetir en Windows |
| T03 | Relaciones en cadena | Crear Edición→Categoría→Votación→3 Opciones y recorrerlas | Relaciones directas e inversas correctas | Coincide con lo esperado (OK) | Verificada en entorno de Claude; pendiente de repetir en Windows |
| T04 | Unicidad de categoría por edición | Repetir nombre en la misma edición y en otra | Rechaza el duplicado; permite el mismo nombre en otra edición | Coincide con lo esperado (OK) | Verificada en entorno de Claude; pendiente de repetir en Windows |
| T05 | Unicidad de votación y opción | Repetir título en la categoría y nombre en la votación | `IntegrityError` en ambos | Coincide con lo esperado (OK) | Verificada en entorno de Claude; pendiente de repetir en Windows |
| T06 | Validación de fechas de edición | `full_clean` con fin anterior al inicio | `ValidationError` | Coincide con lo esperado (OK) | Verificada en entorno de Claude; pendiente de repetir en Windows |
| T07 | Eliminación protegida | Borrar edición, categoría y votación con hijos | `ProtectedError` | Coincide con lo esperado (OK) | Verificada en entorno de Claude; pendiente de repetir en Windows |
| T08 | Regla RN02 en el modelo | Abrir votación con 1 opción y luego con 2 | Rechaza con 1; acepta con 2 | Coincide con lo esperado (OK) | Verificada en entorno de Claude; pendiente de repetir en Windows |
| T09 | Validación de fechas de votación | Cierre anterior a la apertura | `ValidationError` | Coincide con lo esperado (OK) | Verificada en entorno de Claude; pendiente de repetir en Windows |
| T10 | Inicio con datos | GET `/` con datos en BD | 200; muestra edición, categoría y votación abierta | Coincide con lo esperado (OK) | Verificada en entorno de Claude; pendiente de repetir en Windows |
| T11 | Inicio sin registros | GET `/` con BD vacía | 200; mensaje «Aún no hay ediciones publicadas» | Coincide con lo esperado (OK) | Verificada en entorno de Claude; pendiente de repetir en Windows |
| T12 | Lista de ediciones | GET `/ediciones/` con una publicada y una no | 200; solo la publicada | Coincide con lo esperado (OK) | Verificada en entorno de Claude; pendiente de repetir en Windows |
| T13 | Ediciones sin registros | GET `/ediciones/` con BD vacía | 200; mensaje de lista vacía | Coincide con lo esperado (OK) | Verificada en entorno de Claude; pendiente de repetir en Windows |
| T14 | Detalle de edición y 404 | GET año existente, inexistente y no publicado | 200 / 404 / 404 | Coincide con lo esperado (OK) | Verificada en entorno de Claude; pendiente de repetir en Windows |
| T15 | Categorías con paginación | 10 categorías; GET página 1 y 2; año inexistente | 9 y 1 elementos; 404 para año inexistente | Coincide con lo esperado (OK) | Verificada en entorno de Claude; pendiente de repetir en Windows |
| T16 | Categoría inactiva | Desactivar categoría y consultarla | 404; no aparece en el listado | Coincide con lo esperado (OK) | Verificada en entorno de Claude; pendiente de repetir en Windows |
| T17 | Votaciones de una categoría | Categoría con votación abierta y borrador; id inexistente | Oculta el borrador; 404 para id inexistente | Coincide con lo esperado (OK) | Verificada en entorno de Claude; pendiente de repetir en Windows |
| T18 | Categoría sin votaciones | GET categoría vacía | 200; mensaje «aún no tiene votaciones» | Coincide con lo esperado (OK) | Verificada en entorno de Claude; pendiente de repetir en Windows |
| T19 | Opciones activas en detalle | Votación con opciones activas e inactiva | Muestra solo las activas | Coincide con lo esperado (OK) | Verificada en entorno de Claude; pendiente de repetir en Windows |
| T20 | Votación borrador/inexistente | GET borrador e id inexistente | 404 en ambos | Coincide con lo esperado (OK) | Verificada en entorno de Claude; pendiente de repetir en Windows |
| T21 | Votación sin opciones | GET votación sin opciones | 200; mensaje «todavía no tiene opciones» | Coincide con lo esperado (OK) | Verificada en entorno de Claude; pendiente de repetir en Windows |
| T22 | Sin botones falsos | GET detalle de votación | No existe botón «Votar»; aviso de función futura | Coincide con lo esperado (OK) | Verificada en entorno de Claude; pendiente de repetir en Windows |
| T23 | Datos demo idempotentes | Ejecutar `cargar_demo` dos veces | Mismo conteo de registros | Coincide con lo esperado (OK) | Verificada en entorno de Claude; pendiente de repetir en Windows |
| T24 | Limpieza segura | `cargar_demo --limpiar` con datos reales presentes | Borra solo `es_demo=True` | Coincide con lo esperado (OK) | Verificada en entorno de Claude; pendiente de repetir en Windows |
| T25 | Admin exige login | GET `/admin/festival/edicion/` anónimo | 302 a `/admin/login/` | Coincide con lo esperado (OK) | Verificada en entorno de Claude; pendiente de repetir en Windows |
| T26 | Admin lista los 4 modelos | Superusuario consulta los 4 listados | 200 en los 4 | Coincide con lo esperado (OK) | Verificada en entorno de Claude; pendiente de repetir en Windows |
| T27 | Admin crea edición | POST de alta en admin | 302; registro guardado en BD | Coincide con lo esperado (OK) | Verificada en entorno de Claude; pendiente de repetir en Windows |
| T28 | Admin: abrir con <2 opciones | Alta de votación «abierta» con 1 opción | Queda en borrador | Coincide con lo esperado (OK) | Verificada en entorno de Claude; pendiente de repetir en Windows |
| T29 | Admin: abrir con 2 opciones | Alta de votación «abierta» con 2 opciones | Queda abierta | Coincide con lo esperado (OK) | Verificada en entorno de Claude; pendiente de repetir en Windows |
| A01 | Página de registro | GET `/cuentas/registro/` | 200 | Coincide con lo esperado (OK) | Verificada en entorno de Claude; pendiente de repetir en Windows |
| A02 | Registro válido | POST con datos válidos | Crea usuario, contraseña PBKDF2, redirige a login con mensaje | Coincide con lo esperado (OK) | Verificada en entorno de Claude; pendiente de repetir en Windows |
| A03 | Contraseñas distintas | POST con contraseñas diferentes | Error; no crea usuario | Coincide con lo esperado (OK) | Verificada en entorno de Claude; pendiente de repetir en Windows |
| A04 | Correo duplicado | POST con correo ya usado (otra capitalización) | Error; no crea usuario | Coincide con lo esperado (OK) | Verificada en entorno de Claude; pendiente de repetir en Windows |
| A05 | Datos personales | POST sin aceptar el tratamiento de datos | Error; no crea usuario | Coincide con lo esperado (OK) | Verificada en entorno de Claude; pendiente de repetir en Windows |
| A06 | Contraseña común | POST con «password» | Rechazada por validadores | Coincide con lo esperado (OK) | Verificada en entorno de Claude; pendiente de repetir en Windows |
| A07 | CSRF en registro | POST sin token con `enforce_csrf_checks` | 403 | Coincide con lo esperado (OK) | Verificada en entorno de Claude; pendiente de repetir en Windows |
| A08 | Login correcto | POST credenciales válidas | Redirige al inicio; mensaje de bienvenida; sesión activa | Coincide con lo esperado (OK) | Verificada en entorno de Claude; pendiente de repetir en Windows |
| A09 | Login incorrecto | POST credenciales erróneas | 200; mensaje de error; sin sesión | Coincide con lo esperado (OK) | Verificada en entorno de Claude; pendiente de repetir en Windows |
| A10 | Logout por POST | POST `/cuentas/logout/` | Sesión cerrada; mensaje; redirige al inicio | Coincide con lo esperado (OK) | Verificada en entorno de Claude; pendiente de repetir en Windows |
| A11 | Logout por GET | GET `/cuentas/logout/` | 405; la sesión sigue activa | Coincide con lo esperado (OK) | Verificada en entorno de Claude; pendiente de repetir en Windows |
| A12 | CSRF en logout | POST sin token | 403 | Coincide con lo esperado (OK) | Verificada en entorno de Claude; pendiente de repetir en Windows |
| A13 | Página protegida | GET `/cuentas/perfil/` sin y con sesión | 302 a login / 200 | Coincide con lo esperado (OK) | Verificada en entorno de Claude; pendiente de repetir en Windows |
| A14 | Registro con sesión | GET registro autenticado | Redirige al inicio | Coincide con lo esperado (OK) | Verificada en entorno de Claude; pendiente de repetir en Windows |
| A15 | Navegación según sesión | GET inicio anónimo y autenticado | Cambia entre «Iniciar sesión» y «Cerrar sesión» (con token CSRF) | Coincide con lo esperado (OK) | Verificada en entorno de Claude; pendiente de repetir en Windows |

## Pruebas manuales

| Código | Funcionalidad | Procedimiento | Resultado esperado | Resultado obtenido | Estado |
|---|---|---|---|---|---|
| M01 | Conexión real a MySQL | `migrate` y `SHOW TABLES` en Windows | 4 tablas del festival + tablas de autenticación | _(completar)_ | Pendiente de ejecución |
| M02 | Django Admin en navegador | Crear una edición, una categoría, una votación y 2 opciones desde `/admin/` | Registros guardados y visibles en el sitio público | _(completar)_ | Pendiente de ejecución |
| M03 | Subida de imagen de opción | Cargar una imagen desde el admin y verla en el detalle | La imagen aparece (con `DEBUG=True`) | _(completar)_ | Pendiente de ejecución |
| M04 | Diseño responsive | Probar en 360 px, 768 px y escritorio | Sin desbordes; menú móvil funcional | _(completar)_ | Pendiente de ejecución |
| M05 | Flujo completo de usuario | Registrarse → iniciar sesión → ver perfil → cerrar sesión | Mensajes y redirecciones correctos | _(completar)_ | Pendiente de ejecución |
| M06 | Instalación desde cero en Windows | Seguir el README en un equipo limpio | Servidor arranca sin errores | _(completar)_ | Pendiente de ejecución |
