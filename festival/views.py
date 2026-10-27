"""
Vistas públicas del Festival (parte "View" del patrón MVT).

Cada vista consulta los modelos con el ORM y entrega los datos a una plantilla.
Reglas de visibilidad pública:
  - Solo ediciones publicadas.
  - Solo categorías activas.
  - Las votaciones en borrador no se muestran.
  - Solo opciones activas.
Un registro inexistente o no visible responde con HTTP 404.
"""
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render

from .models import Categoria, Edicion, Votacion


def _votaciones_visibles():
    return Votacion.objects.exclude(estado=Votacion.Estado.BORRADOR)


def inicio(request):
    edicion = Edicion.objects.filter(publicada=True).order_by("-anio").first()
    categorias = []
    if edicion:
        categorias = edicion.categorias.filter(activa=True)[:6]
    abiertas = (
        _votaciones_visibles()
        .filter(estado=Votacion.Estado.ABIERTA, categoria__activa=True, categoria__edicion__publicada=True)
        .select_related("categoria", "categoria__edicion")[:6]
    )
    return render(request, "festival/inicio.html", {"edicion": edicion, "categorias": categorias, "abiertas": abiertas})


def ediciones(request):
    paginador = Paginator(Edicion.objects.filter(publicada=True), 6)
    pagina = paginador.get_page(request.GET.get("page"))
    return render(request, "festival/ediciones.html", {"pagina": pagina})


def edicion_detalle(request, anio):
    edicion = get_object_or_404(Edicion, anio=anio, publicada=True)
    categorias = edicion.categorias.filter(activa=True)
    return render(request, "festival/edicion_detalle.html", {"edicion": edicion, "categorias": categorias})


def categorias_edicion(request, anio):
    edicion = get_object_or_404(Edicion, anio=anio, publicada=True)
    paginador = Paginator(edicion.categorias.filter(activa=True), 9)
    pagina = paginador.get_page(request.GET.get("page"))
    return render(request, "festival/categorias.html", {"edicion": edicion, "pagina": pagina})


def votaciones_categoria(request, pk):
    categoria = get_object_or_404(Categoria.objects.select_related("edicion"), pk=pk, activa=True, edicion__publicada=True)
    votaciones = _votaciones_visibles().filter(categoria=categoria)
    return render(request, "festival/votaciones.html", {"categoria": categoria, "votaciones": votaciones})


def votacion_detalle(request, pk):
    votacion = get_object_or_404(
        _votaciones_visibles().select_related("categoria", "categoria__edicion"),
        pk=pk,
        categoria__activa=True,
        categoria__edicion__publicada=True,
    )
    opciones = votacion.opciones.filter(activa=True)
    return render(request, "festival/votacion_detalle.html", {"votacion": votacion, "opciones": opciones})
