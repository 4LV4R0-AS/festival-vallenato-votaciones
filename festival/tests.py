"""Pruebas automatizadas del dominio del Festival (códigos T01..T25 en docs/tabla_pruebas.md)."""
from datetime import date, timedelta
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Categoria, Edicion, OpcionParticipante, Votacion

User = get_user_model()
E = Votacion.Estado


def crear_cadena(anio=2027, publicada=True, estado=E.ABIERTA, n_opciones=3):
    edicion = Edicion.objects.create(anio=anio, nombre=f"Edición {anio}", publicada=publicada)
    categoria = Categoria.objects.create(edicion=edicion, nombre="Acordeón")
    votacion = Votacion.objects.create(categoria=categoria, titulo="Favorito", estado=estado)
    for i in range(n_opciones):
        OpcionParticipante.objects.create(votacion=votacion, nombre=f"Opción {i + 1}")
    return edicion, categoria, votacion


class ModelosTests(TestCase):
    def test_T01_crear_edicion(self):
        e = Edicion.objects.create(anio=2027, nombre="Festival 2027")
        self.assertEqual(Edicion.objects.count(), 1)
        self.assertFalse(e.publicada)
        self.assertEqual(str(e), "Festival 2027 (2027)")

    def test_T02_anio_de_edicion_es_unico(self):
        Edicion.objects.create(anio=2027, nombre="A")
        with self.assertRaises(IntegrityError), transaction.atomic():
            Edicion.objects.create(anio=2027, nombre="B")

    def test_T03_relaciones_edicion_categoria_votacion_opcion(self):
        edicion, categoria, votacion = crear_cadena()
        self.assertEqual(list(edicion.categorias.all()), [categoria])
        self.assertEqual(list(categoria.votaciones.all()), [votacion])
        self.assertEqual(votacion.opciones.count(), 3)
        opcion = votacion.opciones.first()
        self.assertEqual(opcion.votacion.categoria.edicion, edicion)

    def test_T04_categoria_unica_por_edicion(self):
        e1 = Edicion.objects.create(anio=2027, nombre="A")
        e2 = Edicion.objects.create(anio=2028, nombre="B")
        Categoria.objects.create(edicion=e1, nombre="Piqueria")
        Categoria.objects.create(edicion=e2, nombre="Piqueria")  # otra edición: permitido
        with self.assertRaises(IntegrityError), transaction.atomic():
            Categoria.objects.create(edicion=e1, nombre="Piqueria")

    def test_T05_votacion_y_opcion_unicas(self):
        _, categoria, votacion = crear_cadena()
        with self.assertRaises(IntegrityError), transaction.atomic():
            Votacion.objects.create(categoria=categoria, titulo="Favorito")
        with self.assertRaises(IntegrityError), transaction.atomic():
            OpcionParticipante.objects.create(votacion=votacion, nombre="Opción 1")

    def test_T06_validacion_de_fechas_de_edicion(self):
        e = Edicion(anio=2027, nombre="X", fecha_inicio=date(2027, 5, 2), fecha_fin=date(2027, 4, 28))
        with self.assertRaises(ValidationError):
            e.full_clean()

    def test_T07_no_se_puede_borrar_un_registro_con_hijos(self):
        edicion, categoria, votacion = crear_cadena()
        with self.assertRaises(ProtectedError):
            edicion.delete()
        with self.assertRaises(ProtectedError):
            categoria.delete()
        with self.assertRaises(ProtectedError):
            votacion.delete()

    def test_T08_votacion_abierta_requiere_dos_opciones_activas(self):
        _, _, votacion = crear_cadena(estado=E.BORRADOR, n_opciones=1)
        votacion.estado = E.ABIERTA
        with self.assertRaises(ValidationError):
            votacion.full_clean()
        OpcionParticipante.objects.create(votacion=votacion, nombre="Segunda")
        votacion.full_clean()  # ahora es válida

    def test_T09_fechas_de_votacion_invalidas(self):
        _, categoria, _ = crear_cadena()
        ahora = timezone.now()
        v = Votacion(categoria=categoria, titulo="Otra", fecha_apertura=ahora, fecha_cierre=ahora - timedelta(days=1))
        with self.assertRaises(ValidationError):
            v.full_clean()


