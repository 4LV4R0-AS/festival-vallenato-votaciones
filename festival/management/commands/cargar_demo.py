"""
Carga datos de DEMOSTRACIÓN para verificar las relaciones del modelo.

Uso:
    python manage.py cargar_demo             # crea/actualiza los datos (no duplica)
    python manage.py cargar_demo --limpiar   # elimina SOLO los registros marcados como demo

Todos los registros llevan es_demo=True. Los nombres de participantes son ficticios:
NO corresponden a información oficial del Festival.
"""
from datetime import date

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from festival.models import Categoria, Edicion, OpcionParticipante, Votacion

E = Votacion.Estado

CATEGORIAS = {
    "Acordeón profesional": (
        "Categoría de demostración inspirada en los concursos de acordeón.",
        [
            ("Favorito del público – Acordeón profesional", "Votación abierta de demostración.", E.ABIERTA,
             ["Acordeonero Demo 1", "Acordeonero Demo 2", "Acordeonero Demo 3"]),
            ("Revelación juvenil – Acordeón", "Votación programada de demostración.", E.PROGRAMADA,
             ["Joven Talento Demo A", "Joven Talento Demo B"]),
        ],
    ),
    "Piqueria": (
        "Categoría de demostración inspirada en la improvisación de versos.",
        [
            ("Mejor verso improvisado", "Votación abierta de demostración.", E.ABIERTA,
             ["Piquero Demo 1", "Piquero Demo 2", "Piquero Demo 3", "Piquero Demo 4"]),
            ("Piqueria infantil – favorito", "Votación cerrada de demostración.", E.CERRADA,
             ["Piquero Infantil Demo 1", "Piquero Infantil Demo 2"]),
        ],
    ),
    "Canción Vallenata Inédita": (
        "Categoría de demostración inspirada en el concurso de composición.",
        [
            ("Canción favorita del público", "Votación abierta de demostración.", E.ABIERTA,
             ["Canción Demo «Amanecer»", "Canción Demo «Río Guatapurí»", "Canción Demo «Camino de Tierra»"]),
            ("Votación en borrador (no visible al público)", "Sirve para probar que los borradores se ocultan.", E.BORRADOR,
             ["Opción Borrador 1", "Opción Borrador 2"]),
        ],
    ),
    "Desfile de Piloneras": (
        "Categoría de demostración inspirada en el Desfile de Piloneras.",
        [
            ("Mejor comparsa", "Votación programada de demostración.", E.PROGRAMADA,
             ["Comparsa Demo 1", "Comparsa Demo 2", "Comparsa Demo 3"]),
        ],
    ),
}


class Command(BaseCommand):
    help = "Carga (o limpia con --limpiar) los datos de demostración del Festival."

    def add_arguments(self, parser):
        parser.add_argument("--limpiar", action="store_true", help="Elimina solo los registros marcados como demostración.")

    @transaction.atomic
    def handle(self, *args, **opciones):
        if opciones["limpiar"]:
            return self.limpiar()

        edicion, _ = Edicion.objects.update_or_create(
            anio=2027,
            defaults=dict(
                nombre="Festival de la Leyenda Vallenata 2027",
                descripcion="DATOS DE DEMOSTRACIÓN. Edición de ejemplo creada para verificar el sistema; "
                            "no corresponde a información oficial de la Fundación Festival de la Leyenda Vallenata.",
                fecha_inicio=date(2027, 4, 28),
                fecha_fin=date(2027, 5, 2),
                publicada=True,
                es_demo=True,
            ),
        )
        ahora = timezone.now()
        creadas = 0
        for nombre_cat, (desc_cat, votaciones) in CATEGORIAS.items():
            categoria, _ = Categoria.objects.update_or_create(
                edicion=edicion, nombre=nombre_cat, defaults=dict(descripcion=desc_cat, activa=True, es_demo=True)
            )
            for titulo, desc, estado, opciones_nombres in votaciones:
                apertura = ahora - timezone.timedelta(days=2) if estado in (E.ABIERTA, E.CERRADA) else ahora + timezone.timedelta(days=30)
                cierre = ahora - timezone.timedelta(days=1) if estado == E.CERRADA else ahora + timezone.timedelta(days=60)
                votacion, _ = Votacion.objects.update_or_create(
                    categoria=categoria, titulo=titulo,
                    defaults=dict(descripcion=desc, estado=estado, fecha_apertura=apertura, fecha_cierre=cierre, es_demo=True),
                )
                for nombre_op in opciones_nombres:
                    _, nueva = OpcionParticipante.objects.update_or_create(
                        votacion=votacion, nombre=nombre_op,
                        defaults=dict(descripcion="Participante ficticio de demostración.", activa=True, es_demo=True),
                    )
                    creadas += nueva
        self.stdout.write(self.style.SUCCESS(
            f"Datos de demostración listos. Ediciones: {Edicion.objects.filter(es_demo=True).count()}, "
            f"categorías: {Categoria.objects.filter(es_demo=True).count()}, "
            f"votaciones: {Votacion.objects.filter(es_demo=True).count()}, "
            f"opciones: {OpcionParticipante.objects.filter(es_demo=True).count()} "
            f"(opciones nuevas en esta ejecución: {creadas})."
        ))

    def limpiar(self):
        o = OpcionParticipante.objects.filter(es_demo=True).delete()[0]
        v = Votacion.objects.filter(es_demo=True).delete()[0]
        c = Categoria.objects.filter(es_demo=True).delete()[0]
        # La edición solo se borra si ya no tiene categorías (reales) asociadas.
        e = Edicion.objects.filter(es_demo=True, categorias__isnull=True).delete()[0]
        self.stdout.write(self.style.WARNING(
            f"Eliminados -> opciones: {o}, votaciones: {v}, categorías: {c}, ediciones: {e}. "
            "Los registros reales (es_demo=False) no se tocaron."
        ))
