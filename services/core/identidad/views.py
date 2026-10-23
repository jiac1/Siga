"""Inicio de sesión único de la Suite: páginas HTML y API de identidad."""

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.core import signing
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_http_methods
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, serializers, status
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from .forms import IngresoForm, RegistroForm
from .models import Modulo, Rol, Usuario
from .sso import auditar, poner_cookie, quitar_cookie

SAL_VERIFICACION = "suite-verificacion-correo"


def _destino_seguro(request, por_defecto=None):
    destino = request.POST.get("next") or request.GET.get("next") or ""
    if destino and url_has_allowed_host_and_scheme(destino, {request.get_host()}, request.is_secure()):
        return destino
    return por_defecto or settings.SUITE_PORTAL_URL


def _puede_ingresar(usuario) -> str | None:
    if not usuario.is_active:
        return "Tu cuenta está desactivada."
    if usuario.is_superuser:
        return None
    if usuario.organizacion is None:
        return "Tu cuenta no está asociada a ninguna institución."
    if not usuario.organizacion.activa:
        return "Tu institución no tiene acceso activo a la Suite."
    return None


def _iniciar(request, usuario, respuesta):
    login(request, usuario, backend="django.contrib.auth.backends.ModelBackend")
    request._suite_cookie_gestionada = True
    auditar(request, "login", usuario=usuario)
    return poner_cookie(respuesta, usuario)


# ── HTML ───────────────────────────────────────────────────────────
@require_http_methods(["GET", "POST"])
def ingresar(request):
    if request.user.is_authenticated and request.method == "GET":
        return poner_cookie(redirect(_destino_seguro(request)), request.user)
    form = IngresoForm(request.POST or None)
    error = None
    if request.method == "POST" and form.is_valid():
        usuario = authenticate(
            request, email=form.cleaned_data["email"].lower(), password=form.cleaned_data["password"]
        )
        if usuario is None:
            auditar(request, "login_fallido", usuario=None, email=form.cleaned_data["email"].lower())
            error = "Correo o contraseña incorrectos."
        else:
            error = _puede_ingresar(usuario)
            if error is None:
                return _iniciar(request, usuario, redirect(_destino_seguro(request)))
    return render(
        request,
        "core/ingresar.html",
        {
            "form": form,
            "error": error,
            "next": request.GET.get("next", ""),
            "registro_abierto": bool(settings.REGISTRO_DOMINIOS),
        },
    )


def salir(request):
    if request.user.is_authenticated:
        auditar(request, "logout")
    logout(request)
    request._suite_cookie_gestionada = True
    return quitar_cookie(redirect(settings.SUITE_LOGIN_URL))


@require_http_methods(["GET", "POST"])
def registro(request):
    if not settings.REGISTRO_DOMINIOS:
        return render(
            request,
            "core/mensaje.html",
            {
                "titulo": "Registro cerrado",
                "mensaje": "Las cuentas son creadas por el administrador de tu institución.",
            },
        )
    form = RegistroForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        d = form.cleaned_data
        verificar = settings.EMAIL_BACKEND != "django.core.mail.backends.console.EmailBackend" or not settings.DEBUG
        usuario = Usuario.objects.create_user(
            email=d["email"],
            password=d["password1"],
            first_name=d["first_name"],
            last_name=d["last_name"],
            organizacion=form.organizacion,
            rol=Rol.ESTUDIANTE,
            is_active=not verificar,
            correo_verificado=not verificar,
        )
        auditar(request, "registro", usuario=usuario, organizacion=form.organizacion.slug)
        if verificar:
            token = signing.dumps({"u": usuario.pk}, salt=SAL_VERIFICACION)
            enlace = request.build_absolute_uri(reverse("identidad:verificar", args=[token]))
            send_mail(
                "Activa tu cuenta de Suite UNAB",
                f"Hola {usuario.first_name}:\n\nActiva tu cuenta ingresando a:\n{enlace}\n\n"
                "El enlace vence en 48 horas.",
                None,
                [usuario.email],
            )
            return render(
                request,
                "core/mensaje.html",
                {"titulo": "Revisa tu correo", "mensaje": f"Enviamos un enlace de activación a {usuario.email}."},
            )
        return _iniciar(request, usuario, redirect(settings.SUITE_PORTAL_URL))
    return render(request, "core/registro.html", {"form": form})


