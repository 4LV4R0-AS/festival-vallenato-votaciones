"""
Pruebas del módulo de votación (Entrega 3). Cubren los casos funcionales CP-01 a CP-10.
Cada prueba lleva en su nombre el código del caso (CP-xx) para cruzarlo con la tabla del informe.
"""
import json
import threading
from datetime import timedelta
from types import SimpleNamespace

from django.contrib.auth import get_user_model
from django.db import IntegrityError, connection, transaction
from django.test import Client, TestCase, TransactionTestCase
from django.urls import reverse
from django.utils import timezone

from .models import Categoria, Edicion, OpcionParticipante, Votacion, Voto
from .services import VotoError, registrar_voto

User = get_user_model()
E = Votacion.Estado


def preparar():
    """Edición 2027 con dos categorías; la primera tiene dos votaciones abiertas (subeventos)."""
    ahora = timezone.now()
    abierta = dict(estado=E.ABIERTA, fecha_apertura=ahora - timedelta(days=1), fecha_cierre=ahora + timedelta(days=30))
    edicion = Edicion.objects.create(anio=2027, nombre="Festival 2027", publicada=True)
    cat_a = Categoria.objects.create(edicion=edicion, nombre="Acordeón")
    cat_b = Categoria.objects.create(edicion=edicion, nombre="Piqueria")
    v_a1 = Votacion.objects.create(categoria=cat_a, titulo="Favorito del público", **abierta)
    v_a2 = Votacion.objects.create(categoria=cat_a, titulo="Revelación juvenil", **abierta)
    v_b = Votacion.objects.create(categoria=cat_b, titulo="Mejor verso", **abierta)
    ops = {}
    for clave, v in (("a1", v_a1), ("a2", v_a2), ("b", v_b)):
        ops[clave] = [OpcionParticipante.objects.create(votacion=v, nombre=f"{v.titulo} {n}") for n in (1, 2)]
    return SimpleNamespace(edicion=edicion, cat_a=cat_a, cat_b=cat_b, v_a1=v_a1, v_a2=v_a2, v_b=v_b, ops=ops)


def votar_http(client, votacion, opcion, paso="confirmar", follow=False):
    return client.post(reverse("votar", args=[votacion.pk]), {"opcion": opcion.pk, "paso": paso}, follow=follow)


class VotoBase(TestCase):
    def setUp(self):
        self.d = preparar()
        self.usuario = User.objects.create_user("ana", "ana@example.com", "ClaveMuySegura_9876")
        self.client.force_login(self.usuario)


class CP01_VotoValido(VotoBase):
    def test_CP01_usuario_autenticado_registra_un_voto_valido(self):
        d = self.d
        # Paso 1: seleccionar -> pantalla de confirmación (no registra nada todavía)
        r = votar_http(self.client, d.v_a1, d.ops["a1"][0], paso="seleccionar")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Confirma tu voto")
        self.assertEqual(Voto.objects.count(), 0)
        # Paso 2: confirmar -> se registra en MySQL
        r = votar_http(self.client, d.v_a1, d.ops["a1"][0], follow=True)
        self.assertRedirects(r, reverse("mis_votos"))
        self.assertContains(r, "quedó registrado")
        voto = Voto.objects.get()
        self.assertEqual((voto.usuario, voto.opcion, voto.votacion, voto.categoria, voto.edicion),
                         (self.usuario, d.ops["a1"][0], d.v_a1, d.cat_a, d.edicion))


