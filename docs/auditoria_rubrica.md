# Auditoría final de requisitos

**Estados:** ✅ Implementado y verificado · 🟡 Implementado, pendiente de verificación · ⏳ Pendiente · ➖ No aplicable en esta entrega

**Dónde se verificó:** «Entorno de Claude» = Ubuntu 24.04, Python 3.12.3, MySQL 8.0.46, Django 5.2.18 (corrida de 44 pruebas, instalación desde cero con `requirements.txt` y servidor de desarrollo consultado con `curl`). **Ninguna verificación se hizo todavía en Windows ni con un navegador.**

| # | Requisito | Estado | Evidencia / observación |
|---|---|---|---|
| 1 | Django configurado | ✅ | `manage.py check` sin errores; servidor responde |
| 2 | Conexión real a MySQL (sin SQLite) | ✅ entorno de Claude · 🟡 Windows | `settings.py` usa `django.db.backends.mysql`; migraciones y pruebas corrieron sobre MySQL 8.0.46 |
| 3 | Modelos y relaciones correctos | ✅ | T01–T09; llaves y restricciones comprobadas en `information_schema` |
| 4 | Migraciones ejecutables | ✅ | `migrate` en base vacía; `makemigrations --check` sin cambios pendientes |
| 5 | Django Admin funcional | ✅ pruebas automatizadas · 🟡 uso en navegador | T25–T29; falta prueba manual M02 |
| 6 | Registro, inicio y cierre de sesión | ✅ pruebas automatizadas · 🟡 flujo en navegador | A01–A15 (cierre por POST con CSRF); falta M05 |
| 7 | Ediciones, categorías, votaciones y opciones administrables | ✅ | T26–T29 |
| 8 | Datos consultados dinámicamente (ORM, sin datos en plantillas) | ✅ | T10–T22; `curl` sobre el servidor con MySQL |
| 9 | Las 12 páginas/elementos mínimos de la sección 9 | ✅ | Todas responden 200 (o 302/404 según el caso) |
| 10 | Paginación y 404 para registros inexistentes | ✅ | T15, T14, T17, T20 |
| 11 | Interfaz con CSS propio y responsive | 🟡 | El CSS se sirve (200) pero **no se revisó visualmente en un navegador**; falta M04 |
| 12 | Datos de prueba que no se duplican y limpieza segura | ✅ | T23, T24; ejecutado dos veces en MySQL |
| 13 | Pruebas automatizadas documentadas | ✅ | 44 pruebas en `docs/tabla_pruebas.md` |
| 14 | Pruebas manuales | ⏳ | M01–M06 por ejecutar |
| 15 | Ejecución de las pruebas en Windows | ⏳ | Debe hacerla el equipo |
| 16 | Código listo para GitHub (`.gitignore`, `.env.example`, sin `.env`) | ✅ | El paquete no contiene `.env` |
| 17 | Repositorio publicado y enlace | ⏳ | Debe publicarlo el equipo |
| 18 | README completo | ✅ contenido · 🟡 pasos en Windows | Instrucciones de Windows no probadas en Windows |
| 19 | Documentación técnica (MVT, modelo, MySQL, flujo HTTP) | ✅ | `docs/documentacion_tecnica.md` |
| 20 | Informe académico (APA 7) | 🟡 | Redactado; contiene marcadores [COMPLETAR]; referencias por verificar |
| 21 | Evidencias gráficas reales | ⏳ | Lista de 21 capturas en `docs/lista_capturas.md` |
| 22 | Guion de video con 4 integrantes | 🟡 | Guion listo; cada integrante debe confirmar su parte; video por grabar |
| 23 | Enlace al video | ⏳ | Pendiente |
| 24 | Votación definitiva, elegibilidad, duplicados, auditoría, resultados | ➖ | Fuera de alcance; diseño preparado (documentación técnica, sección 6) |
| 25 | Recuperación de contraseña | ➖ | Pendiente de validación con el cliente |
| 26 | Despliegue en producción | ➖ | No exigido; `check --deploy` advierte HTTPS/HSTS |
| 27 | Rúbricas de 25 y 20 puntos | ⏳ | No se recibió el texto de las rúbricas; el equipo debe contrastar cada criterio con esta lista |

## Acciones que quedan a cargo del equipo

1. Instalar Python 3.12, MySQL 8 y Git en Windows, y seguir el README.
2. Crear la base de datos y el usuario con su propia contraseña y generar su `DJANGO_SECRET_KEY`.
3. Ejecutar `migrate`, `createsuperuser`, `cargar_demo` y `python manage.py test`, y anotar los resultados reales.
4. Abrir el sitio en un navegador, revisar el diseño en pantalla de teléfono y ejecutar las pruebas manuales M01–M06.
5. Tomar las 21 capturas reales.
6. Completar el informe: fecha, nombres, responsabilidades, capturas, enlaces y resultado en Windows; verificar las referencias.
7. Publicar el repositorio (revisar con `git status` que no aparezca `.env`).
8. Grabar y publicar el video y agregar su enlace.
9. Contrastar la entrega con las dos rúbricas.
