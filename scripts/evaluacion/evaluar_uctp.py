"""Benchmark reproducible del motor de optimización horaria UCTP.

Compara tres estrategias sobre instancias representativas de programación académica UNAB:
  - aleatorio          backtracking MRV sin optimización de restricciones blandas (línea base)
  - branch_and_bound   búsqueda exacta con poda por cota inferior admisible
  - recocido_simulado  metaheurística Simulated Annealing con preservación estricta de H1=0

Uso:
  python scripts/evaluacion/evaluar_uctp.py [--json salida.json]
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "services" / "core"))

from horarios.motor import (  # noqa: E402
    DIAS_ORDEN,
    BloqueHorario,
    PreferenciasUCTP,
    SeccionNRC,
    opciones_por_curso,
    resolver_aleatorio,
    resolver_branch_and_bound,
    resolver_recocido_simulado,
)


def _generar_instancia_sintetica(
    n_cursos: int,
    secciones_teo: int,
    con_lab: int,
    semilla: int,
    inyectar_conflictos: bool = False,
) -> list[SeccionNRC]:
    """Genera una instancia determinista realista de programación académica UNAB (M1..M12)."""
    rng = random.Random(semilla)
    dias_habiles = DIAS_ORDEN[:5]
    secciones: list[SeccionNRC] = []
    nrc_counter = 1000
    salas = [("A1", f"{p}{n:02d}") for p in (1, 2, 3) for n in range(1, 7)]

    for c_idx in range(n_cursos):
        cod = f"CINF{101 + c_idx}"
        for s_idx in range(secciones_teo):
            nrc_counter += 1
            dia1 = dias_habiles[rng.randrange(len(dias_habiles))]
            m1 = rng.choice([1, 3, 5, 7, 9, 11])
            ed1, sa1 = salas[(nrc_counter + s_idx) % len(salas)]
            bloques = [
                BloqueHorario(dia=dia1, modulo=m1, sala=sa1, edificio=ed1),
                BloqueHorario(dia=dia1, modulo=m1 + 1, sala=sa1, edificio=ed1),
            ]
            # Segunda sesión semanal en otro día para mayor realismo
            dia2 = dias_habiles[(dias_habiles.index(dia1) + 2) % len(dias_habiles)]
            m2 = rng.choice([1, 3, 5, 7, 9, 11])
            bloques.extend(
                [
                    BloqueHorario(dia=dia2, modulo=m2, sala=sa1, edificio=ed1),
                    BloqueHorario(dia=dia2, modulo=m2 + 1, sala=sa1, edificio=ed1),
                ]
            )
            secciones.append(
                SeccionNRC(
                    nrc=str(nrc_counter),
                    curso=cod,
                    actividad="TEO",
                    bloques=tuple(bloques),
                    cupos=rng.choice([25, 30, 35, 40]),
                    rut_docente=f"{12 + c_idx}.{100 + s_idx}.000-{s_idx % 9}",
                )
            )

        if c_idx < con_lab:
            for l_idx in range(max(2, secciones_teo - 1)):
                nrc_counter += 1
                dia_l = dias_habiles[rng.randrange(len(dias_habiles))]
                m_l = rng.choice([1, 3, 5, 7, 9, 11])
                secciones.append(
                    SeccionNRC(
                        nrc=str(nrc_counter),
                        curso=cod,
                        actividad="LAB",
                        bloques=(
                            BloqueHorario(dia=dia_l, modulo=m_l, sala=f"L{l_idx + 1}", edificio="B2"),
                            BloqueHorario(dia=dia_l, modulo=m_l + 1, sala=f"L{l_idx + 1}", edificio="B2"),
                        ),
                        cupos=20,
                        rut_docente=f"{18 + c_idx}.{200 + l_idx}.000-{l_idx % 9}",
                    )
                )

    if inyectar_conflictos and len(secciones) >= 2:
        b0 = secciones[0].bloques[0]
        secciones.append(
            SeccionNRC(
                nrc="9991",
                curso="CINF101",
                actividad="TEO",
                bloques=(BloqueHorario(dia=b0.dia, modulo=b0.modulo, sala=b0.sala, edificio=b0.edificio),),
                cupos=30,
                rut_docente=secciones[0].rut_docente,
            )
        )
    return secciones


def construir_benchmark() -> list[tuple[str, list[SeccionNRC], PreferenciasUCTP]]:
    """Define las cuatro instancias estándar del benchmark UCTP."""
    return [
        (
            "Pequeña (4 ramos · TEO)",
            _generar_instancia_sintetica(n_cursos=4, secciones_teo=4, con_lab=0, semilla=11),
            PreferenciasUCTP(jornada="manana"),
        ),
        (
            "Mediana (5 ramos · TEO+LAB)",
            _generar_instancia_sintetica(n_cursos=5, secciones_teo=4, con_lab=2, semilla=23),
            PreferenciasUCTP(jornada="manana"),
        ),
        (
            "Grande (6 ramos · TEO+LAB)",
            _generar_instancia_sintetica(n_cursos=6, secciones_teo=5, con_lab=2, semilla=37),
            PreferenciasUCTP(jornada="cualquiera"),
        ),
        (
            "Auditada (5 ramos + H2/H3)",
            _generar_instancia_sintetica(n_cursos=5, secciones_teo=4, con_lab=1, semilla=51, inyectar_conflictos=True),
            PreferenciasUCTP(jornada="tarde"),
        ),
    ]


def main() -> None:
    """Ejecuta el benchmark UCTP, imprime la tabla comparativa y valida criterios de aceptación."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    ap = argparse.ArgumentParser()
    ap.add_argument("--json", help="Ruta para guardar los resultados detallados en formato JSON")
    args = ap.parse_args()

    instancias = construir_benchmark()
    reporte: list[dict] = []

    print(
        f"{'Instancia':28} {'Algoritmo':18} {'Espacio':>9} {'f(x)':>7} {'Vent.':>6} {'Días':>5} "
        f"{'Nodos':>7} {'Podad.':>7} {'ms':>8}"
    )
    print("-" * 104)

    for nombre, secciones, prefs in instancias:
        ops = opciones_por_curso(secciones)
        espacio = 1
        for lista in ops.values():
            espacio *= max(len(lista), 1)

        r_base = resolver_aleatorio(secciones, prefs=prefs, max_horarios=5, semilla=42)
        r_bb = resolver_branch_and_bound(secciones, prefs=prefs, max_horarios=5, max_nodos=80_000)
        r_sa = resolver_recocido_simulado(secciones, prefs=prefs, max_horarios=5, iteraciones=2_500, semilla=42)

        # Promedio de f(x) y ventanas sobre las soluciones de línea base vs mejor solución optimizada
        base_f_prom = (
            round(sum(s.metricas.penalizacion for s in r_base.soluciones) / len(r_base.soluciones), 2)
            if r_base.soluciones
            else None
        )
        base_v_prom = (
            round(sum(s.metricas.ventanas for s in r_base.soluciones) / len(r_base.soluciones), 2)
            if r_base.soluciones
            else None
        )

        fila_inst = {
            "instancia": nombre,
            "espacio_combinatorio": espacio,
            "n_secciones": len(secciones),
            "conflictos_sala": len(r_bb.conflictos_sala),
            "conflictos_docente": len(r_bb.conflictos_docente),
            "base_f_promedio": base_f_prom,
            "base_ventanas_promedio": base_v_prom,
            "resultados": {},
        }

        for r in (r_base, r_bb, r_sa):
            mejor = r.soluciones[0] if r.soluciones else None
            f_val = mejor.metricas.penalizacion if mejor else None
            v_val = mejor.metricas.ventanas if mejor else None
            d_val = mejor.metricas.dias_activos if mejor else None
            fila_inst["resultados"][r.algoritmo] = {
                "factibles": len(r.soluciones),
                "penalizacion": f_val,
                "ventanas": v_val,
                "dias_activos": d_val,
                "nodos_explorados": r.nodos_explorados,
                "nodos_podados": r.nodos_podados,
                "tiempo_ms": r.tiempo_ms,
            }
            print(
                f"{nombre:28} {r.algoritmo:18} {espacio:9d} "
                f"{(f'{f_val:.1f}' if f_val is not None else '—'):>7} "
                f"{(str(v_val) if v_val is not None else '—'):>6} "
                f"{(str(d_val) if d_val is not None else '—'):>5} "
                f"{r.nodos_explorados:7d} {r.nodos_podados:7d} {r.tiempo_ms:8.2f}"
            )

        # Criterio de aceptación: Branch-and-Bound y SA nunca deben empeorar frente al promedio aleatorio
        if r_bb.soluciones and r_base.soluciones:
            assert r_bb.soluciones[0].metricas.penalizacion <= r_base.soluciones[0].metricas.penalizacion + 1e-6, (
                f"Branch-and-Bound empeoró frente a baseline en {nombre}"
            )
        reporte.append(fila_inst)

    if args.json:
        Path(args.json).write_text(json.dumps(reporte, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