class CP02_Duplicado(VotoBase):
    def test_CP02_segundo_voto_en_la_misma_votacion_se_rechaza(self):
        d = self.d
        votar_http(self.client, d.v_a1, d.ops["a1"][0])
        r = votar_http(self.client, d.v_a1, d.ops["a1"][1], follow=True)
        self.assertContains(r, "Ya votaste en esta categoría")
        self.assertEqual(Voto.objects.count(), 1)

    def test_CP02_segundo_voto_en_otro_subevento_de_la_misma_categoria_se_rechaza(self):
        d = self.d
        votar_http(self.client, d.v_a1, d.ops["a1"][0])
        r = votar_http(self.client, d.v_a2, d.ops["a2"][0], follow=True)
        self.assertContains(r, "Ya votaste en esta categoría")
        self.assertEqual(Voto.objects.filter(usuario=self.usuario, categoria=d.cat_a).count(), 1)

    def test_CP02_la_restriccion_unica_de_mysql_impide_el_duplicado(self):
        d = self.d
        Voto.objects.create(usuario=self.usuario, edicion=d.edicion, categoria=d.cat_a, votacion=d.v_a1, opcion=d.ops["a1"][0])
        with self.assertRaises(IntegrityError), transaction.atomic():
            Voto.objects.create(usuario=self.usuario, edicion=d.edicion, categoria=d.cat_a, votacion=d.v_a2, opcion=d.ops["a2"][0])

    def test_CP02_otro_usuario_si_puede_votar_en_la_misma_categoria(self):
        d = self.d
        votar_http(self.client, d.v_a1, d.ops["a1"][0])
        otro = Client()
        otro.force_login(User.objects.create_user("luis", "luis@example.com", "ClaveMuySegura_9876"))
        votar_http(otro, d.v_a1, d.ops["a1"][0])
        self.assertEqual(Voto.objects.filter(categoria=d.cat_a).count(), 2)

    def test_CP02_el_detalle_muestra_el_voto_ya_emitido_y_oculta_el_formulario(self):
        d = self.d
        votar_http(self.client, d.v_a1, d.ops["a1"][0])
        r = self.client.get(reverse("votacion_detalle", args=[d.v_a2.pk]))
        self.assertContains(r, "Ya votaste en esta categoría")
        self.assertNotContains(r, 'name="opcion"')


class CP03_OtraCategoria(VotoBase):
    def test_CP03_votar_en_una_categoria_diferente_esta_permitido(self):
        d = self.d
        votar_http(self.client, d.v_a1, d.ops["a1"][0])
        votar_http(self.client, d.v_b, d.ops["b"][0])
        self.assertEqual(Voto.objects.filter(usuario=self.usuario).count(), 2)
        self.assertEqual(set(Voto.objects.values_list("categoria_id", flat=True)), {d.cat_a.pk, d.cat_b.pk})


class CP04_Autenticacion(TestCase):
    def test_CP04_usuario_anonimo_no_puede_votar(self):
        d = preparar()
        r = votar_http(self.client, d.v_a1, d.ops["a1"][0])
        self.assertEqual(r.status_code, 302)
        self.assertIn(reverse("login"), r["Location"])
        self.assertEqual(Voto.objects.count(), 0)

    def test_CP04_el_servicio_tambien_exige_autenticacion(self):
        from django.contrib.auth.models import AnonymousUser
        d = preparar()
        with self.assertRaises(VotoError) as ctx:
            registrar_voto(AnonymousUser(), d.v_a1.pk, d.ops["a1"][0].pk)
        self.assertEqual(ctx.exception.codigo, "no_autenticado")

    def test_CP04_el_voto_exige_token_csrf(self):
        d = preparar()
        cliente = Client(enforce_csrf_checks=True)
        cliente.force_login(User.objects.create_user("ana", "ana@example.com", "ClaveMuySegura_9876"))
        r = cliente.post(reverse("votar", args=[d.v_a1.pk]), {"opcion": d.ops["a1"][0].pk, "paso": "confirmar"})
        self.assertEqual(r.status_code, 403)
        self.assertEqual(Voto.objects.count(), 0)

    def test_CP04_votar_por_get_no_registra_nada(self):
        d = preparar()
        c = Client()
        c.force_login(User.objects.create_user("ana", "ana@example.com", "ClaveMuySegura_9876"))
        r = c.get(reverse("votar", args=[d.v_a1.pk]))
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Voto.objects.count(), 0)


