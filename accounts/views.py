from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import RegistroForm


class RegistroView(SuccessMessageMixin, CreateView):
    form_class = RegistroForm
    template_name = "accounts/registro.html"
    success_url = reverse_lazy("login")
    success_message = "Tu cuenta fue creada. Ahora puedes iniciar sesión."

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("inicio")
        return super().dispatch(request, *args, **kwargs)


class LoginView(auth_views.LoginView):
    template_name = "registration/login.html"
    redirect_authenticated_user = True

    def form_valid(self, form):
        respuesta = super().form_valid(form)
        messages.success(self.request, f"Bienvenido, {form.get_user().get_username()}.")
        return respuesta


class LogoutView(auth_views.LogoutView):
    """Cierra la sesión únicamente por POST (con token CSRF)."""

    def post(self, request, *args, **kwargs):
        respuesta = super().post(request, *args, **kwargs)
        messages.success(request, "Cerraste sesión correctamente.")
        return respuesta


@login_required
def perfil(request):
    """Única página que exige autenticación en esta entrega."""
    return render(request, "accounts/perfil.html")
