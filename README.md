# Sistema de Votaciones – Festival de la Leyenda Vallenata 2027

Proyecto académico de **Desarrollo Web** (Fundación Universitaria del Área Andina) – **Entrega 2**.
Aplicación web en **Python + Django (patrón MVT)** con base de datos **MySQL**.

> Proyecto de estudiantes, sin vinculación oficial con la Fundación Festival de la Leyenda Vallenata.
> Los datos cargados con `cargar_demo` son **de demostración** (nombres ficticios).

## 1. Qué hace esta versión

- Consulta de **ediciones → categorías → votaciones → opciones participantes**, leídas de MySQL con el ORM.
- Administración completa con **Django Admin** (`/admin/`).
- **Registro, inicio y cierre de sesión** con `django.contrib.auth` (cierre por POST con CSRF).
- Interfaz responsive con CSS propio (sin CDN ni servicios externos).
- 44 pruebas automatizadas (`TestCase`).

**Fuera de alcance (entregas futuras):** registro de votos, reglas de elegibilidad, prevención de votos duplicados, auditoría, resultados y recuperación de contraseña. El diseño ya queda preparado (ver `docs/documentacion_tecnica.md`, sección 6).

## 2. Tecnologías

| Tecnología | Versión | Uso |
|---|---|---|
| Python | 3.12 (3.10–3.13 compatibles con Django 5.2) | Lenguaje |
| Django | 5.2.18 (LTS) | Framework web |
| MySQL | 8.0 o superior | Base de datos |
| mysqlclient | 2.3.0 | Controlador MySQL |
| Pillow | 13.0.0 | Imágenes opcionales de las opciones |
| python-dotenv | 1.2.4 | Variables de entorno |

Las versiones exactas están en `requirements.txt`.

## 3. Requisitos previos (Windows)

1. **Python 3.12** (marca «Add python.exe to PATH» al instalar).
2. **MySQL Server 8.x** (y opcionalmente MySQL Workbench).
3. **Git** y **Visual Studio Code**.

## 4. Estructura

```
festival_vallenato/
├── manage.py                 # Punto de entrada de comandos Django
├── requirements.txt          # Dependencias con versión exacta
├── .env.example              # Plantilla de variables de entorno (sin secretos)
├── .gitignore                # Excluye .env, venv, media, __pycache__
├── config/                   # Configuración global
│   ├── settings.py           # MySQL, apps, autenticación, estáticos
│   ├── urls.py               # URLconf raíz
│   └── wsgi.py / asgi.py
├── accounts/                 # Registro, login, logout y perfil
│   ├── forms.py  views.py  urls.py  tests.py
│   └── templates/accounts/   # registro.html, perfil.html
├── festival/                 # Dominio: Edición, Categoría, Votación, Opción
│   ├── models.py  admin.py  views.py  urls.py  tests.py
│   ├── management/commands/cargar_demo.py
│   ├── templates/festival/   # Páginas públicas
│   └── static/festival/      # css/estilo.css, js/menu.js
├── templates/                # base.html, 404.html, registration/login.html
└── docs/                     # Documentación técnica, informe, pruebas, guion
```

## 5. Instalación paso a paso (PowerShell o terminal de VS Code)

```powershell
# 1) Entrar a la carpeta del proyecto
cd festival_vallenato

# 2) Crear y activar el entorno virtual
python -m venv venv
venv\Scripts\activate

# 3) Instalar dependencias
pip install -r requirements.txt
```

Si PowerShell bloquea la activación: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

## 6. Configurar MySQL

**Crear la base de datos y el usuario NO lo hace Django**; eso se hace en MySQL. **Las tablas sí las crean las migraciones de Django.**

Abre «MySQL 8.x Command Line Client» (o Workbench) como `root` y ejecuta:

```sql
CREATE DATABASE festival_vallenato CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'festival_user'@'localhost' IDENTIFIED BY 'ESCRIBE_UNA_CONTRASENA_PROPIA';
GRANT ALL PRIVILEGES ON festival_vallenato.* TO 'festival_user'@'localhost';
-- Necesario para que Django cree la base temporal de pruebas:
GRANT ALL PRIVILEGES ON `test_festival_vallenato`.* TO 'festival_user'@'localhost';
FLUSH PRIVILEGES;
```

## 7. Variables de entorno

```powershell
copy .env.example .env
```

Edita `.env` con tu contraseña real y una `DJANGO_SECRET_KEY` propia. Para generar una:

```powershell
python -c "from django.core.management.utils import get_random_secret_key as k; print(k())"
```

`.env` está en `.gitignore`: **nunca lo subas a GitHub**.

| Variable | Descripción |
|---|---|
| `DJANGO_SECRET_KEY` | Clave secreta (obligatoria) |
| `DJANGO_DEBUG` | `True` solo en desarrollo |
| `DJANGO_ALLOWED_HOSTS` | Hosts permitidos, separados por coma |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | Conexión a MySQL |

## 8. Migraciones, superusuario y datos de prueba

```powershell
python manage.py migrate
python manage.py createsuperuser
python manage.py cargar_demo
```

- `migrate` crea las tablas (`festival_edicion`, `festival_categoria`, `festival_votacion`, `festival_opcionparticipante` y las de autenticación).
- `cargar_demo` puede ejecutarse varias veces sin duplicar registros.
- Para borrar **solo** los datos de demostración: `python manage.py cargar_demo --limpiar`.

Verificar tablas en MySQL:

```sql
USE festival_vallenato;
SHOW TABLES;
SELECT COUNT(*) FROM festival_votacion;
```

## 9. Ejecutar el servidor

```powershell
python manage.py runserver
```

| Ruta | Descripción | Acceso |
|---|---|---|
| `/` | Inicio | Público |
| `/ediciones/` · `/ediciones/2027/` | Lista y detalle de edición | Público |
| `/ediciones/2027/categorias/` | Categorías de la edición | Público |
| `/categorias/<id>/votaciones/` | Votaciones de una categoría | Público |
| `/votaciones/<id>/` | Detalle con opciones | Público |
| `/cuentas/registro/` · `/cuentas/login/` | Registro e inicio de sesión | Público |
| `/cuentas/logout/` | Cierre de sesión (solo POST) | Con sesión |
| `/cuentas/perfil/` | Datos del usuario | **Requiere login** |
| `/admin/` | Administración | Staff / superusuario |

Visibilidad pública: solo ediciones **publicadas**, categorías **activas**, votaciones que **no** estén en borrador y opciones **activas**.

## 10. Ejecutar las pruebas

```powershell
python manage.py test
```

Usa MySQL (crea y destruye `test_festival_vallenato`). Detalle en `docs/tabla_pruebas.md`.

## 11. Solución de errores comunes

| Error | Causa probable | Solución |
|---|---|---|
| `ImproperlyConfigured: Falta la variable de entorno ...` | No existe `.env` | `copy .env.example .env` y complétalo |
| `OperationalError (2003) Can't connect to MySQL server` | MySQL apagado, host o puerto erróneos | Inicia el servicio MySQL80 (`services.msc`) y revisa `DB_HOST`/`DB_PORT` |
| `OperationalError (1045) Access denied` | Usuario o contraseña incorrectos | Revisa `.env` y el `CREATE USER` |
| `OperationalError (1049) Unknown database` | No se creó la base | Ejecuta el `CREATE DATABASE` |
| `Access denied ... test_festival_vallenato` al correr pruebas | Falta el `GRANT` sobre la base de pruebas | Ejecuta el `GRANT` de la sección 6 |
| Falla `pip install mysqlclient` | Sin rueda precompilada para tu Python | Usa Python 3.12; si persiste, ver «Alternativa PyMySQL» |
| Las imágenes de opciones no cargan | Con `DEBUG=False` Django no sirve `media/` | Es esperado; usa `DEBUG=True` en desarrollo |

**Alternativa PyMySQL (solo si `mysqlclient` no instala):** `pip install pymysql` y agrega al inicio de `config/settings.py`:
```python
import pymysql
pymysql.install_as_MySQLdb()
```

## 12. Recomendaciones de seguridad

- No subas `.env`, contraseñas, tokens ni claves a GitHub, al PDF o al video.
- Usa `DJANGO_DEBUG=False` fuera de desarrollo; con `DEBUG=False` las cookies de sesión y CSRF pasan a `Secure` (requieren HTTPS).
- Para producción faltaría configurar HTTPS, `SECURE_SSL_REDIRECT` y HSTS (`python manage.py check --deploy` lo advierte). El despliegue está fuera del alcance de esta entrega.
- Usa un usuario de MySQL con permisos solo sobre esta base, no `root`.

## 13. Publicar en GitHub

```powershell
git init
git add .
git status          # comprueba que NO aparezca .env
git commit -m "Entrega 2: Sistema de Votaciones con Django y MySQL"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/TU_REPOSITORIO.git
git push -u origin main
```