class CP05_CategoriaNoHabilitada(VotoBase):
    def _rechazado(self, votacion, opcion):
        r = votar_http(self.client, votacion, opcion, follow=True)
        self.assertEqual(Voto.objects.count(), 0)
        return r

    def test_CP05_votacion_cerrada(self):
        d = self.d
        d.v_a1.estado = E.CERRADA
        d.v_a1.save()
        self.assertContains(self._rechazado(d.v_a1, d.ops["a1"][0]), "no está abierta")

    def test_CP05_votacion_programada(self):
        d = self.d
        d.v_a1.estado = E.PROGRAMADA
        d.v_a1.save()
        self.assertContains(self._rechazado(d.v_a1, d.ops["a1"][0]), "no está abierta")

    def test_CP05_votacion_abierta_pero_fuera_de_fecha(self):
        d = self.d
        d.v_a1.fecha_cierre = timezone.now() - timedelta(hours=1)
        d.v_a1.save()
        self.assertContains(self._rechazado(d.v_a1, d.ops["a1"][0]), "ya cerró")

    def test_CP05_votacion_abierta_que_aun_no_comienza(self):
        d = self.d
        d.v_a1.fecha_apertura = timezone.now() + timedelta(days=1)
        d.v_a1.save()
        self.assertContains(self._rechazado(d.v_a1, d.ops["a1"][0]), "todavía no ha comenzado")

    def test_CP05_categoria_inactiva(self):
        d = self.d
        d.cat_a.activa = False
        d.cat_a.save()
        r = votar_http(self.client, d.v_a1, d.ops["a1"][0])
        self.assertEqual(r.status_code, 404)
        with self.assertRaises(VotoError) as ctx:
            registrar_voto(self.usuario, d.v_a1.pk, d.ops["a1"][0].pk)
        self.assertEqual(ctx.exception.codigo, "no_habilitada")
        self.assertEqual(Voto.objects.count(), 0)

    def test_CP05_edicion_no_publicada(self):
        d = self.d
        d.edicion.publicada = False
        d.edicion.save()
        self.assertEqual(votar_http(self.client, d.v_a1, d.ops["a1"][0]).status_code, 404)
        with self.assertRaises(VotoError) as ctx:
            registrar_voto(self.usuario, d.v_a1.pk, d.ops["a1"][0].pk)
        self.assertEqual(ctx.exception.codigo, "no_habilitada")

    def test_CP05_opcion_inactiva(self):
        d = self.d
        d.ops["a1"][0].activa = False
        d.ops["a1"][0].save()
        self.assertContains(self._rechazado(d.v_a1, d.ops["a1"][0]), "no corresponde")


class CP06_OpcionAjena(VotoBase):
    def test_CP06_opcion_de_otra_categoria_se_rechaza(self):
        d = self.d
        r = votar_http(self.client, d.v_a1, d.ops["b"][0], follow=True)  # opción de Piqueria enviada a Acordeón
        self.assertContains(r, "no corresponde a esta votación")
        self.assertEqual(Voto.objects.count(), 0)

    def test_CP06_opcion_de_otra_votacion_de_la_misma_categoria_se_rechaza(self):
        d = self.d
        r = votar_http(self.client, d.v_a1, d.ops["a2"][0], follow=True)
        self.assertContains(r, "no corresponde a esta votación")
        self.assertEqual(Voto.objects.count(), 0)

    def test_CP06_el_servicio_rechaza_opciones_ajenas_o_inexistentes(self):
        d = self.d
        for opcion_id in (d.ops["b"][0].pk, 999999, "abc", None):
            with self.assertRaises(VotoError) as ctx:
                registrar_voto(self.usuario, d.v_a1.pk, opcion_id)
            self.assertEqual(ctx.exception.codigo, "opcion_invalida")
        self.assertEqual(Voto.objects.count(), 0)

    def test_CP06_enviar_opcion_vacia_o_invalida_no_rompe_la_pagina(self):
        d = self.d
        for dato in ({}, {"opcion": ""}, {"opcion": "abc"}):
            r = self.client.post(reverse("votar", args=[d.v_a1.pk]), dato)
            self.assertEqual(r.status_code, 302)
        self.assertEqual(Voto.objects.count(), 0)


