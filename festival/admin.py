"""Configuración de Django Admin para gestionar el Festival."""
from django.contrib import admin, messages

from .models import Categoria, Edicion, OpcionParticipante, Votacion


class CategoriaInline(admin.TabularInline):
    model = Categoria
    extra = 0
    fields = ("nombre", "activa", "es_demo")
    show_change_link = True


class OpcionInline(admin.TabularInline):
    model = OpcionParticipante
    extra = 2
    fields = ("nombre", "descripcion", "imagen", "activa")


@admin.register(Edicion)
class EdicionAdmin(admin.ModelAdmin):
    list_display = ("anio", "nombre", "fecha_inicio", "fecha_fin", "publicada", "es_demo")
    list_filter = ("publicada", "es_demo")
    search_fields = ("nombre", "anio")
    ordering = ("-anio",)
    inlines = [CategoriaInline]


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "edicion", "activa", "es_demo")
    list_filter = ("edicion", "activa", "es_demo")
    search_fields = ("nombre", "descripcion")
    list_select_related = ("edicion",)


@admin.register(Votacion)
class VotacionAdmin(admin.ModelAdmin):
    list_display = ("titulo", "categoria", "estado", "fecha_apertura", "fecha_cierre", "es_demo")
    list_filter = ("estado", "categoria__edicion", "categoria", "es_demo")
    search_fields = ("titulo", "descripcion")
    list_select_related = ("categoria", "categoria__edicion")
    inlines = [OpcionInline]

    def save_related(self, request, form, formsets, change):
        """Después de guardar las opciones en línea, aplica RN02: abrir exige >= 2 opciones activas."""
        super().save_related(request, form, formsets, change)
        votacion = form.instance
        if votacion.estado == Votacion.Estado.ABIERTA and votacion.opciones_activas().count() < 2:
            votacion.estado = Votacion.Estado.BORRADOR
            votacion.save(update_fields=["estado"])
            self.message_user(
                request,
                "La votación se guardó como borrador: necesita al menos dos opciones activas para abrirse.",
                level=messages.WARNING,
            )


@admin.register(OpcionParticipante)
class OpcionParticipanteAdmin(admin.ModelAdmin):
    list_display = ("nombre", "votacion", "activa", "es_demo")
    list_filter = ("activa", "votacion__categoria__edicion", "es_demo")
    search_fields = ("nombre", "descripcion", "votacion__titulo")
    list_select_related = ("votacion",)
