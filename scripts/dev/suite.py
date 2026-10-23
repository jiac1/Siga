"""Orquestador de desarrollo local de Suite UNAB (sin Docker; Windows, macOS o Linux).

Replica en una sola máquina la topología de AWS: un único dominio
(http://localhost:8080) que enruta por prefijo igual que el ALB/CloudFront:

    /core/*          -> servicio core          (127.0.0.1:8001)
    /mapa-calor/*    -> Mapa de Calor          (127.0.0.1:8002)
    /estres-malla/*  -> Estrés de Malla        (127.0.0.1:8003)
    /*               -> portal estático        (services/portal)

Uso:
    python scripts/dev/suite.py preparar        migra BD, carga catálogo y datos demo
    python scripts/dev/suite.py iniciar         levanta la Suite completa (modo suite)
    python scripts/dev/suite.py independiente   cada app por separado, como el prototipo

Requiere haber instalado las dependencias:  pip install -r requirements-dev.txt
"""

from __future__ import annotations

import argparse
import http.client
import http.server
import os
import signal
import subprocess
import sys
import time
import webbrowser
from functools import partial
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
SERVICIOS = RAIZ / "services"
PY = sys.executable
PUERTO_GATEWAY = int(os.environ.get("SUITE_PUERTO", "8080"))

# Secreto SOLO para desarrollo local; en AWS viene de Secrets Manager.
SECRETO_DEV = "dev-local-suite-unab-sso-0123456789abcdef"


def cargar_env(ruta: Path = RAIZ / ".env") -> None:
    """Carga variables KEY=VALUE de .env (sin dependencias); no pisa las ya definidas."""
    if not ruta.exists():
        return
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if linea and not linea.startswith("#") and "=" in linea:
            clave, _, valor = linea.partition("=")
            os.environ.setdefault(clave.strip(), valor.strip().strip('"'))


RUTAS = {  # prefijo -> (servicio, puerto)
    "/core/": ("core", 8001),
    "/mapa-calor/": ("mapa-calor", 8002),
    "/estres-malla/": ("estres-malla", 8003),
}


def entorno(servicio: str, prefijo: str, modo: str) -> dict:
    env = dict(os.environ)
    env.update(
        {
            "DEBUG": "True",
            "PYTHONUNBUFFERED": "1",
            "PYTHONIOENCODING": "utf-8",
            "SUITE_MODE": modo,
            "URL_PREFIX": prefijo,
            "SUITE_SSO_SECRET": env.get("SUITE_SSO_SECRET", SECRETO_DEV),
            "ALLOWED_HOSTS": "localhost,127.0.0.1",
            "CSRF_TRUSTED_ORIGINS": f"http://localhost:{PUERTO_GATEWAY},http://127.0.0.1:{PUERTO_GATEWAY}",
        }
    )
    return env


def manage(servicio: str, *args, prefijo="", modo="suite", check=True):
    return subprocess.run(
        [PY, "manage.py", *args], cwd=SERVICIOS / servicio, env=entorno(servicio, prefijo, modo), check=check
    )


def preparar(_args):
    print("» Generando catálogo de mallas…")
    subprocess.run([PY, str(RAIZ / "scripts" / "catalogo" / "build_catalogo_universidades.py")], check=True)
    print("» core: migraciones, módulos, catálogo y usuarios demo")
    manage("core", "migrate", "--noinput", prefijo="core/")
    manage("core", "cargar_catalogo", prefijo="core/")
    os.environ.setdefault("SUITE_ADMIN_EMAIL", "admin@unab.cl")
    manage("core", "inicializar_suite", "--demo", prefijo="core/")
    print("» estres-malla: migraciones y carrera base")
    manage("estres-malla", "migrate", "--noinput", prefijo="estres-malla/")
    manage("estres-malla", "inicializar_mallaiq", "--demo", prefijo="estres-malla/")
    print("\nListo. Las contraseñas demo se definen en .env (ver .env.example) o se mostraron arriba.")


