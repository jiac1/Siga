"""accounts/views.py"""
from urllib.parse import urlencode

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme


def _en_suite():
    return getattr(settings, "SUITE_MODE", "standalone") == "suite"


def login_view(request):
    if _en_suite():
        # En la Suite la identidad la gestiona core (inicio de sesión único).
        destino = request.GET.get("next") or reverse("malla:dashboard")
        return redirect(f"{settings.SUITE_LOGIN_URL}?{urlencode({'next': destino})}")

    if request.user.is_authenticated:
        return redirect("malla:dashboard")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user:
            if user.organization and not user.organization.activa:
                messages.error(request, "Tu institución no tiene acceso activo.")
            else:
                login(request, user)
                destino = request.GET.get("next", "")
                if not url_has_allowed_host_and_scheme(destino, {request.get_host()}, request.is_secure()):
                    destino = reverse("malla:dashboard")
                return redirect(destino)
        else:
            messages.error(request, "Usuario o contraseña incorrectos.")

    return render(request, "accounts/login.html")


def logout_view(request):
    logout(request)
    if _en_suite():
        return redirect(settings.SUITE_LOGOUT_URL)
    return redirect("accounts:login")


@login_required
def profile_view(request):
    return render(request, "accounts/profile.html", {"user": request.user})
