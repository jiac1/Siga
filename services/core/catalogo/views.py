"""API pública de solo lectura del catálogo de mallas."""

from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, extend_schema_field
from rest_framework import permissions, serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Carrera, Universidad


class CarreraResumenSerializer(serializers.ModelSerializer):
    asignaturas = serializers.IntegerField(source="n_asignaturas", read_only=True)

    class Meta:
        model = Carrera
        fields = ["slug", "nombre", "area", "plan", "regimen", "duracion", "asignaturas"]


class UniversidadSerializer(serializers.ModelSerializer):
    carreras = serializers.SerializerMethodField()

    class Meta:
        model = Universidad
        fields = ["sigla", "nombre", "region", "carreras"]

    @extend_schema_field(CarreraResumenSerializer(many=True))
    def get_carreras(self, obj):
        return CarreraResumenSerializer(obj.carreras_anotadas, many=True).data


class AsignaturaSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    codigo = serializers.CharField(allow_blank=True)
    nombre = serializers.CharField()
    semestre = serializers.IntegerField()
    creditos = serializers.IntegerField(allow_null=True)
    generica = serializers.BooleanField()
    semestre_incierto = serializers.BooleanField()


class CarreraDetalleSerializer(serializers.ModelSerializer):
    universidad = serializers.CharField(source="universidad.nombre")
    sigla = serializers.CharField(source="universidad.sigla")
    fuente = serializers.SerializerMethodField()
    semestres = serializers.SerializerMethodField()

    class Meta:
        model = Carrera
        fields = [
            "slug",
            "nombre",
            "universidad",
            "sigla",
            "area",
            "plan",
            "regimen",
            "duracion",
            "fuente",
            "semestres",
        ]

    def get_fuente(self, obj) -> dict:
        return {
            "url": obj.fuente_url,
            "consultada": obj.fuente_consultada,
            "metodo": obj.fuente_metodo,
            "notas": obj.notas,
        }

    def get_semestres(self, obj) -> list[dict]:
        semestres: dict[int, list] = {}
        for a in obj.asignaturas.all():
            semestres.setdefault(a.semestre, []).append(AsignaturaSerializer(a).data)
        return [{"numero": n, "asignaturas": semestres[n]} for n in sorted(semestres)]


def _universidades(destino: bool):
    unis = Universidad.objects.filter(es_destino=destino).order_by("nombre")
    for u in unis:
        u.carreras_anotadas = (
            u.carreras.filter(vigente=True)
            .annotate(n_asignaturas=Count("asignaturas", filter=Q(asignaturas__generica=False)))
            .order_by("nombre")
        )
    return unis


class UniversidadesOrigenView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="Universidades de origen y sus mallas disponibles", responses=UniversidadSerializer(many=True)
    )
    def get(self, request):
        return Response(UniversidadSerializer(_universidades(False), many=True).data)


class CarrerasUnabView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="Carreras de destino (UNAB) del catálogo de convalidación", responses=UniversidadSerializer(many=True)
    )
    def get(self, request):
        return Response(UniversidadSerializer(_universidades(True), many=True).data)


class CarreraDetalleView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(summary="Malla completa de una carrera (con su fuente)", responses=CarreraDetalleSerializer)
    def get(self, request, slug):
        carrera = get_object_or_404(
            Carrera.objects.select_related("universidad").prefetch_related("asignaturas"), slug=slug
        )
        return Response(CarreraDetalleSerializer(carrera).data)