class Gateway(http.server.SimpleHTTPRequestHandler):
    """Proxy inverso por prefijo + servidor de archivos del portal."""

    protocol_version = "HTTP/1.1"

    def _destino(self):
        for prefijo, (_, puerto) in RUTAS.items():
            if self.path == prefijo.rstrip("/") or self.path.startswith(prefijo):
                return puerto
        return None

    def _proxy(self, puerto: int):
        largo = int(self.headers.get("Content-Length") or 0)
        cuerpo = self.rfile.read(largo) if largo else None
        cabeceras = {k: v for k, v in self.headers.items() if k.lower() not in ("connection", "keep-alive")}
        cabeceras["X-Forwarded-For"] = self.client_address[0]
        cabeceras["X-Forwarded-Proto"] = "http"
        cabeceras["X-Forwarded-Host"] = self.headers.get("Host", "")
        try:
            con = http.client.HTTPConnection("127.0.0.1", puerto, timeout=120)
            con.request(self.command, self.path, body=cuerpo, headers=cabeceras)
            resp = con.getresponse()
            datos = resp.read()
        except OSError:
            self.send_error(502, "Servicio no disponible (¿está iniciado?)")
            return
        self.send_response(resp.status, resp.reason)
        for k, v in resp.getheaders():
            if k.lower() not in ("transfer-encoding", "connection", "content-length"):
                self.send_header(k, v)
        self.send_header("Content-Length", str(len(datos)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(datos)

    def _manejar(self):
        puerto = self._destino()
        if puerto:
            return self._proxy(puerto)
        if self.command in ("GET", "HEAD"):
            return super().do_GET() if self.command == "GET" else super().do_HEAD()
        self.send_error(405)

    do_GET = do_POST = do_PUT = do_PATCH = do_DELETE = do_HEAD = _manejar

    def end_headers(self):
        if not self._destino():
            self.send_header("Cache-Control", "no-store")  # en desarrollo, sin caché del portal
        super().end_headers()

    def log_message(self, fmt, *args):
        sys.stderr.write("[gateway] " + (fmt % args) + "\n")


def _lanzar(procesos, nombre, comando, cwd, env):
    print(f"» {nombre}: {' '.join(comando[-2:])}")
    procesos.append(subprocess.Popen(comando, cwd=cwd, env=env))


def _esperar_y_cerrar(procesos, servidor=None):
    def cerrar(*_):
        print("\nDeteniendo la Suite…")
        for p in procesos:
            p.terminate()
        if servidor:
            servidor.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGINT, cerrar)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, cerrar)
    return cerrar


def iniciar(args):
    procesos = []
    for prefijo, (servicio, puerto) in RUTAS.items():
        _lanzar(
            procesos,
            servicio,
            [PY, "manage.py", "runserver", f"127.0.0.1:{puerto}", "--noreload"],
            SERVICIOS / servicio,
            entorno(servicio, prefijo.strip("/") + "/", "suite"),
        )
    handler = partial(Gateway, directory=str(SERVICIOS / "portal"))
    servidor = http.server.ThreadingHTTPServer(("127.0.0.1", PUERTO_GATEWAY), handler)
    cerrar = _esperar_y_cerrar(procesos, servidor)
    url = f"http://localhost:{PUERTO_GATEWAY}/"
    print(f"\nSuite UNAB disponible en {url}   (Ctrl+C para detener)\n")
    if not args.sin_navegador:
        time.sleep(2)
        webbrowser.open(url)
    try:
        servidor.serve_forever()
    finally:
        cerrar()


def independiente(args):
    """Cada módulo por separado (sin SSO), como funcionaba el prototipo."""
    procesos = []
    _lanzar(
        procesos,
        "portal",
        [PY, "-m", "http.server", "8791", "--directory", str(SERVICIOS / "portal")],
        RAIZ,
        dict(os.environ),
    )
    _lanzar(
        procesos,
        "mapa-calor",
        [PY, "manage.py", "runserver", "127.0.0.1:8792", "--noreload"],
        SERVICIOS / "mapa-calor",
        entorno("mapa-calor", "", "standalone"),
    )
    _lanzar(
        procesos,
        "estres-malla",
        [PY, "manage.py", "runserver", "127.0.0.1:8793", "--noreload"],
        SERVICIOS / "estres-malla",
        entorno("estres-malla", "", "standalone"),
    )
    _esperar_y_cerrar(procesos)
    print("\nModo independiente: portal http://localhost:8791/ · Mapa de Calor :8792 · Estrés de Malla :8793")
    if not args.sin_navegador:
        time.sleep(2)
        webbrowser.open("http://localhost:8791/index.html")
    for p in procesos:
        p.wait()


def main():
    ap = argparse.ArgumentParser(description="Suite UNAB · entorno de desarrollo local")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("preparar").set_defaults(fn=preparar)
    for nombre, fn in (("iniciar", iniciar), ("independiente", independiente)):
        p = sub.add_parser(nombre)
        p.add_argument("--sin-navegador", action="store_true")
        p.set_defaults(fn=fn)
    args = ap.parse_args()
    cargar_env()
    args.fn(args)


if __name__ == "__main__":
    main()
