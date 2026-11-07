"""
Demuestra la protección contra votos duplicados simultáneos.

    python manage.py probar_concurrencia            # lanza 8 votos a la vez de un mismo usuario
    python manage.py probar_concurrencia --limpiar  # elimina el usuario y los votos de la prueba

Crea (si no existe) el usuario «concurrencia_demo», borra sus votos y lanza varias solicitudes
simultáneas hacia la MISMA categoría. Debe quedar exactamente un voto en MySQL.
"""
import threading

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import connection

from festival.models import Categoria, OpcionParticipante, Votacion, Voto
from festival.services import VotoError, estado_votacion, registrar_voto

USERNAME = "concurrencia_demo"


class Command(BaseCommand):
    help = "Lanza votos simultáneos de un mismo usuario en una categoría y comprueba que solo se registre uno."

    def add_arguments(self, parser):
        parser.add_argument("--hilos", type=int, default=8, help="Cantidad de solicitudes simultáneas (por defecto 8).")
        parser.add_argument("--limpiar", action="store_true", help="Elimina el usuario y los votos de la prueba.")

    def handle(self, *args, **opciones):
        User = get_user_model()
        if opciones["limpiar"]:
            usuario = User.objects.filter(username=USERNAME).first()
            if usuario:
                borrados = Voto.objects.filter(usuario=usuario).delete()[0]
                usuario.delete()
                self.stdout.write(self.style.WARNING(f"Eliminados: usuario «{USERNAME}» y {borrados} voto(s)."))
            else:
                self.stdout.write("No hay nada que limpiar.")
            return

        # Busca una categoría con al menos una votación abierta y opciones activas.
        categoria, candidatas = None, []
        for c in Categoria.objects.filter(activa=True, edicion__publicada=True).select_related("edicion"):
            candidatas = []
            for v in Votacion.objects.filter(categoria=c).select_related("categoria__edicion"):
                if estado_votacion(v)[0]:
                    candidatas += [(v.pk, o.pk) for o in OpcionParticipante.objects.filter(votacion=v, activa=True)]
            if candidatas:
                categoria = c
                break
        if not categoria:
            raise CommandError("No hay votaciones abiertas. Ejecuta primero: python manage.py cargar_demo")

        usuario, _ = User.objects.get_or_create(username=USERNAME, defaults={"email": "concurrencia@example.com"})
        Voto.objects.filter(usuario=usuario).delete()

        n = max(2, opciones["hilos"])
        self.stdout.write(f"Categoría: {categoria.nombre} · Usuario: {USERNAME} · Solicitudes simultáneas: {n}")
        barrera = threading.Barrier(n)
        resultados = []

        def intento(i):
            votacion_id, opcion_id = candidatas[i % len(candidatas)]
            try:
                barrera.wait()
                voto = registrar_voto(usuario, votacion_id, opcion_id)
                resultados.append(("REGISTRADO", f"hilo {i + 1}: voto {voto.pk} por «{voto.opcion.nombre}»"))
            except VotoError as error:
                resultados.append(("RECHAZADO", f"hilo {i + 1}: {error.codigo}"))
            finally:
                connection.close()

        hilos = [threading.Thread(target=intento, args=(i,)) for i in range(n)]
        for h in hilos:
            h.start()
        for h in hilos:
            h.join()

        for estado, detalle in sorted(resultados, key=lambda r: r[1]):
            self.stdout.write(f"  {estado:<10} {detalle}")
        total = Voto.objects.filter(usuario=usuario, categoria=categoria).count()
        registrados = sum(1 for r in resultados if r[0] == "REGISTRADO")
        self.stdout.write(f"Solicitudes registradas: {registrados} · Rechazadas: {n - registrados}")
        if total == 1:
            self.stdout.write(self.style.SUCCESS(f"Votos en MySQL para esta categoría: {total}. La concurrencia quedó controlada."))
        else:
            self.stdout.write(self.style.ERROR(f"Votos en MySQL para esta categoría: {total}. Se esperaba 1."))
