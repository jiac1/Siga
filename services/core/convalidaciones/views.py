"""API de convalidación: sugerencias, envío de solicitudes y consulta de estado."""

from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import permissions, serializers, status
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, ScopedRateThrottle
from rest_framework.views import APIView

from catalogo.models import Carrera
from identidad.sso import auditar

from . import servicio
from .models import Item, Solicitud

RETENCION_DIAS = getattr(settings, "CONVALIDACION_RETENCION_DIAS", 730)


# ── Validación de RUT (módulo 11), igual que el formulario del postulante ──
def rut_valido(valor: str) -> bool:
    r = "".join(c for c in valor.upper() if c.isdigit() or c == "K")
    if len(r) < 8 or len(r) > 9:
        return False
    cuerpo, dv = r[:-1], r[-1]
    if not cuerpo.isdigit():
        return False
    suma, mul = 0, 2
    for d in reversed(cuerpo):
        suma += int(d) * mul
        mul = 2 if mul == 7 else mul + 1
    resto = 11 - suma % 11
    return dv == ("0" if resto == 11 else "K" if resto == 10 else str(resto))


class ItemEntradaSerializer(serializers.Serializer):
    nombre = serializers.CharField(max_length=250)
    texto = serializers.CharField(required=False, allow_blank=True, max_length=20000)
    asignatura_origen_id = serializers.IntegerField(required=False, allow_null=True)
    nota = serializers.DecimalField(
        max_digits=3, decimal_places=1, required=False, allow_null=True, min_value=1, max_value=7
    )
    aprobada = serializers.BooleanField(required=False, allow_null=True)


class SugerenciasSerializer(serializers.Serializer):
    carrera_destino = serializers.SlugRelatedField(
        slug_field="slug", queryset=Carrera.objects.filter(universidad__es_destino=True)
    )
    asignaturas = ItemEntradaSerializer(many=True, max_length=80)


# ── Serializadores de respuesta (documentación OpenAPI) ──
class CandidatoSerializer(serializers.Serializer):
    codigo = serializers.CharField()
    nombre = serializers.CharField()
    semestre = serializers.IntegerField(allow_null=True)
    creditos = serializers.IntegerField(allow_null=True)
    score = serializers.FloatField(help_text="Puntaje 0-1 (≥0,45 convalidable)")
    estado = serializers.ChoiceField(choices=["convalidable", "revision", "sin_coincidencia"])
    fuente = serializers.ChoiceField(choices=["motor", "precedente"])
    concepto = serializers.ListField(child=serializers.CharField(), allow_null=True, required=False)
    destino_id = serializers.IntegerField(allow_null=True)


class ResultadoAsignaturaSerializer(serializers.Serializer):
    nombre = serializers.CharField()
    asignatura_origen_id = serializers.IntegerField(allow_null=True)
    mejor = CandidatoSerializer(allow_null=True)
    candidatos = CandidatoSerializer(many=True)


class SugerenciasRespuestaSerializer(serializers.Serializer):
    carrera_destino = serializers.CharField()
    resultados = ResultadoAsignaturaSerializer(many=True)


class ResumenSerializer(serializers.Serializer):
    total = serializers.IntegerField()
    convalidables = serializers.IntegerField()
    aprobados = serializers.IntegerField()
    pendientes = serializers.IntegerField()


class SolicitudRespuestaSerializer(serializers.Serializer):
    folio = serializers.CharField()
    estado = serializers.CharField()
    resumen = ResumenSerializer()
    resultados = ResultadoAsignaturaSerializer(many=True)


class ItemEstadoSerializer(serializers.Serializer):
    asignatura_origen = serializers.CharField()
    decision = serializers.CharField()
    asignatura_unab = serializers.CharField(allow_null=True)


class EstadoSolicitudSerializer(serializers.Serializer):
    folio = serializers.CharField()
    estado = serializers.CharField()
    estado_texto = serializers.CharField()
    carrera_destino = serializers.CharField()
    creada_en = serializers.DateTimeField()
    resumen = ResumenSerializer()
    items = ItemEstadoSerializer(many=True)


class SugerenciasView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [AnonRateThrottle]

    @extend_schema(
        summary="Sugerir equivalencias UNAB para asignaturas de origen",
        request=SugerenciasSerializer,
        responses=SugerenciasRespuestaSerializer,
    )
    def post(self, request):
        s = SugerenciasSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        resultado = servicio.sugerir(s.validated_data["carrera_destino"], s.validated_data["asignaturas"])
        return Response({"carrera_destino": s.validated_data["carrera_destino"].slug, "resultados": resultado})


class SolicitudEntradaSerializer(serializers.Serializer):
    tipo_documento = serializers.ChoiceField(choices=Solicitud.TipoDocumento.choices)
    documento = serializers.CharField(max_length=20)
    nombres = serializers.CharField(max_length=120)
    apellidos = serializers.CharField(max_length=120)
    correo = serializers.EmailField()
    telefono = serializers.CharField(max_length=20, required=False, allow_blank=True)
    consentimiento = serializers.BooleanField()
    carrera_destino = serializers.SlugRelatedField(
        slug_field="slug", queryset=Carrera.objects.filter(universidad__es_destino=True)
    )
    carrera_origen = serializers.SlugRelatedField(
        slug_field="slug",
        queryset=Carrera.objects.filter(universidad__es_destino=False),
        required=False,
        allow_null=True,
    )
    institucion_origen_texto = serializers.CharField(max_length=200, required=False, allow_blank=True)
    certificado_verificacion = serializers.JSONField(required=False)
    asignaturas = ItemEntradaSerializer(many=True, min_length=1, max_length=80)

    def validate_consentimiento(self, v):
        if not v:
            raise serializers.ValidationError("Se requiere el consentimiento para tratar los datos personales.")
        return v

    def validate(self, datos):
        if datos["tipo_documento"] == "rut" and not rut_valido(datos["documento"]):
            raise serializers.ValidationError({"documento": "RUT inválido."})
        return datos


