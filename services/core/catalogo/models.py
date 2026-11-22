"""Catálogo curricular: mallas UNAB (destino) y de universidades de origen."""

from django.db import models


class Universidad(models.Model):
    sigla = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=200)
    region = models.CharField(max_length=80, default="Metropolitana")
    es_destino = models.BooleanField(default=False, help_text="Institución propietaria de la Suite (UNAB)")

    class Meta:
        verbose_name = "universidad"
        verbose_name_plural = "universidades"
        ordering = ["nombre"]

    def __str__(self):
        return f"{self.nombre} ({self.sigla})"


class Carrera(models.Model):
    """Una malla concreta (carrera + plan) de una universidad."""

    universidad = models.ForeignKey(Universidad, on_delete=models.CASCADE, related_name="carreras")
    slug = models.SlugField(max_length=120, unique=True)
    nombre = models.CharField(max_length=250)
    area = models.CharField(max_length=20, db_index=True)
    plan = models.CharField(max_length=250, blank=True)
    regimen = models.CharField(max_length=60, default="semestral")
    duracion = models.PositiveSmallIntegerField(default=10)
    fuente_url = models.URLField(max_length=500, blank=True)
    fuente_consultada = models.DateField(null=True, blank=True)
    fuente_metodo = models.CharField(max_length=250, blank=True)
    notas = models.TextField(blank=True)
    vigente = models.BooleanField(default=True)

    class Meta:
        verbose_name = "carrera / malla"
        verbose_name_plural = "carreras / mallas"
        ordering = ["universidad__nombre", "nombre"]

    def __str__(self):
        return f"{self.universidad.sigla} · {self.nombre}"


class Asignatura(models.Model):
    carrera = models.ForeignKey(Carrera, on_delete=models.CASCADE, related_name="asignaturas")
    codigo = models.CharField(max_length=30, blank=True)
    nombre = models.CharField(max_length=250)
    semestre = models.PositiveSmallIntegerField()
    creditos = models.PositiveSmallIntegerField(null=True, blank=True)
    contenidos = models.TextField(blank=True, help_text="Descripción/contenidos (si la fuente los publica)")
    aprendizajes = models.JSONField(default=list, blank=True)
    generica = models.BooleanField(default=False, help_text="Cupo electivo/minor/formación general")
    semestre_incierto = models.BooleanField(default=False)

    class Meta:
        verbose_name = "asignatura"
        verbose_name_plural = "asignaturas"
        ordering = ["carrera", "semestre", "id"]
        indexes = [models.Index(fields=["carrera", "generica"])]

    def __str__(self):
        return f"{self.codigo + ' · ' if self.codigo else ''}{self.nombre}"