def verificar(request, token):
    try:
        datos = signing.loads(token, salt=SAL_VERIFICACION, max_age=48 * 3600)
        usuario = Usuario.objects.get(pk=datos["u"])
    except (signing.BadSignature, Usuario.DoesNotExist):
        return render(
            request,
            "core/mensaje.html",
            {"titulo": "Enlace inválido", "mensaje": "El enlace de activación no es válido o ya venció."},
            status=400,
        )
    usuario.is_active = usuario.correo_verificado = True
    usuario.save(update_fields=["is_active", "correo_verificado"])
    auditar(request, "correo_verificado", usuario=usuario)
    return _iniciar(request, usuario, redirect(settings.SUITE_PORTAL_URL))


# ── API ────────────────────────────────────────────────────────────
class ModuloSerializer(serializers.ModelSerializer):
    habilitado = serializers.SerializerMethodField()

    class Meta:
        model = Modulo
        fields = [
            "slug",
            "nombre",
            "descripcion",
            "ruta",
            "tipo",
            "icono",
            "color",
            "acceso_publico",
            "orden",
            "habilitado",
        ]

    def get_habilitado(self, obj) -> bool:
        return obj.slug in self.context.get("habilitados", set()) or obj.acceso_publico


class UsuarioSerializer(serializers.ModelSerializer):
    nombre = serializers.CharField(source="nombre_visible")
    organizacion = serializers.SerializerMethodField()
    roles = serializers.SerializerMethodField()
    modulos = serializers.SerializerMethodField()

    class Meta:
        model = Usuario
        fields = ["id", "email", "nombre", "first_name", "last_name", "rol", "roles", "organizacion", "modulos"]

    def get_organizacion(self, obj) -> dict | None:
        return {"slug": obj.organizacion.slug, "nombre": obj.organizacion.nombre} if obj.organizacion else None

    def get_roles(self, obj) -> list[str]:
        return obj.roles()

    def get_modulos(self, obj) -> list[str]:
        return [m.slug for m in obj.modulos_habilitados()]


class MeView(APIView):
    @extend_schema(summary="Usuario autenticado y módulos habilitados", responses=UsuarioSerializer)
    def get(self, request):
        return Response(UsuarioSerializer(request.user).data)


class ModulosView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="Catálogo de módulos de la Suite con su estado para el usuario", responses=ModuloSerializer(many=True)
    )
    def get(self, request):
        habilitados = {m.slug for m in request.user.modulos_habilitados()} if request.user.is_authenticated else set()
        modulos = Modulo.objects.filter(activo=True)
        return Response(ModuloSerializer(modulos, many=True, context={"habilitados": habilitados}).data)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()


class LoginThrottle(AnonRateThrottle):
    rate = "10/min"


class LoginApiView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    throttle_classes = [LoginThrottle]

    @extend_schema(summary="Iniciar sesión (emite la cookie SSO)", request=LoginSerializer, responses=UsuarioSerializer)
    def post(self, request):
        s = LoginSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        usuario = authenticate(request, email=s.validated_data["email"].lower(), password=s.validated_data["password"])
        if usuario is None:
            auditar(request, "login_fallido", usuario=None, email=s.validated_data["email"].lower())
            return Response({"error": "credenciales_invalidas"}, status=status.HTTP_401_UNAUTHORIZED)
        motivo = _puede_ingresar(usuario)
        if motivo:
            return Response({"error": "acceso_denegado", "detalle": motivo}, status=status.HTTP_403_FORBIDDEN)
        return _iniciar(request._request, usuario, Response(UsuarioSerializer(usuario).data))


class LogoutApiView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(summary="Cerrar sesión en toda la Suite", request=None, responses={204: None})
    def post(self, request):
        if request.user.is_authenticated:
            auditar(request._request, "logout")
        logout(request._request)
        request._request._suite_cookie_gestionada = True
        return quitar_cookie(Response(status=status.HTTP_204_NO_CONTENT))
