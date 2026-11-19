"""API REST de optimización combinatoria de horarios (UCTP)."""

from __future__ import annotations

import threading
import uuid

from django.core.mail import send_mail
from django.db import close_old_connections
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .campus import SalaCampus, construir_campus_desde_secciones, resolver_campus_global
from .models import TrabajoPlanificacionCampus
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


class SalaCampusSerializer(serializers.Serializer):
    """Sala física disponible para planificación global de campus."""

    id_sala = serializers.CharField(max_length=40)
    capacidad = serializers.IntegerField(min_value=1, max_value=2000)
    edificio = serializers.CharField(max_length=40, required=False, allow_blank=True, default="")


class PlanificarCampusEntradaSerializer(serializers.Serializer):
    """Payload para lanzar la optimización global de tabla maestra de campus."""

    secciones = SeccionSerializer(many=True, min_length=1, max_length=2500)
    salas = SalaCampusSerializer(many=True, min_length=1, max_length=500)
    perfiles_estudiantes = serializers.ListField(
        child=serializers.ListField(child=serializers.CharField(max_length=40)),
        required=False,
        default=list,
    )
    presupuesto_segundos = serializers.FloatField(min_value=0.2, max_value=300.0, required=False, default=60.0)
    iteraciones = serializers.IntegerField(min_value=100, max_value=50_000, required=False, default=4_000)
    email_notificacion = serializers.EmailField(required=False, allow_blank=True, default="")
    ejecucion_sincrona = serializers.BooleanField(required=False, default=False)


def _ejecutar_trabajo_campus(
    trabajo_id: uuid.UUID,
    secciones: list[SeccionNRC],
    salas: list[SalaCampus],
    perfiles: list[list[str]],
    presupuesto_segundos: float,
    iteraciones: int,
) -> None:
    """Ejecuta el solver global de campus, persiste resultados y notifica por correo."""
    close_old_connections()
    trabajo = TrabajoPlanificacionCampus.objects.get(id=trabajo_id)
    trabajo.estado = TrabajoPlanificacionCampus.ESTADO_EN_PROCESO
    trabajo.save(update_fields=["estado"])
    try:
        clases = construir_campus_desde_secciones(secciones, salas)
        res = resolver_campus_global(
            clases,
            salas,
            perfiles_estudiantes=perfiles or None,
            iteraciones=iteraciones,
            presupuesto_segundos=presupuesto_segundos,
        )
        m = res.metricas
        payload = {
            "algoritmo": res.algoritmo,
            "tiempo_ms": res.tiempo_ms,
            "metricas": m.__dict__,
            "no_asignadas": res.no_asignadas,
            "asignaciones": [
                {
                    "id_clase": a.id_clase,
                    "curso": a.curso,
                    "actividad": a.actividad,
                    "id_sala": a.id_sala,
                    "docente": a.docente,
                    "slots": [list(s) for s in a.slots],
                }
                for a in res.asignaciones
            ],
        }
        trabajo.estado = TrabajoPlanificacionCampus.ESTADO_COMPLETADO
        trabajo.total_clases = m.total_clases
        trabajo.clases_asignadas = m.clases_asignadas
        trabajo.conflictos_h2 = m.conflictos_sala_h2
        trabajo.conflictos_h3 = m.conflictos_docente_h3
        trabajo.conflictos_estudiantes = m.conflictos_estudiantes
        trabajo.tiempo_ms = res.tiempo_ms
        trabajo.resultado = payload
        trabajo.completado_en = timezone.now()
        trabajo.save()

        if trabajo.email_notificacion:
            send_mail(
                f"[SIGA-DSS] Tabla maestra de campus completada ({m.clases_asignadas}/{m.total_clases} clases)",
                (
                    f"La planificación global de campus (ID: {trabajo.id}) finalizó en {res.tiempo_ms:.1f} ms.\n\n"
                    f"- Clases asignadas: {m.clases_asignadas}/{m.total_clases} ({m.tasa_asignacion_pct}%)\n"
                    f"- Conflictos sala (H2): {m.conflictos_sala_h2}\n"
                    f"- Conflictos docente (H3): {m.conflictos_docente_h3}\n"
                    f"- Conflictos estudiantiles agregados: {m.conflictos_estudiantes}\n"
                ),
                None,
                [trabajo.email_notificacion],
                fail_silently=True,
            )
    except Exception as exc:  # pragma: no cover - resguardo operativo de hilo
        trabajo.estado = TrabajoPlanificacionCampus.ESTADO_ERROR
        trabajo.error_detalle = str(exc)
        trabajo.completado_en = timezone.now()
        trabajo.save()
    finally:
        close_old_connections()


