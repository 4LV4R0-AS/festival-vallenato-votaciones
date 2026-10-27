# Documentación técnica

## 1. Patrón MVT en Django

| Componente | Archivo(s) | Responsabilidad |
|---|---|---|
| **Model** | `festival/models.py` | Entidades, atributos, validaciones, relaciones y restricciones. |
| **View** | `festival/views.py`, `accounts/views.py` | Reciben la solicitud HTTP, consultan los modelos con el ORM y eligen la plantilla. |
| **Template** | `templates/`, `*/templates/` | Presentan los datos en HTML con el lenguaje de plantillas de Django. |
| **URLconf** | `config/urls.py`, `*/urls.py` | Relacionan cada ruta con su vista. |

**Equivalencia conceptual con MVC:** el *Model* de Django equivale al modelo de MVC; el *Template* cumple el papel de la vista de MVC (presentación); y la *View* de Django cumple el papel del controlador (lógica de la solicitud). La correspondencia es conceptual, no de nomenclatura: en Django «View» no significa lo mismo que en MVC.

## 2. Flujo de una solicitud HTTP

Ejemplo: `GET /votaciones/1/`

1. El navegador envía la solicitud al servidor de desarrollo.
2. Los *middleware* procesan sesión, CSRF y autenticación.
3. `config/urls.py` delega en `festival/urls.py`, que encuentra `votaciones/<int:pk>/` → `votacion_detalle`.
4. La vista consulta MySQL mediante el ORM (`get_object_or_404`, `opciones.filter(activa=True)`).
5. La vista entrega `votacion` y `opciones` a `votacion_detalle.html`, que extiende `base.html`.
6. Django genera el HTML y lo devuelve. Si el registro no existe o no es visible, responde 404.

## 3. Modelo de datos

```
Edicion 1 ──< Categoria 1 ──< Votacion 1 ──< OpcionParticipante
```

| Entidad | Campos | Restricciones |
|---|---|---|
| Edicion | `anio`, `nombre`, `descripcion`, `fecha_inicio`, `fecha_fin`, `publicada`, `es_demo` | `anio` único; `fecha_fin ≥ fecha_inicio` |
| Categoria | `edicion` (FK), `nombre`, `descripcion`, `activa`, `es_demo` | único (`edicion`, `nombre`) |
| Votacion | `categoria` (FK), `titulo`, `descripcion`, `fecha_apertura`, `fecha_cierre`, `estado`, `es_demo` | único (`categoria`, `titulo`); `cierre ≥ apertura`; abierta exige ≥ 2 opciones activas |
| OpcionParticipante | `votacion` (FK), `nombre`, `descripcion`, `imagen`, `activa`, `es_demo` | único (`votacion`, `nombre`) |

- **Reglas de eliminación:** todas las FK usan `PROTECT`; no se puede borrar un registro con hijos (se prueba en T07).
- **Unicidad justificada:** evita categorías, votaciones u opciones repetidas dentro de su padre, pero permite el mismo nombre en padres distintos (ej.: «Piqueria» en dos ediciones).
- **`es_demo`:** marca los datos de demostración para poder borrarlos sin tocar datos reales.
- **Estados de votación:** borrador, programada, abierta, cerrada. Los borradores no son visibles al público.
- **Usuarios:** se usa `auth.User` de Django; no hay sistema propio ni contraseñas manuales.

## 4. MySQL

- Motor: MySQL 8, `utf8mb4`, controlador `mysqlclient`.
- Credenciales por variables de entorno (`.env`, leído con `python-dotenv`).
- `CREATE DATABASE` se ejecuta en MySQL; las **tablas** las crea `python manage.py migrate` a partir de `festival/migrations/0001_initial.py`.
- `sql_mode=STRICT_TRANS_TABLES` evita que MySQL trunque datos en silencio.

## 5. Autenticación

- Registro: `RegistroForm` (extiende `UserCreationForm`) con correo único (sin distinguir mayúsculas) y aceptación del tratamiento de datos.
- Contraseñas: PBKDF2 con validadores de Django (longitud, comunes, numéricas, similitud).
- Login/logout: vistas de `django.contrib.auth`; el cierre de sesión **solo acepta POST** y exige token CSRF.
- Autorización: solo existe la distinción de Django entre usuario normal y `is_staff`/`is_superuser` (acceso a `/admin/`). **No hay autorización avanzada ni roles propios.**
- Única página pública que exige login: `/cuentas/perfil/`.

## 6. Cómo se incorporarán las reglas futuras

Las reglas de elegibilidad, frecuencia y publicación de resultados siguen pendientes de validación con el cliente (Entrega 1, sección 11), por lo que **no se inventaron**. El diseño permite añadirlas sin rehacer lo existente:

- **Voto:** nuevo modelo con FK a `User` y a `OpcionParticipante` (y a `Votacion`), fecha y hora. La unicidad `(usuario, votacion)` impediría votos duplicados si el cliente decide «un voto por votación»; si decide otra frecuencia, se parametrizaría en `Votacion` (campo `regla_frecuencia` de la Entrega 1) con una migración.
- **Ventana de votación:** `estado`, `fecha_apertura` y `fecha_cierre` ya existen.
- **Votación atómica:** `transaction.atomic()` con restricción única en base de datos.
- **Auditoría:** modelo de bitácora con FK a `User` y marca de tiempo.
- **Resultados:** agregaciones del ORM (`Count`) sobre `Voto`.
- **Recuperación de contraseña (RF12):** vistas `PasswordReset*` de Django, cuando se defina el canal (correo).

## 7. Decisiones de implementación respecto a la Entrega 1

| Entrega 1 | Entrega 2 | Motivo |
|---|---|---|
| Bootstrap como referencia | CSS propio | El enunciado exige no depender de servicios externos. |
| `regla_frecuencia` en Votación | No incluido | Regla aún pendiente de validación (RN04). |
| Login con correo (prototipo) | Login con nombre de usuario; correo único en el registro | Es el mecanismo estándar de Django; el correo con backend propio queda como mejora. |
| CU-04, CU-08, RF13 | Pendientes | Corresponden a entregas posteriores. |
| RF12 (recuperar contraseña) | No incluido | Pendiente de validación. |

## 8. Limitaciones conocidas

- No se registra ningún voto.
- Sin recuperación de contraseña ni verificación de correo.
- Sin despliegue; `check --deploy` advierte sobre HTTPS/HSTS, propio de producción.
- Las imágenes subidas se sirven solo con `DEBUG=True`.
