"""Pruebas de autenticación (códigos A01..A12 en docs/tabla_pruebas.md)."""
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

User = get_user_model()

DATOS_VALIDOS = {
    "username": "votante1",
    "email": "votante1@example.com",
    "password1": "ClaveMuySegura_9876",
    "password2": "ClaveMuySegura_9876",
    "acepta_datos": "on",
}


class RegistroTests(TestCase):
    def test_A01_pagina_de_registro(self):
        r = self.client.get(reverse("registro"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Crear cuenta")

    def test_A02_registro_valido_crea_usuario_con_contrasena_cifrada(self):
        r = self.client.post(reverse("registro"), DATOS_VALIDOS, follow=True)
        self.assertRedirects(r, reverse("login"))
        self.assertContains(r, "Tu cuenta fue creada")
        usuario = User.objects.get(username="votante1")
        self.assertNotEqual(usuario.password, DATOS_VALIDOS["password1"])
        self.assertTrue(usuario.password.startswith("pbkdf2_sha256$"))
        self.assertTrue(usuario.check_password(DATOS_VALIDOS["password1"]))

    def test_A03_contrasenas_diferentes(self):
        datos = {**DATOS_VALIDOS, "password2": "otra-distinta-123"}
        r = self.client.post(reverse("registro"), datos)
        self.assertEqual(r.status_code, 200)
        self.assertFalse(User.objects.filter(username="votante1").exists())
        self.assertContains(r, "no coinciden")

    def test_A04_correo_duplicado(self):
        User.objects.create_user("otro", "VOTANTE1@example.com", "x" * 12)
        r = self.client.post(reverse("registro"), DATOS_VALIDOS)
        self.assertContains(r, "Ya existe una cuenta con este correo")
        self.assertFalse(User.objects.filter(username="votante1").exists())

    def test_A05_exige_aceptar_tratamiento_de_datos(self):
        datos = {k: v for k, v in DATOS_VALIDOS.items() if k != "acepta_datos"}
        r = self.client.post(reverse("registro"), datos)
        self.assertContains(r, "Debes aceptar el tratamiento de datos")
        self.assertFalse(User.objects.filter(username="votante1").exists())

    def test_A06_contrasena_comun_es_rechazada(self):
        datos = {**DATOS_VALIDOS, "password1": "password", "password2": "password"}
        r = self.client.post(reverse("registro"), datos)
        self.assertEqual(r.status_code, 200)
        self.assertFalse(User.objects.filter(username="votante1").exists())

    def test_A07_registro_exige_token_csrf(self):
        cliente = Client(enforce_csrf_checks=True)
        r = cliente.post(reverse("registro"), DATOS_VALIDOS)
        self.assertEqual(r.status_code, 403)


class SesionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.usuario = User.objects.create_user("ana", "ana@example.com", "ClaveMuySegura_9876")

    def test_A08_login_correcto_redirige_al_inicio(self):
        r = self.client.post(reverse("login"), {"username": "ana", "password": "ClaveMuySegura_9876"}, follow=True)
        self.assertRedirects(r, reverse("inicio"))
        self.assertContains(r, "Bienvenido, ana")
        self.assertTrue(r.context["user"].is_authenticated)

    def test_A09_login_incorrecto_muestra_error(self):
        r = self.client.post(reverse("login"), {"username": "ana", "password": "mala"})
        self.assertEqual(r.status_code, 200)
        self.assertFalse(r.context["user"].is_authenticated)
        self.assertContains(r, "introduzca un nombre de usuario y clave correctos")  # mensaje estándar de Django

    def test_A10_logout_por_post_cierra_la_sesion(self):
        self.client.force_login(self.usuario)
        r = self.client.post(reverse("logout"), follow=True)
        self.assertRedirects(r, reverse("inicio"))
        self.assertFalse(r.context["user"].is_authenticated)
        self.assertContains(r, "Cerraste sesión correctamente")

    def test_A11_logout_por_get_no_esta_permitido(self):
        self.client.force_login(self.usuario)
        r = self.client.get(reverse("logout"))
        self.assertEqual(r.status_code, 405)
        self.assertIn("_auth_user_id", self.client.session)

    def test_A12_logout_exige_token_csrf(self):
        cliente = Client(enforce_csrf_checks=True)
        cliente.force_login(self.usuario)
        self.assertEqual(cliente.post(reverse("logout")).status_code, 403)

    def test_A13_perfil_requiere_autenticacion(self):
        r = self.client.get(reverse("perfil"))
        self.assertRedirects(r, f"{reverse('login')}?next={reverse('perfil')}")
        self.client.force_login(self.usuario)
        r = self.client.get(reverse("perfil"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "ana@example.com")

    def test_A14_usuario_autenticado_no_ve_el_registro(self):
        self.client.force_login(self.usuario)
        self.assertRedirects(self.client.get(reverse("registro")), reverse("inicio"))

    def test_A15_navegacion_cambia_segun_la_sesion(self):
        r = self.client.get(reverse("inicio"))
        self.assertContains(r, "Iniciar sesión")
        self.assertNotContains(r, "Cerrar sesión")
        self.client.force_login(self.usuario)
        r = self.client.get(reverse("inicio"))
        self.assertContains(r, "Cerrar sesión")
        self.assertContains(r, "csrfmiddlewaretoken")
