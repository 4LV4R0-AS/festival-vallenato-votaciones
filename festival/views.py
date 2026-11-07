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
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Prefetch
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET

from .models import Categoria, Edicion, OpcionParticipante, Votacion, Voto
from .services import MENSAJE_DUPLICADO, VotoError, estado_votacion, registrar_voto


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


def _votacion_publica(pk):
    return get_object_or_404(
        _votaciones_visibles().select_related("categoria", "categoria__edicion"),
        pk=pk,
        categoria__activa=True,
        categoria__edicion__publicada=True,
    )


def votacion_detalle(request, pk):
    votacion = _votacion_publica(pk)
    opciones = votacion.opciones.filter(activa=True)
    habilitada, motivo = estado_votacion(votacion)
    voto_usuario = None
    if request.user.is_authenticated:
        voto_usuario = (
            Voto.objects.filter(usuario=request.user, edicion=votacion.categoria.edicion, categoria=votacion.categoria)
            .select_related("opcion", "votacion")
            .first()
        )
    contexto = {
        "votacion": votacion,
        "opciones": opciones,
        "habilitada": habilitada,
        "motivo": motivo,
        "voto_usuario": voto_usuario,
        "puede_votar": habilitada and request.user.is_authenticated and voto_usuario is None and opciones.exists(),
    }
    return render(request, "festival/votacion_detalle.html", contexto)


@login_required
def votar(request, pk):
    """Paso 1 (seleccionar): muestra la confirmación. Paso 2 (confirmar): registra el voto en MySQL. Solo POST."""
    votacion = _votacion_publica(pk)
    if request.method != "POST":
        return redirect(votacion)

    opcion_id = request.POST.get("opcion")
    if not opcion_id:
        messages.error(request, "Selecciona una opción antes de continuar.")
        return redirect(votacion)

    if request.POST.get("paso") == "confirmar":
        try:
            voto = registrar_voto(request.user, votacion.pk, opcion_id)
        except VotoError as error:
            messages.error(request, error.mensaje)
            return redirect(votacion)
        messages.success(request, f"Tu voto por «{voto.opcion.nombre}» quedó registrado.")
        return redirect("mis_votos")

    # Paso de selección: se validan los datos antes de pedir la confirmación.
    try:
        opcion = votacion.opciones.filter(activa=True).filter(pk=int(opcion_id)).first()
    except (TypeError, ValueError):
        opcion = None
    if opcion is None:
        messages.error(request, "La opción elegida no corresponde a esta votación.")
        return redirect(votacion)
    habilitada, motivo = estado_votacion(votacion)
    if not habilitada:
        messages.error(request, motivo)
        return redirect(votacion)
    if Voto.objects.filter(usuario=request.user, edicion=votacion.categoria.edicion, categoria=votacion.categoria).exists():
        messages.error(request, MENSAJE_DUPLICADO)
        return redirect(votacion)
    return render(request, "festival/confirmar_voto.html", {"votacion": votacion, "opcion": opcion})


@login_required
def mis_votos(request):
    votos = request.user.votos.select_related("edicion", "categoria", "votacion", "opcion")
    votadas = votos.values_list("categoria_id", flat=True)
    pendientes = (
        Categoria.objects.filter(activa=True, edicion__publicada=True, votaciones__estado=Votacion.Estado.ABIERTA)
        .exclude(pk__in=votadas)
        .select_related("edicion")
        .distinct()
    )
    return render(request, "festival/mis_votos.html", {"votos": votos, "pendientes": pendientes})


@require_GET
def api_categorias(request):
    """GET /api/categorias/ -> categorías con sus votaciones y opciones, en JSON, desde MySQL."""
    categorias = Categoria.objects.filter(activa=True, edicion__publicada=True).select_related("edicion")
    anio = request.GET.get("edicion")
    if anio:
        try:
            categorias = categorias.filter(edicion__anio=int(anio))
        except ValueError:
            return JsonResponse({"error": "El parámetro 'edicion' debe ser un año numérico."}, status=400)

    categorias = categorias.prefetch_related(
        Prefetch(
            "votaciones",
            queryset=Votacion.objects.exclude(estado=Votacion.Estado.BORRADOR).prefetch_related(
                Prefetch(
                    "opciones",
                    queryset=OpcionParticipante.objects.filter(activa=True),
                    to_attr="opciones_api",
                )
            ),
            to_attr="votaciones_api",
        )
    )

    datos = {
        "categorias": [
            {
                "id": c.pk,
                "nombre": c.nombre,
                "descripcion": c.descripcion,
                "edicion": {"id": c.edicion.pk, "anio": c.edicion.anio, "nombre": c.edicion.nombre},
                "votaciones": [
                    {
                        "id": v.pk,
                        "titulo": v.titulo,
                        "descripcion": v.descripcion,
                        "estado": v.estado,
                        "fecha_apertura": v.fecha_apertura.isoformat() if v.fecha_apertura else None,
                        "fecha_cierre": v.fecha_cierre.isoformat() if v.fecha_cierre else None,
                        "opciones": [
                            {"id": o.pk, "nombre": o.nombre, "descripcion": o.descripcion}
                            for o in v.opciones_api
                        ],
                    }
                    for v in c.votaciones_api
                ],
            }
            for c in categorias
        ]
    }
    datos["total"] = len(datos["categorias"])
    return JsonResponse(datos, json_dumps_params={"ensure_ascii": False, "indent": 2})
