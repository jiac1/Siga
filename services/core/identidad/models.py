"""Identidad, instituciones (tenants), módulos y licencias de la Suite.

Modelo comercial tipo "suite": una institución puede licenciar la Suite
completa o solo algunos módulos; cada usuario ve las apps que su
institución tiene contratadas y que su rol permite usar.
"""

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone


class Organizacion(models.Model):
    """Institución cliente (universidad, facultad o campus)."""

    nombre = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, help_text="Identificador corto, ej.: unab")
    dominios_correo = models.CharField(
        max_length=300,
        blank=True,
        help_text="Dominios de correo institucional separados por coma (ej.: unab.cl,uandresbello.edu)",
    )
    activa = models.BooleanField(default=True)
    creada_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "institución"
        verbose_name_plural = "instituciones"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre

    def acepta_correo(self, correo: str) -> bool:
        dominio = correo.rsplit("@", 1)[-1].lower()
        return dominio in {d.strip().lower() for d in self.dominios_correo.split(",") if d.strip()}

    def modulos_licenciados(self):
        hoy = timezone.localdate()
        return (
            Modulo.objects.filter(
                licencias__organizacion=self,
                licencias__activa=True,
                activo=True,
            )
            .filter(models.Q(licencias__vigente_hasta__isnull=True) | models.Q(licencias__vigente_hasta__gte=hoy))
            .distinct()
        )


class Rol(models.TextChoices):
    SUPERADMIN = "superadmin", "Operador de la Suite"
    ADMIN_INSTITUCION = "admin_institucion", "Administrador de institución"
    STAFF = "staff", "Personal académico / Servicio al Estudiante"
    DOCENTE = "docente", "Docente / Jefatura de carrera"
    ESTUDIANTE = "estudiante", "Estudiante"


class UsuarioManager(BaseUserManager):
    use_in_migrations = True

    def _crear(self, email, password, **extra):
        if not email:
            raise ValueError("El correo es obligatorio")
        usuario = self.model(email=self.normalize_email(email).lower(), **extra)
        usuario.set_password(password)
        usuario.save(using=self._db)
        return usuario

    def create_user(self, email, password=None, **extra):
        extra.setdefault("is_staff", False)
        extra.setdefault("is_superuser", False)
        return self._crear(email, password, **extra)

    def create_superuser(self, email, password=None, **extra):
        extra.update(is_staff=True, is_superuser=True, rol=Rol.SUPERADMIN)
        return self._crear(email, password, **extra)


class Usuario(AbstractUser):
    """Usuario de la Suite; inicia sesión con su correo."""

    username = None
    email = models.EmailField("correo", unique=True)
    organizacion = models.ForeignKey(
        Organizacion,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="usuarios",
        verbose_name="institución",
    )
    rol = models.CharField(max_length=24, choices=Rol.choices, default=Rol.ESTUDIANTE)
    correo_verificado = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
    objects = UsuarioManager()

    class Meta:
        verbose_name = "usuario"
        verbose_name_plural = "usuarios"

    def __str__(self):
        return f"{self.get_full_name() or self.email} ({self.get_rol_display()})"

    @property
    def nombre_visible(self) -> str:
        return self.get_full_name() or self.email.split("@")[0]

    def roles(self) -> list[str]:
        roles = [self.rol]
        if self.is_superuser and Rol.SUPERADMIN not in roles:
            roles.append(Rol.SUPERADMIN)
        return roles

    def modulos_habilitados(self):
        """Módulos licenciados por la institución que el rol del usuario puede usar."""
        if self.is_superuser:
            return Modulo.objects.filter(activo=True)
        if not self.organizacion or not self.organizacion.activa:
            return Modulo.objects.none()
        return [m for m in self.organizacion.modulos_licenciados() if m.permite_rol(self.rol)]


class Modulo(models.Model):
    """Aplicación de la Suite (equivalente a un producto dentro de un paquete)."""

    class Tipo(models.TextChoices):
        ESTATICO = "estatico", "Front-end estático (S3/CloudFront)"
        SERVICIO = "servicio", "Servicio con backend (ECS)"

    slug = models.SlugField(unique=True)
    nombre = models.CharField(max_length=80)
    descripcion = models.TextField(blank=True)
    ruta = models.CharField(max_length=200, help_text="Ruta bajo el dominio de la Suite, ej.: /mapa-calor/")
    tipo = models.CharField(max_length=10, choices=Tipo.choices, default=Tipo.ESTATICO)
    icono = models.CharField(max_length=4, default="•", help_text="Sigla corta mostrada en el portal")
    color = models.CharField(max_length=9, default="#102338")
    roles_permitidos = models.CharField(
        max_length=200,
        default="superadmin,admin_institucion,staff,docente,estudiante",
        help_text="Roles separados por coma que pueden usar el módulo",
    )
    acceso_publico = models.BooleanField(
        default=False, help_text="Usable sin iniciar sesión (ej.: convalidación para postulantes)"
    )
    orden = models.PositiveSmallIntegerField(default=10)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "módulo"
        verbose_name_plural = "módulos"
        ordering = ["orden", "nombre"]

    def __str__(self):
        return self.nombre

    def permite_rol(self, rol: str) -> bool:
        return rol in {r.strip() for r in self.roles_permitidos.split(",")}


class Licencia(models.Model):
    """Contrato de una institución sobre un módulo (o la suite completa)."""

    class Plan(models.TextChoices):
        PILOTO = "piloto", "Piloto"
        ESTANDAR = "estandar", "Estándar"
        SUITE = "suite", "Suite completa"

    organizacion = models.ForeignKey(
        Organizacion, on_delete=models.CASCADE, related_name="licencias", verbose_name="institución"
    )
    modulo = models.ForeignKey(Modulo, on_delete=models.CASCADE, related_name="licencias")
    plan = models.CharField(max_length=10, choices=Plan.choices, default=Plan.ESTANDAR)
    activa = models.BooleanField(default=True)
    vigente_desde = models.DateField(default=timezone.localdate)
    vigente_hasta = models.DateField(null=True, blank=True, help_text="Vacío = sin vencimiento")
    usuarios_maximos = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        verbose_name = "licencia"
        verbose_name_plural = "licencias"
        unique_together = [("organizacion", "modulo")]

    def __str__(self):
        return f"{self.organizacion} · {self.modulo} ({self.get_plan_display()})"

    @property
    def vigente(self) -> bool:
        hoy = timezone.localdate()
        return self.activa and self.vigente_desde <= hoy and (self.vigente_hasta is None or self.vigente_hasta >= hoy)


class EventoAuditoria(models.Model):
    """Registro inmutable de eventos de seguridad y de negocio relevantes."""

    momento = models.DateTimeField(auto_now_add=True, db_index=True)
    usuario = models.ForeignKey(Usuario, null=True, blank=True, on_delete=models.SET_NULL)
    accion = models.CharField(max_length=60, db_index=True)
    detalle = models.JSONField(default=dict, blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        verbose_name = "evento de auditoría"
        verbose_name_plural = "auditoría"
        ordering = ["-momento"]

    def __str__(self):
        return f"{self.momento:%Y-%m-%d %H:%M} {self.accion}"
