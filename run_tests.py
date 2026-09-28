"""
run_tests.py — Ejecutor unificado de todas las pruebas Python de Suite UNAB
Ejecuta las suites de sznLogger, Gateway/Reverse Proxy, Mapa de Calor y Estrés de Malla
en procesos aislados para evitar colisiones de configuración en los settings de Django.
"""

import os
import subprocess
import sys
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

TEST_SUITES = [
    ("Motor de Logging (sznLogger)", os.path.join(BASE_DIR, "tests", "test_szn_logger.py")),
    ("Gateway y Reverse Proxy Unificado", os.path.join(BASE_DIR, "tests", "test_runner_gateway.py")),
    ("Django: Mapa de Calor", os.path.join(BASE_DIR, "tests", "test_mapa_calor.py")),
    ("Django: Estrés de Malla", os.path.join(BASE_DIR, "tests", "test_estres_malla.py")),
]


def main():
    print("\n" + "=" * 75)
    print(" [TESTS] SUITE UNAB - EJECUTOR DE PRUEBAS AUTOMATIZADAS (PYTHON)")
    print("=" * 75)

    all_passed = True
    start_total = time.time()
    results = []

    for name, script_path in TEST_SUITES:
        print(f"\n>> Ejecutando suite: {name} ...")
        t0 = time.time()
        proc = subprocess.run(
            [sys.executable, script_path],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        duration = round(time.time() - t0, 2)

        if proc.returncode == 0:
            print(f"   [PASS] {name} ({duration}s)")
            results.append((name, "PASS", duration))
        else:
            print(f"   [FAIL] {name} ({duration}s)")
            print("\n--- Salida del fallo ---")
            print(proc.stdout)
            print(proc.stderr)
            print("------------------------\n")
            results.append((name, "FAIL", duration))
            all_passed = False

    total_duration = round(time.time() - start_total, 2)
    print("\n" + "=" * 75)
    print(" RESUMEN DE PRUEBAS PYTHON:")
    for name, status, dur in results:
        badge = "[OK]  " if status == "PASS" else "[FAIL]"
        print(f"   {badge} {name:<40} ({dur}s)")
    print("-" * 75)

    if all_passed:
        print(f" [EXITO] Todas las suites Python pasaron limpiamente en {total_duration}s.")
        print("=" * 75 + "\n")
        sys.exit(0)
    else:
        print(f" [ERROR] Algunas suites fallaron. Tiempo total: {total_duration}s.")
        print("=" * 75 + "\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
