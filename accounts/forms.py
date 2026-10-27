from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

User = get_user_model()


class RegistroForm(UserCreationForm):
    """Registro de votantes con el sistema de usuarios incorporado de Django."""

    email = forms.EmailField(label="Correo electrónico", max_length=254)
    acepta_datos = forms.BooleanField(
        label="Acepto el tratamiento de mis datos personales (Ley 1581 de 2012)",
        error_messages={"required": "Debes aceptar el tratamiento de datos para registrarte."},
    )

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Ya existe una cuenta con este correo electrónico.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user