class SolicitudesView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_scope = "solicitudes"
    throttle_classes = [ScopedRateThrottle]

    @extend_schema(
        summary="Registrar una solicitud de convalidación (postulante)",
        request=SolicitudEntradaSerializer,
        responses={201: SolicitudRespuestaSerializer},
    )
    def post(self, request):
        s = SolicitudEntradaSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        # Las asignaturas elegidas desde el catálogo se vinculan a su registro de origen
        # (por id o por nombre exacto) para poder crear precedentes al resolver.
        validos_origen, por_nombre = set(), {}
        if d.get("carrera_origen"):
            for pk, nombre in d["carrera_origen"].asignaturas.values_list("pk", "nombre"):
                validos_origen.add(pk)
                por_nombre.setdefault(nombre.strip().lower(), pk)
        for entrada in d["asignaturas"]:
            if not entrada.get("asignatura_origen_id"):
                entrada["asignatura_origen_id"] = por_nombre.get(entrada["nombre"].strip().lower())
        # Las sugerencias se recalculan en el servidor: no se confía en el puntaje enviado por el cliente.
        sugerencias = servicio.sugerir(d["carrera_destino"], d["asignaturas"])
        ahora = timezone.now()
        with transaction.atomic():
            sol = Solicitud.objects.create(
                tipo_documento=d["tipo_documento"],
                documento=d["documento"].strip().upper(),
                nombres=d["nombres"].strip(),
                apellidos=d["apellidos"].strip(),
                correo=d["correo"].lower(),
                telefono=d.get("telefono", ""),
                consentimiento=True,
                consentimiento_en=ahora,
                carrera_destino=d["carrera_destino"],
                carrera_origen=d.get("carrera_origen"),
                institucion_origen_texto=d.get("institucion_origen_texto", ""),
                certificado_verificacion=d.get("certificado_verificacion") or {},
                eliminar_desde=(ahora + timedelta(days=RETENCION_DIAS)).date(),
            )
            items = []
            for entrada, sug in zip(d["asignaturas"], sugerencias, strict=True):
                mejor = sug["mejor"] or {}
                aprobada = entrada.get("aprobada")
                estado = (
                    Item.Sugerencia.NO_APROBADA
                    if aprobada is False
                    else (mejor.get("estado") or Item.Sugerencia.SIN_COINCIDENCIA)
                )
                origen_id = entrada.get("asignatura_origen_id")
                items.append(
                    Item(
                        solicitud=sol,
                        asignatura_origen_nombre=entrada["nombre"],
                        asignatura_origen_id=origen_id if origen_id in validos_origen else None,
                        nota=entrada.get("nota"),
                        aprobada_en_origen=aprobada,
                        asignatura_destino_id=mejor.get("destino_id"),
                        puntaje=mejor.get("score"),
                        estado_sugerido=estado,
                        fuente_sugerencia=mejor.get("fuente", "motor"),
                    )
                )
            Item.objects.bulk_create(items)
        auditar(
            request._request,
            "convalidacion_solicitud",
            usuario=None,
            folio=sol.folio,
            carrera=sol.carrera_destino.slug,
            items=len(items),
        )
        send_mail(
            f"Recibimos tu solicitud de convalidación {sol.folio}",
            f"Hola {sol.nombres}:\n\nRegistramos tu solicitud {sol.folio} para {sol.carrera_destino.nombre}.\n"
            f"La Dirección de Carrera la revisará y te contactará a este correo.\n\n"
            f"El resultado preliminar es orientativo y no reemplaza la resolución oficial.",
            None,
            [sol.correo],
            fail_silently=True,
        )
        return Response(
            {"folio": sol.folio, "estado": sol.estado, "resumen": sol.resumen, "resultados": sugerencias},
            status=status.HTTP_201_CREATED,
        )


class EstadoSolicitudView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [AnonRateThrottle]

    @extend_schema(
        summary="Consultar el estado de una solicitud (requiere el correo del postulante)",
        parameters=[OpenApiParameter("correo", str, required=True)],
        responses=EstadoSolicitudSerializer,
    )
    def get(self, request, folio):
        sol = get_object_or_404(Solicitud, folio=folio.upper(), correo=request.query_params.get("correo", "").lower())
        return Response(
            {
                "folio": sol.folio,
                "estado": sol.estado,
                "estado_texto": sol.get_estado_display(),
                "carrera_destino": sol.carrera_destino.nombre,
                "creada_en": sol.creada_en,
                "resumen": sol.resumen,
                "items": [
                    {
                        "asignatura_origen": i.asignatura_origen_nombre,
                        "decision": i.get_decision_display(),
                        "asignatura_unab": str(i.asignatura_destino_final or "")
                        if i.decision == Item.Decision.APROBADA
                        else None,
                    }
                    for i in sol.items.select_related("asignatura_destino_final")
                ],
            }
        )
