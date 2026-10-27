from django.urls import path

from . import views

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("ediciones/", views.ediciones, name="ediciones"),
    path("ediciones/<int:anio>/", views.edicion_detalle, name="edicion_detalle"),
    path("ediciones/<int:anio>/categorias/", views.categorias_edicion, name="categorias_edicion"),
    path("categorias/<int:pk>/votaciones/", views.votaciones_categoria, name="votaciones_categoria"),
    path("votaciones/<int:pk>/", views.votacion_detalle, name="votacion_detalle"),
]