class VistasPublicasTests(TestCase):
    def test_T10_inicio_muestra_datos_de_la_base(self):
        crear_cadena()
        r = self.client.get(reverse("inicio"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Edición 2027")
        self.assertContains(r, "Acordeón")
        self.assertContains(r, "Favorito")  # votación abierta

    def test_T11_inicio_sin_registros(self):
        r = self.client.get(reverse("inicio"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Aún no hay ediciones publicadas")

    def test_T12_lista_de_ediciones_solo_publicadas(self):
        crear_cadena(anio=2027, publicada=True)
        Edicion.objects.create(anio=2030, nombre="Oculta", publicada=False)
        r = self.client.get(reverse("ediciones"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Edición 2027")
        self.assertNotContains(r, "Oculta")

    def test_T13_ediciones_sin_registros(self):
        r = self.client.get(reverse("ediciones"))
        self.assertContains(r, "No hay ediciones publicadas todavía")

    def test_T14_detalle_de_edicion_y_404(self):
        crear_cadena()
        Edicion.objects.create(anio=2030, nombre="Oculta", publicada=False)
        self.assertEqual(self.client.get(reverse("edicion_detalle", args=[2027])).status_code, 200)
        self.assertEqual(self.client.get(reverse("edicion_detalle", args=[1999])).status_code, 404)  # inexistente
        self.assertEqual(self.client.get(reverse("edicion_detalle", args=[2030])).status_code, 404)  # no publicada

    def test_T15_categorias_de_edicion_con_paginacion(self):
        edicion, _, _ = crear_cadena()
        for i in range(10):
            Categoria.objects.create(edicion=edicion, nombre=f"Cat {i:02d}")
        r1 = self.client.get(reverse("categorias_edicion", args=[2027]))
        self.assertEqual(r1.status_code, 200)
        self.assertEqual(len(r1.context["pagina"]), 9)
        r2 = self.client.get(reverse("categorias_edicion", args=[2027]) + "?page=2")
        self.assertEqual(len(r2.context["pagina"]), 2)
        self.assertEqual(self.client.get(reverse("categorias_edicion", args=[1999])).status_code, 404)

    def test_T16_categoria_inactiva_no_es_visible(self):
        _, categoria, _ = crear_cadena()
        categoria.activa = False
        categoria.save()
        self.assertEqual(self.client.get(reverse("votaciones_categoria", args=[categoria.pk])).status_code, 404)
        self.assertNotContains(self.client.get(reverse("categorias_edicion", args=[2027])), "Acordeón")

    def test_T17_votaciones_de_categoria_ocultan_borradores(self):
        _, categoria, _ = crear_cadena()
        Votacion.objects.create(categoria=categoria, titulo="Secreta", estado=E.BORRADOR)
        r = self.client.get(reverse("votaciones_categoria", args=[categoria.pk]))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Favorito")
        self.assertNotContains(r, "Secreta")
        self.assertEqual(self.client.get(reverse("votaciones_categoria", args=[99999])).status_code, 404)

    def test_T18_categoria_sin_votaciones(self):
        edicion, _, _ = crear_cadena()
        vacia = Categoria.objects.create(edicion=edicion, nombre="Vacía")
        r = self.client.get(reverse("votaciones_categoria", args=[vacia.pk]))
        self.assertContains(r, "aún no tiene votaciones publicadas")

    def test_T19_detalle_de_votacion_muestra_solo_opciones_activas(self):
        _, _, votacion = crear_cadena()
        OpcionParticipante.objects.create(votacion=votacion, nombre="Retirada", activa=False)
        r = self.client.get(reverse("votacion_detalle", args=[votacion.pk]))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Opción 1")
        self.assertContains(r, "Opción 3")
        self.assertNotContains(r, "Retirada")

    def test_T20_votacion_borrador_o_inexistente_da_404(self):
        _, categoria, _ = crear_cadena()
        borrador = Votacion.objects.create(categoria=categoria, titulo="B", estado=E.BORRADOR)
        self.assertEqual(self.client.get(reverse("votacion_detalle", args=[borrador.pk])).status_code, 404)
        self.assertEqual(self.client.get(reverse("votacion_detalle", args=[99999])).status_code, 404)

    def test_T21_votacion_sin_opciones(self):
        _, _, votacion = crear_cadena(n_opciones=0)
        r = self.client.get(reverse("votacion_detalle", args=[votacion.pk]))
        self.assertContains(r, "todavía no tiene opciones participantes")

    def test_T22_no_hay_boton_de_votar_falso(self):
        _, _, votacion = crear_cadena()
        r = self.client.get(reverse("votacion_detalle", args=[votacion.pk]))
        self.assertNotContains(r, "Votar ahora")
        self.assertContains(r, "todavía no está disponible")


class DatosDemoTests(TestCase):
    def ejecutar(self, *args):
        call_command("cargar_demo", *args, stdout=StringIO())

    def test_T23_cargar_demo_no_duplica(self):
        self.ejecutar()
        conteo = (Edicion.objects.count(), Categoria.objects.count(), Votacion.objects.count(), OpcionParticipante.objects.count())
        self.ejecutar()
        self.assertEqual(conteo, (Edicion.objects.count(), Categoria.objects.count(),
                                  Votacion.objects.count(), OpcionParticipante.objects.count()))
        self.assertTrue(Edicion.objects.filter(anio=2027, es_demo=True).exists())

    def test_T24_limpiar_solo_borra_datos_demo(self):
        real = Edicion.objects.create(anio=2026, nombre="Real", publicada=True)
        cat_real = Categoria.objects.create(edicion=real, nombre="Real")
        self.ejecutar()
        self.ejecutar("--limpiar")
        self.assertFalse(Edicion.objects.filter(es_demo=True).exists())
        self.assertTrue(Edicion.objects.filter(pk=real.pk).exists())
        self.assertTrue(Categoria.objects.filter(pk=cat_real.pk).exists())


class AdminTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_superuser("admin", "admin@example.com", "ClaveSegura_2027")

    def test_T25_admin_exige_login(self):
        r = self.client.get("/admin/festival/edicion/")
        self.assertEqual(r.status_code, 302)
        self.assertIn("/admin/login/", r["Location"])

    def test_T26_superusuario_ve_los_cuatro_modelos(self):
        self.client.force_login(self.admin)
        for modelo in ("edicion", "categoria", "votacion", "opcionparticipante"):
            r = self.client.get(f"/admin/festival/{modelo}/")
            self.assertEqual(r.status_code, 200, modelo)

    def test_T27_superusuario_crea_edicion_desde_admin(self):
        self.client.force_login(self.admin)
        r = self.client.post("/admin/festival/edicion/add/", {
            "anio": 2031, "nombre": "Creada en admin", "descripcion": "", "publicada": "on",
            "categorias-TOTAL_FORMS": 0, "categorias-INITIAL_FORMS": 0,
            "categorias-MIN_NUM_FORMS": 0, "categorias-MAX_NUM_FORMS": 1000,
        })
        self.assertEqual(r.status_code, 302)
        self.assertTrue(Edicion.objects.filter(anio=2031, publicada=True).exists())

    def _post_votacion(self, categoria, titulo, nombres):
        datos = {
            "categoria": categoria.pk, "titulo": titulo, "descripcion": "", "estado": E.ABIERTA,
            "opciones-TOTAL_FORMS": len(nombres), "opciones-INITIAL_FORMS": 0,
            "opciones-MIN_NUM_FORMS": 0, "opciones-MAX_NUM_FORMS": 1000,
        }
        for i, nombre in enumerate(nombres):
            datos[f"opciones-{i}-nombre"] = nombre
            datos[f"opciones-{i}-descripcion"] = ""
            datos[f"opciones-{i}-activa"] = "on"
        return self.client.post("/admin/festival/votacion/add/", datos)

    def test_T28_admin_regresa_a_borrador_si_abre_con_menos_de_dos_opciones(self):
        self.client.force_login(self.admin)
        _, categoria, _ = crear_cadena()
        self.assertEqual(self._post_votacion(categoria, "Con una", ["Solo una"]).status_code, 302)
        self.assertEqual(Votacion.objects.get(titulo="Con una").estado, E.BORRADOR)

    def test_T29_admin_permite_abrir_con_dos_opciones(self):
        self.client.force_login(self.admin)
        _, categoria, _ = crear_cadena()
        self.assertEqual(self._post_votacion(categoria, "Con dos", ["Uno", "Dos"]).status_code, 302)
        self.assertEqual(Votacion.objects.get(titulo="Con dos").estado, E.ABIERTA)
