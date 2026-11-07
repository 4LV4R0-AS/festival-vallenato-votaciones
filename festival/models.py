"""
Modelos del dominio del Festival.

Jerarquía:  Edición -> Categoría -> Votación -> Opción participante

Las claves foráneas usan on_delete=PROTECT: no se puede borrar un registro que
tenga hijos (evita perder información por accidente). El registro definitivo de
votos NO se implementa en esta entrega; un futuro modelo "Voto" se relacionaría
con User y con OpcionParticipante (ver docs/documentacion_tecnica.md).
"""
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse


def _validar_fechas(inicio, fin, campo_fin="fecha_fin"):
    if inicio and fin and fin < inicio:
        raise ValidationError({campo_fin: "La fecha final no puede ser anterior a la fecha inicial."})


class Edicion(models.Model):
    anio = models.PositiveSmallIntegerField("año", unique=True)
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField("descripción", blank=True)
    fecha_inicio = models.DateField("fecha de inicio", null=True, blank=True)
    fecha_fin = models.DateField("fecha de finalización", null=True, blank=True)
    publicada = models.BooleanField(default=False, help_text="Solo las ediciones publicadas son visibles al público.")
    es_demo = models.BooleanField("dato de demostración", default=False)

    class Meta:
        verbose_name = "edición"
        verbose_name_plural = "ediciones"
        ordering = ["-anio"]

    def __str__(self):
        return f"{self.nombre} ({self.anio})"

    def clean(self):
        _validar_fechas(self.fecha_inicio, self.fecha_fin)

    def get_absolute_url(self):
        return reverse("edicion_detalle", args=[self.anio])


class Categoria(models.Model):
    edicion = models.ForeignKey(Edicion, on_delete=models.PROTECT, related_name="categorias", verbose_name="edición")
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField("descripción", blank=True)
    activa = models.BooleanField(default=True)
    es_demo = models.BooleanField("dato de demostración", default=False)

    class Meta:
        verbose_name = "categoría"
        verbose_name_plural = "categorías"
        ordering = ["edicion", "nombre"]
        constraints = [
            models.UniqueConstraint(fields=["edicion", "nombre"], name="categoria_unica_por_edicion"),
        ]

    def __str__(self):
        return f"{self.nombre} – {self.edicion.anio}"

    def get_absolute_url(self):
        return reverse("votaciones_categoria", args=[self.pk])


class Votacion(models.Model):
    class Estado(models.TextChoices):
        BORRADOR = "borrador", "Borrador"
        PROGRAMADA = "programada", "Programada"
        ABIERTA = "abierta", "Abierta"
        CERRADA = "cerrada", "Cerrada"

    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, related_name="votaciones", verbose_name="categoría")
    titulo = models.CharField("título", max_length=200)
    descripcion = models.TextField("descripción", blank=True)
    fecha_apertura = models.DateTimeField(null=True, blank=True)
    fecha_cierre = models.DateTimeField(null=True, blank=True)
    estado = models.CharField(max_length=12, choices=Estado.choices, default=Estado.BORRADOR)
    es_demo = models.BooleanField("dato de demostración", default=False)

    class Meta:
        verbose_name = "votación"
        verbose_name_plural = "votaciones"
        ordering = ["categoria", "titulo"]
        constraints = [
            models.UniqueConstraint(fields=["categoria", "titulo"], name="votacion_unica_por_categoria"),
        ]

    def __str__(self):
        return self.titulo

    def clean(self):
        _validar_fechas(self.fecha_apertura, self.fecha_cierre, "fecha_cierre")
        # RN02 (Entrega 1): una votación necesita al menos dos opciones activas para abrirse.
        if self.pk and self.estado == self.Estado.ABIERTA and self.opciones_activas().count() < 2:
            raise ValidationError({"estado": "Una votación necesita al menos dos opciones activas para abrirse."})

    def opciones_activas(self):
        return self.opciones.filter(activa=True)

    def get_absolute_url(self):
        return reverse("votacion_detalle", args=[self.pk])


class OpcionParticipante(models.Model):
    votacion = models.ForeignKey(Votacion, on_delete=models.PROTECT, related_name="opciones", verbose_name="votación")
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField("descripción", blank=True)
    imagen = models.ImageField(upload_to="opciones/", null=True, blank=True)
    activa = models.BooleanField(default=True)
    es_demo = models.BooleanField("dato de demostración", default=False)

    class Meta:
        verbose_name = "opción participante"
        verbose_name_plural = "opciones participantes"
        ordering = ["votacion", "nombre"]
        constraints = [
            models.UniqueConstraint(fields=["votacion", "nombre"], name="opcion_unica_por_votacion"),
        ]

    def __str__(self):
        return self.nombre


class Voto(models.Model):
    """
    Voto emitido por un usuario.

    Regla central (Entrega 3): un usuario puede votar UNA sola vez por categoría y edición,
    aunque la categoría tenga varias votaciones (subeventos). La regla se garantiza con una
    restricción única en MySQL (usuario, edición, categoría) y se valida además en
    festival/services.py. Edición, categoría y votación se calculan en el servidor a partir de la
    opción elegida; nunca se aceptan desde el formulario.
    """

    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="votos")
    edicion = models.ForeignKey(Edicion, on_delete=models.PROTECT, related_name="votos", verbose_name="edición")
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, related_name="votos", verbose_name="categoría")
    votacion = models.ForeignKey(Votacion, on_delete=models.PROTECT, related_name="votos", verbose_name="votación")
    opcion = models.ForeignKey(OpcionParticipante, on_delete=models.PROTECT, related_name="votos", verbose_name="opción")
    fecha_hora = models.DateTimeField("fecha y hora", auto_now_add=True)

    class Meta:
        verbose_name = "voto"
        verbose_name_plural = "votos"
        ordering = ["-fecha_hora"]
        constraints = [
            models.UniqueConstraint(
                fields=["usuario", "edicion", "categoria"],
                name="un_voto_por_usuario_categoria_edicion",
            ),
        ]

    def __str__(self):
        return f"{self.usuario} → {self.opcion} ({self.categoria})"

    def clean(self):
        """Comprueba que usuario, opción, votación, categoría y edición sean coherentes entre sí."""
        if self.opcion_id and self.votacion_id and self.opcion.votacion_id != self.votacion_id:
            raise ValidationError("La opción no pertenece a la votación indicada.")
        if self.votacion_id and self.categoria_id and self.votacion.categoria_id != self.categoria_id:
            raise ValidationError("La votación no pertenece a la categoría indicada.")
        if self.categoria_id and self.edicion_id and self.categoria.edicion_id != self.edicion_id:
            raise ValidationError("La categoría no pertenece a la edición indicada.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
