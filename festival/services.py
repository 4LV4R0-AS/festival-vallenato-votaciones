"""
Lógica de negocio del módulo de votación.

Toda la regla de "un voto por usuario, categoría y edición" y las validaciones del servidor
están en este archivo (función registrar_voto). La unicidad también está protegida en MySQL
mediante la restricción `un_voto_por_usuario_categoria_edicion` (festival/models.py, clase Voto).
"""
from django.contrib.auth import get_user_model
from django.db import IntegrityError, OperationalError, transaction
from django.utils import timezone

from .models import OpcionParticipante, Votacion, Voto

User = get_user_model()

MENSAJE_DUPLICADO = "Ya votaste en esta categoría de esta edición. Solo se permite un voto por categoría."


class VotoError(Exception):
    """Error de validación al votar. `codigo` identifica el motivo; `mensaje` se muestra al usuario."""

    def __init__(self, codigo, mensaje):
        super().__init__(mensaje)
        self.codigo = codigo
        self.mensaje = mensaje


def estado_votacion(votacion, ahora=None):
    """Devuelve (habilitada, motivo). Una votación está habilitada si se puede votar en este momento."""
    ahora = ahora or timezone.now()
    categoria = votacion.categoria
    if not categoria.edicion.publicada:
        return False, "La edición no está publicada."
    if not categoria.activa:
        return False, "La categoría no está habilitada."
    if votacion.estado != Votacion.Estado.ABIERTA:
        return False, f"La votación no está abierta (estado: {votacion.get_estado_display().lower()})."
    if votacion.fecha_apertura and ahora < votacion.fecha_apertura:
        return False, "La votación todavía no ha comenzado."
    if votacion.fecha_cierre and ahora > votacion.fecha_cierre:
        return False, "La votación ya cerró."
    return True, ""


def _registrar(usuario, votacion_id, opcion_id):
    with transaction.atomic():
        # Bloquea la fila del usuario: los votos simultáneos de la misma persona se atienden uno por uno.
        User.objects.select_for_update().get(pk=usuario.pk)

        try:
            opcion = OpcionParticipante.objects.select_related(
                "votacion__categoria__edicion"
            ).get(pk=opcion_id, votacion_id=votacion_id, activa=True)
        except (OpcionParticipante.DoesNotExist, ValueError, TypeError):
            raise VotoError("opcion_invalida", "La opción elegida no corresponde a esta votación.")

        votacion = opcion.votacion
        categoria = votacion.categoria
        edicion = categoria.edicion

        habilitada, motivo = estado_votacion(votacion)
        if not habilitada:
            raise VotoError("no_habilitada", motivo)

        if Voto.objects.filter(usuario=usuario, edicion=edicion, categoria=categoria).exists():
            raise VotoError("duplicado", MENSAJE_DUPLICADO)

        try:
            # Savepoint: si MySQL rechaza el duplicado, la transacción externa sigue sana.
            with transaction.atomic():
                return Voto.objects.create(
                    usuario=usuario, edicion=edicion, categoria=categoria, votacion=votacion, opcion=opcion
                )
        except IntegrityError:
            # Última defensa: la restricción única de MySQL frena la solicitud duplicada concurrente.
            raise VotoError("duplicado", MENSAJE_DUPLICADO)


def registrar_voto(usuario, votacion_id, opcion_id):
    """Valida y registra un voto. Lanza VotoError si no se puede votar; devuelve el Voto creado."""
    if usuario is None or not usuario.is_authenticated:
        raise VotoError("no_autenticado", "Debes iniciar sesión para votar.")
    for intento in range(3):
        try:
            return _registrar(usuario, votacion_id, opcion_id)
        except OperationalError as error:
            # 1213 = deadlock, 1205 = tiempo de espera de bloqueo: se reintenta.
            if error.args and error.args[0] in (1205, 1213) and intento < 2:
                continue
            raise
