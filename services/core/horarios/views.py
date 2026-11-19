"""API REST de optimización combinatoria de horarios (UCTP)."""

from __future__ import annotations

from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from .motor import BloqueHorario, PreferenciasUCTP, SeccionNRC, optimizar_horarios


class BloqueSerializer(serializers.Serializer):
    """Bloque temporal y espacio físico asociado a una sección."""

    dia = serializers.CharField(max_length=20)
    modulo = serializers.IntegerField(min_value=1, max_value=20)
    sala = serializers.CharField(max_length=40, required=False, allow_blank=True, default="")
    edificio = serializers.CharField(max_length=40, required=False, allow_blank=True, default="")


class SeccionSerializer(serializers.Serializer):
    """Sección ofertada (NRC) de una asignatura."""

    nrc = serializers.CharField(max_length=30)
    curso = serializers.CharField(max_length=40)
    actividad = serializers.CharField(max_length=20, default="TEO")
    bloques = BloqueSerializer(many=True, min_length=1)
    cupos = serializers.IntegerField(min_value=0, required=False, default=0)
    inscritos = serializers.IntegerField(min_value=0, required=False, default=0)
    rut_docente = serializers.CharField(max_length=20, required=False, allow_blank=True, default="")
    nombre_docente = serializers.CharField(max_length=120, required=False, allow_blank=True, default="")
    nombre_curso = serializers.CharField(max_length=200, required=False, allow_blank=True, default="")


class PreferenciasSerializer(serializers.Serializer):
    """Preferencias del estudiante y pesos de restricciones blandas."""

    jornada = serializers.ChoiceField(
        choices=["cualquiera", "manana", "tarde", "vespertino"],
        required=False,
        default="cualquiera",
    )
    peso_ventanas = serializers.FloatField(min_value=0.0, required=False, default=3.0)
    peso_dias = serializers.FloatField(min_value=0.0, required=False, default=2.0)
    peso_jornada = serializers.FloatField(min_value=0.0, required=False, default=1.5)
    peso_sobrecarga = serializers.FloatField(min_value=0.0, required=False, default=1.0)
    max_modulos_dia = serializers.IntegerField(min_value=1, max_value=20, required=False, default=6)


class OptimizarHorariosEntradaSerializer(serializers.Serializer):
    """Payload de entrada para la optimización combinatoria de horarios."""

    secciones = SeccionSerializer(many=True, min_length=1, max_length=500)
    preferencias = PreferenciasSerializer(required=False)
    algoritmo = serializers.ChoiceField(
        choices=["branch_and_bound", "recocido_simulado", "aleatorio"],
        required=False,
        default="branch_and_bound",
    )
    max_horarios = serializers.IntegerField(min_value=1, max_value=12, required=False, default=5)
    disjuntos = serializers.BooleanField(required=False, default=False)


class OptimizarHorariosView(APIView):
    """Optimiza combinaciones de horarios sin topes (H1) y audita conflictos H2/H3."""

    @extend_schema(
        summary="Optimizar horarios sin topes (UCTP) y auditar conflictos de sala/docente",
        request=OptimizarHorariosEntradaSerializer,
    )
    def post(self, request):
        """Ejecuta el motor UCTP sobre las secciones enviadas y retorna soluciones óptimas."""
        s = OptimizarHorariosEntradaSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data

        secciones = [
            SeccionNRC(
                nrc=sec["nrc"],
                curso=sec["curso"],
                actividad=sec["actividad"],
                bloques=tuple(
                    BloqueHorario(
                        dia=b["dia"],
                        modulo=b["modulo"],
                        sala=b.get("sala", ""),
                        edificio=b.get("edificio", ""),
                    )
                    for b in sec["bloques"]
                ),
                cupos=sec.get("cupos", 0),
                inscritos=sec.get("inscritos", 0),
                rut_docente=sec.get("rut_docente", ""),
                nombre_docente=sec.get("nombre_docente", ""),
                nombre_curso=sec.get("nombre_curso", ""),
            )
            for sec in d["secciones"]
        ]

        p_raw = d.get("preferencias") or {}
        prefs = PreferenciasUCTP(
            jornada=p_raw.get("jornada", "cualquiera"),
            peso_ventanas=p_raw.get("peso_ventanas", 3.0),
            peso_dias=p_raw.get("peso_dias", 2.0),
            peso_jornada=p_raw.get("peso_jornada", 1.5),
            peso_sobrecarga=p_raw.get("peso_sobrecarga", 1.0),
            max_modulos_dia=p_raw.get("max_modulos_dia", 6),
        )

        res = optimizar_horarios(
            secciones=secciones,
            prefs=prefs,
            algoritmo=d["algoritmo"],
            max_horarios=d["max_horarios"],
            disjuntos=d["disjuntos"],
        )

        return Response(
            {
                "algoritmo": res.algoritmo,
                "tiempo_ms": res.tiempo_ms,
                "nodos_explorados": res.nodos_explorados,
                "nodos_podados": res.nodos_podados,
                "vacantes_sin_tope": res.vacantes_sin_tope,
                "conflictos_sala": [
                    {
                        "tipo": c.tipo,
                        "recurso": c.recurso,
                        "dia": c.dia,
                        "modulo": c.modulo,
                        "nrcs": list(c.nrcs),
                    }
                    for c in res.conflictos_sala
                ],
                "conflictos_docente": [
                    {
                        "tipo": c.tipo,
                        "recurso": c.recurso,
                        "dia": c.dia,
                        "modulo": c.modulo,
                        "nrcs": list(c.nrcs),
                    }
                    for c in res.conflictos_docente
                ],
                "soluciones": [
                    {
                        "metricas": {
                            "ventanas": sol.metricas.ventanas,
                            "dias_activos": sol.metricas.dias_activos,
                            "bloques_fuera_jornada": sol.metricas.bloques_fuera_jornada,
                            "exceso_carga_diaria": sol.metricas.exceso_carga_diaria,
                            "penalizacion": sol.metricas.penalizacion,
                        },
                        "asignacion": {curso: list(op.nrcs) for curso, op in sorted(sol.asignacion.items())},
                    }
                    for sol in res.soluciones
                ],
            }
        )
