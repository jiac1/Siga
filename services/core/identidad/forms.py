from django import forms
from django.contrib.auth import password_validation

from .models import Organizacion, Usuario


class IngresoForm(forms.Form):
    email = forms.EmailField(
        label="Correo institucional", widget=forms.EmailInput(attrs={"autocomplete": "email", "autofocus": True})
    )
    password = forms.CharField(
        label="Contraseña", widget=forms.PasswordInput(attrs={"autocomplete": "current-password"})
    )


class RegistroForm(forms.Form):
    first_name = forms.CharField(label="Nombres", max_length=150)
    last_name = forms.CharField(label="Apellidos", max_length=150)
    email = forms.EmailField(label="Correo institucional")
    password1 = forms.CharField(label="Contraseña", widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}))
    password2 = forms.CharField(
        label="Repite la contraseña", widget=forms.PasswordInput(attrs={"autocomplete": "new-password"})
    )

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if Usuario.objects.filter(email=email).exists():
            raise forms.ValidationError("Ya existe una cuenta con ese correo.")
        org = next((o for o in Organizacion.objects.filter(activa=True) if o.acepta_correo(email)), None)
        if org is None:
            raise forms.ValidationError("Usa el correo institucional de una universidad adherida a la Suite.")
        self.organizacion = org
        return email

    def clean(self):
        datos = super().clean()
        p1, p2 = datos.get("password1"), datos.get("password2")
        if p1 and p2 and p1 != p2:
            self.add_error("password2", "Las contraseñas no coinciden.")
        if p1:
            candidato = Usuario(
                email=datos.get("email", ""),
                first_name=datos.get("first_name", ""),
                last_name=datos.get("last_name", ""),
            )
            try:
                password_validation.validate_password(p1, candidato)
            except forms.ValidationError as exc:
                self.add_error("password1", exc)
        return datos