class CP07_MisVotos(VotoBase):
    def test_CP07_el_usuario_ve_sus_categorias_votadas_y_las_pendientes(self):
        d = self.d
        votar_http(self.client, d.v_a1, d.ops["a1"][1])
        r = self.client.get(reverse("mis_votos"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Favorito del público 2")   # su opción
        self.assertContains(r, "Acordeón")
        pendientes = [c.pk for c in r.context["pendientes"]]
        self.assertEqual(pendientes, [d.cat_b.pk])          # Piqueria aún sin votar

    def test_CP07_no_muestra_los_votos_de_otros_usuarios(self):
        d = self.d
        otro = User.objects.create_user("luis", "luis@example.com", "ClaveMuySegura_9876")
        Voto.objects.create(usuario=otro, edicion=d.edicion, categoria=d.cat_b, votacion=d.v_b, opcion=d.ops["b"][0])
        r = self.client.get(reverse("mis_votos"))
        self.assertNotContains(r, "Mejor verso 1")
        self.assertContains(r, "Todavía no has votado")

    def test_CP07_requiere_sesion(self):
        r = Client().get(reverse("mis_votos"))
        self.assertEqual(r.status_code, 302)
        self.assertIn(reverse("login"), r["Location"])


class CP08_Administracion(TestCase):
    def setUp(self):
        self.d = preparar()
        self.admin = User.objects.create_superuser("admin", "admin@example.com", "ClaveSegura_2027")
        self.ana = User.objects.create_user("ana", "ana@example.com", "ClaveMuySegura_9876")
        self.luis = User.objects.create_user("luis", "luis@example.com", "ClaveMuySegura_9876")
        d = self.d
        self.voto1 = Voto.objects.create(usuario=self.ana, edicion=d.edicion, categoria=d.cat_a, votacion=d.v_a1, opcion=d.ops["a1"][0])
        self.voto2 = Voto.objects.create(usuario=self.luis, edicion=d.edicion, categoria=d.cat_b, votacion=d.v_b, opcion=d.ops["b"][1])

    def test_CP08_el_administrador_ve_los_votos_registrados(self):
        self.client.force_login(self.admin)
        r = self.client.get("/admin/festival/voto/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context["cl"].result_count, Voto.objects.count())
        for voto in (self.voto1, self.voto2):
            self.assertContains(r, voto.usuario.username)
            self.assertContains(r, voto.opcion.nombre)

    def test_CP08_el_panel_es_de_solo_lectura(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get("/admin/festival/voto/add/").status_code, 403)
        self.assertEqual(self.client.post(f"/admin/festival/voto/{self.voto1.pk}/delete/", {"post": "yes"}).status_code, 403)
        self.assertEqual(Voto.objects.count(), 2)

    def test_CP08_un_usuario_normal_no_accede_a_los_votos_del_panel(self):
        self.client.force_login(self.ana)
        r = self.client.get("/admin/festival/voto/")
        self.assertEqual(r.status_code, 302)
        self.assertIn("/admin/login/", r["Location"])

    def test_CP08_los_filtros_del_panel_funcionan(self):
        self.client.force_login(self.admin)
        r = self.client.get(f"/admin/festival/voto/?categoria__id__exact={self.d.cat_a.pk}")
        self.assertEqual(r.context["cl"].result_count, 1)
        r = self.client.get("/admin/festival/voto/?q=luis")
        self.assertEqual(r.context["cl"].result_count, 1)


class CP09_Concurrencia(TransactionTestCase):
    """Usa TransactionTestCase: las filas se confirman (commit) y los hilos las ven, como en producción."""

    HILOS = 8

    def _lanzar(self, funcion):
        barrera = threading.Barrier(self.HILOS)
        resultados = []

        def hilo(i):
            try:
                barrera.wait()
                resultados.append(funcion(i))
            except Exception as error:  # el resultado se analiza después
                resultados.append(error)
            finally:
                connection.close()

        hilos = [threading.Thread(target=hilo, args=(i,)) for i in range(self.HILOS)]
        for h in hilos:
            h.start()
        for h in hilos:
            h.join()
        return resultados

    def test_CP09_solicitudes_simultaneas_dejan_un_solo_voto(self):
        d = preparar()
        usuario = User.objects.create_user("ana", "ana@example.com", "ClaveMuySegura_9876")
        opciones = d.ops["a1"] + d.ops["a2"]   # mezcla de los dos subeventos de la misma categoría

        resultados = self._lanzar(lambda i: registrar_voto(usuario, opciones[i % 4].votacion_id, opciones[i % 4].pk))

        registrados = [r for r in resultados if isinstance(r, Voto)]
        rechazados = [r for r in resultados if isinstance(r, VotoError) and r.codigo == "duplicado"]
        inesperados = [r for r in resultados if not isinstance(r, (Voto, VotoError))]
        self.assertEqual(inesperados, [])
        self.assertEqual(len(registrados), 1)
        self.assertEqual(len(rechazados), self.HILOS - 1)
        self.assertEqual(Voto.objects.filter(usuario=usuario, categoria=d.cat_a).count(), 1)

    def test_CP09_la_base_de_datos_sola_tambien_impide_duplicados_simultaneos(self):
        """Sin pasar por la validación de la vista: solo la restricción única de MySQL."""
        d = preparar()
        usuario = User.objects.create_user("ana", "ana@example.com", "ClaveMuySegura_9876")
        opcion = d.ops["a1"][0]

        def insertar(i):
            return Voto.objects.create(usuario=usuario, edicion=d.edicion, categoria=d.cat_a, votacion=d.v_a1, opcion=opcion)

        resultados = self._lanzar(insertar)
        self.assertEqual(len([r for r in resultados if isinstance(r, Voto)]), 1)
        self.assertEqual(len([r for r in resultados if isinstance(r, IntegrityError)]), self.HILOS - 1)
        self.assertEqual(Voto.objects.count(), 1)


class CP10_ApiCategorias(TestCase):
    def setUp(self):
        self.d = preparar()

    def _json(self, url="/api/categorias/"):
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
        self.assertIn("application/json", r["Content-Type"])
        return json.loads(r.content)

    def test_CP10_devuelve_json_valido_con_categorias_y_opciones_reales(self):
        datos = self._json()
        self.assertEqual(datos["total"], 2)
        nombres = {c["nombre"] for c in datos["categorias"]}
        self.assertEqual(nombres, {"Acordeón", "Piqueria"})
        acordeon = next(c for c in datos["categorias"] if c["nombre"] == "Acordeón")
        self.assertEqual(acordeon["edicion"]["anio"], 2027)
        self.assertEqual(len(acordeon["votaciones"]), 2)
        titulos_op = {o["nombre"] for v in acordeon["votaciones"] for o in v["opciones"]}
        esperados = set(OpcionParticipante.objects.filter(votacion__categoria=self.d.cat_a).values_list("nombre", flat=True))
        self.assertEqual(titulos_op, esperados)   # coincide con lo guardado en MySQL

    def test_CP10_no_expone_borradores_opciones_inactivas_ni_categorias_ocultas(self):
        d = self.d
        Votacion.objects.create(categoria=d.cat_a, titulo="Secreta", estado=E.BORRADOR)
        d.ops["b"][0].activa = False
        d.ops["b"][0].save()
        oculta = Categoria.objects.create(edicion=d.edicion, nombre="Oculta", activa=False)
        Votacion.objects.create(categoria=oculta, titulo="V oculta", estado=E.ABIERTA)
        texto = json.dumps(self._json(), ensure_ascii=False)
        self.assertNotIn("Secreta", texto)
        self.assertNotIn("Mejor verso 1", texto)
        self.assertNotIn("Oculta", texto)
        self.assertIn("Mejor verso 2", texto)

    def test_CP10_filtro_por_edicion_y_parametro_invalido(self):
        Edicion.objects.create(anio=2030, nombre="Otra", publicada=True)
        self.assertEqual(self._json("/api/categorias/?edicion=2027")["total"], 2)
        self.assertEqual(self._json("/api/categorias/?edicion=2030")["total"], 0)
        r = self.client.get("/api/categorias/?edicion=abc")
        self.assertEqual(r.status_code, 400)
        self.assertIn("error", json.loads(r.content))

    def test_CP10_solo_acepta_get(self):
        for metodo in ("post", "put", "delete"):
            self.assertEqual(getattr(self.client, metodo)("/api/categorias/").status_code, 405)

    def test_CP10_conserva_tildes_en_el_json(self):
        r = self.client.get("/api/categorias/")
        self.assertIn("Acordeón", r.content.decode("utf-8"))


class IntegridadDelModelo(TestCase):
    def test_voto_con_datos_incoherentes_se_rechaza(self):
        from django.core.exceptions import ValidationError
        d = preparar()
        usuario = User.objects.create_user("ana", "ana@example.com", "ClaveMuySegura_9876")
        with self.assertRaises(ValidationError):   # la opción es de Piqueria, pero la votación es de Acordeón
            Voto.objects.create(usuario=usuario, edicion=d.edicion, categoria=d.cat_a, votacion=d.v_a1, opcion=d.ops["b"][0])
        with self.assertRaises(ValidationError):   # la votación no es de la categoría indicada
            Voto.objects.create(usuario=usuario, edicion=d.edicion, categoria=d.cat_b, votacion=d.v_a1, opcion=d.ops["a1"][0])

    def test_no_se_puede_borrar_un_usuario_ni_una_opcion_con_votos(self):
        from django.db.models import ProtectedError
        d = preparar()
        usuario = User.objects.create_user("ana", "ana@example.com", "ClaveMuySegura_9876")
        Voto.objects.create(usuario=usuario, edicion=d.edicion, categoria=d.cat_a, votacion=d.v_a1, opcion=d.ops["a1"][0])
        with self.assertRaises(ProtectedError):
            usuario.delete()
        with self.assertRaises(ProtectedError):
            d.ops["a1"][0].delete()