class PlanificarCampusView(APIView):
    """Lanza la planificación global asíncrona (hasta 300 s) de tabla maestra con aviso por correo."""

    @extend_schema(
        summary="Planificar tabla maestra de campus (asíncrono con aviso por correo)",
        request=PlanificarCampusEntradaSerializer,
    )
    def post(self, request):
        """Registra un trabajo de asignación de campus y lo ejecuta en segundo plano o síncrono."""
        s = PlanificarCampusEntradaSerializer(data=request.data)
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
        salas = [
            SalaCampus(id_sala=sl["id_sala"], capacidad=sl["capacidad"], edificio=sl.get("edificio", ""))
            for sl in d["salas"]
        ]

        trabajo = TrabajoPlanificacionCampus.objects.create(
            email_notificacion=d.get("email_notificacion", ""),
            presupuesto_segundos=d["presupuesto_segundos"],
            total_clases=len(secciones),
        )

        if d["ejecucion_sincrona"]:
            _ejecutar_trabajo_campus(
                trabajo.id,
                secciones,
                salas,
                d.get("perfiles_estudiantes", []),
                d["presupuesto_segundos"],
                d["iteraciones"],
            )
            trabajo.refresh_from_db()
            return Response(
                {
                    "trabajo_id": str(trabajo.id),
                    "estado": trabajo.estado,
                    "presupuesto_segundos": trabajo.presupuesto_segundos,
                    "clases_asignadas": trabajo.clases_asignadas,
                    "total_clases": trabajo.total_clases,
                    "conflictos_h2": trabajo.conflictos_h2,
                    "conflictos_h3": trabajo.conflictos_h3,
                    "resultado": trabajo.resultado,
                },
                status=status.HTTP_200_OK,
            )

        hilo = threading.Thread(
            target=_ejecutar_trabajo_campus,
            args=(
                trabajo.id,
                secciones,
                salas,
                d.get("perfiles_estudiantes", []),
                d["presupuesto_segundos"],
                d["iteraciones"],
            ),
            daemon=True,
        )
        hilo.start()
        return Response(
            {
                "trabajo_id": str(trabajo.id),
                "estado": trabajo.estado,
                "presupuesto_segundos": trabajo.presupuesto_segundos,
                "email_notificacion": trabajo.email_notificacion,
            },
            status=status.HTTP_202_ACCEPTED,
        )


class EstadoPlanificacionCampusView(APIView):
    """Consulta el estado y la tabla maestra generada de un trabajo de campus."""

    @extend_schema(summary="Consultar estado de trabajo de planificación global de campus")
    def get(self, request, trabajo_id: uuid.UUID):
        """Retorna el estado actual, métricas y resultado del trabajo ``trabajo_id``."""
        trabajo = TrabajoPlanificacionCampus.objects.filter(id=trabajo_id).first()
        if trabajo is None:
            return Response({"detalle": "Trabajo no encontrado"}, status=status.HTTP_404_NOT_FOUND)
        return Response(
            {
                "trabajo_id": str(trabajo.id),
                "estado": trabajo.estado,
                "presupuesto_segundos": trabajo.presupuesto_segundos,
                "total_clases": trabajo.total_clases,
                "clases_asignadas": trabajo.clases_asignadas,
                "conflictos_h2": trabajo.conflictos_h2,
                "conflictos_h3": trabajo.conflictos_h3,
                "conflictos_estudiantes": trabajo.conflictos_estudiantes,
                "tiempo_ms": trabajo.tiempo_ms,
                "resultado": trabajo.resultado,
            }
        )
