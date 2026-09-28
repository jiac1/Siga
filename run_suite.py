"""
run_suite.py - Orquestador Unificado de Suite UNAB
Levanta los 3 servicios (Portal Estático, Mapa de Calor y Estrés de Malla)
en una única ventana de consola, bajo un único puerto público (8791),
con logs centralizados, coloreados y rotativos a través de sznLogger.
"""

import http.client
from http.server import HTTPServer, SimpleHTTPRequestHandler
import os
import signal
import socketserver
import subprocess
import sys
import threading
import time
import urllib.parse
import webbrowser

import sznLogger

# Configuración de directorios y puertos
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "suite-unab")
MAPA_DIR = os.path.join(STATIC_DIR, "apps", "mapa-calor")
ESTRES_DIR = os.path.join(STATIC_DIR, "apps", "estres-malla")

GATEWAY_PORT = 8791
MAPA_PORT = 8792
ESTRES_PORT = 8793

# Loggers por subsistema
logger_runner  = sznLogger.get_logger("runner")
logger_gateway = sznLogger.get_logger("gateway")
logger_shell   = sznLogger.get_logger("shell")
logger_mapa    = sznLogger.get_logger("mapa")
logger_estres  = sznLogger.get_logger("estres")


def clean_stale_ports(ports):
    """Detecta y finaliza procesos huérfanos que estén escuchando en los puertos indicados."""
    for port in ports:
        try:
            out = subprocess.check_output(
                f"netstat -ano | findstr :{port} | findstr LISTENING",
                shell=True,
                text=True,
                stderr=subprocess.DEVNULL,
            )
            for line in out.strip().splitlines():
                parts = line.strip().split()
                if parts:
                    pid = parts[-1]
                    if pid and pid != "0" and pid != str(os.getpid()):
                        logger_runner.warning(
                            f"Puerto {port} ocupado por PID {pid}. Liberando..."
                        )
                        subprocess.run(
                            f"taskkill /PID {pid} /F",
                            shell=True,
                            capture_output=True,
                        )
        except Exception:
            pass


def kill_proc_tree(proc):
    """Termina de forma forzada un proceso y todo su árbol de subprocesos hijos."""
    if proc and proc.poll() is None:
        try:
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                capture_output=True,
                timeout=5,
            )
        except Exception:
            try:
                proc.terminate()
                proc.wait(timeout=2)
            except Exception:
                proc.kill()


def stream_reader(pipe, child_logger):
    """Hilo demonio que consume stdout/stderr de un subproceso y lo redirige a sznLogger."""
    try:
        for line in iter(pipe.readline, ""):
            clean = line.strip()
            if clean:
                child_logger.info(clean)
    except Exception:
        pass
    finally:
        try:
            pipe.close()
        except Exception:
            pass


class SuiteGatewayHandler(SimpleHTTPRequestHandler):
    """Manejador HTTP que actúa como servidor estático y Reverse Proxy hacia los backends Django."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def log_message(self, format, *args):
        """Silencia el formato por defecto de http.server y lo canaliza a sznLogger."""
        msg = format % args
        logger_shell.info(msg)

    def do_GET(self):
        self._route_request()

    def do_POST(self):
        self._route_request()

    def do_HEAD(self):
        self._route_request()

    def do_PUT(self):
        self._route_request()

    def do_DELETE(self):
        self._route_request()

    def do_OPTIONS(self):
        self._route_request()

    def _route_request(self):
        path = self.path

        # Normalizar raíz al portal
        if path in ("", "/"):
            self.path = "/index.html"
            path = "/index.html"

        # 1. Rutas de Mapa de Calor
        if path == "/mapa-calor" or path == "/apps/mapa-calor":
            self.send_response(301)
            self.send_header("Location", "/mapa-calor/")
            self.end_headers()
            return

        if path.startswith("/apps/mapa-calor/"):
            new_path = path.replace("/apps/mapa-calor", "/mapa-calor", 1)
            self.send_response(302)
            self.send_header("Location", new_path)
            self.end_headers()
            return

        if path.startswith("/mapa-calor/"):
            if path.startswith("/mapa-calor/static/") or path.startswith("/mapa-calor/media/"):
                backend_path = path
            else:
                backend_path = path[len("/mapa-calor"):]
                if not backend_path.startswith("/"):
                    backend_path = "/" + backend_path
            self._proxy_to(backend_path, "127.0.0.1", MAPA_PORT, logger_mapa)
            return

        # 2. Rutas de Estrés de Malla
        if path == "/estres-malla" or path == "/apps/estres-malla":
            self.send_response(301)
            self.send_header("Location", "/estres-malla/")
            self.end_headers()
            return

        if path.startswith("/apps/estres-malla/"):
            new_path = path.replace("/apps/estres-malla", "/estres-malla", 1)
            self.send_response(302)
            self.send_header("Location", new_path)
            self.end_headers()
            return

        if path.startswith("/estres-malla/"):
            if path.startswith("/estres-malla/static/") or path.startswith("/estres-malla/media/"):
                backend_path = path
            else:
                backend_path = path[len("/estres-malla"):]
                if not backend_path.startswith("/"):
                    backend_path = "/" + backend_path
            self._proxy_to(backend_path, "127.0.0.1", ESTRES_PORT, logger_estres)
            return

        # 3. Fallback inteligente por Referer para recursos huérfanos (/static/ o /media/)
        referer = self.headers.get("Referer", "")
        clean_path = path.lstrip("/").split("?")[0]
        file_candidate = os.path.join(STATIC_DIR, clean_path.replace("/", os.sep))

        if not os.path.exists(file_candidate):
            if "/mapa-calor/" in referer and (path.startswith("/static/") or path.startswith("/media/")):
                self._proxy_to(f"/mapa-calor{path}", "127.0.0.1", MAPA_PORT, logger_mapa)
                return
            if "/estres-malla/" in referer and (path.startswith("/static/") or path.startswith("/media/")):
                self._proxy_to(f"/estres-malla{path}", "127.0.0.1", ESTRES_PORT, logger_estres)
                return

        # 4. Servir archivo estático de Suite UNAB
        if self.command == "GET":
            super().do_GET()
        elif self.command == "HEAD":
            super().do_HEAD()
        else:
            self.send_error(405, "Method Not Allowed")

    def _proxy_to(self, target_path, backend_host, backend_port, target_logger):
        conn = http.client.HTTPConnection(backend_host, backend_port, timeout=60)

        # Leer cuerpo si existe (POST / PUT)
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else None

        # Clonar y filtrar cabeceras de salto
        headers = {}
        for key, val in self.headers.items():
            if key.lower() in ("connection", "keep-alive", "transfer-encoding", "upgrade"):
                continue
            headers[key] = val

        # Añadir metadatos de proxy inverso
        headers["Host"] = f"localhost:{GATEWAY_PORT}"
        headers["X-Forwarded-Host"] = f"localhost:{GATEWAY_PORT}"
        headers["X-Forwarded-Port"] = str(GATEWAY_PORT)
        headers["X-Forwarded-Proto"] = "http"
        client_ip = self.client_address[0]
        if "X-Forwarded-For" in headers:
            headers["X-Forwarded-For"] = f"{headers['X-Forwarded-For']}, {client_ip}"
        else:
            headers["X-Forwarded-For"] = client_ip

        try:
            conn.request(self.command, target_path, body=body, headers=headers)
            res = conn.getresponse()
        except Exception as e:
            target_logger.error(f"Error conectando con backend {backend_host}:{backend_port}: {e}")
            self.send_error(502, f"Bad Gateway: backend no disponible ({e})")
            return

        # Enviar status code
        self.send_response(res.status, res.reason)

        # Reescribir y enviar cabeceras
        for key, val in res.getheaders():
            k_lower = key.lower()
            if k_lower in ("connection", "transfer-encoding", "date", "server"):
                continue
            if k_lower == "location":
                # Reescribir redirecciones para que apunten al puerto unificado 8791
                val = val.replace(f"http://{backend_host}:{backend_port}", f"http://localhost:{GATEWAY_PORT}")
                val = val.replace(f"http://localhost:{backend_port}", f"http://localhost:{GATEWAY_PORT}")
                val = val.replace(f"http://127.0.0.1:{backend_port}", f"http://localhost:{GATEWAY_PORT}")
                if backend_port == MAPA_PORT and val.startswith("/") and not val.startswith("/mapa-calor"):
                    val = f"/mapa-calor{val}"
                elif backend_port == ESTRES_PORT and val.startswith("/") and not val.startswith("/estres-malla"):
                    val = f"/estres-malla{val}"
            self.send_header(key, val)
        self.end_headers()

        # Transmitir cuerpo de la respuesta en chunks
        try:
            while chunk := res.read(64 * 1024):
                self.wfile.write(chunk)
            self.wfile.flush()
        except (ConnectionResetError, BrokenPipeError):
            pass
        finally:
            conn.close()

        target_logger.info(f'"{self.command} {self.path}" -> {res.status} {res.reason}')


class ThreadingGatewayServer(socketserver.ThreadingMixIn, HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def print_banner():
    banner = f"""
\033[36m========================================================================\033[0m
\033[32;1m   🚀 SUITE UNAB - MOTOR UNIFICADO DE SERVICIOS (Puerto {GATEWAY_PORT})\033[0m
\033[36m========================================================================\033[0m
   🌐 \033[1mPortal Principal:\033[0m  http://localhost:{GATEWAY_PORT}/index.html
   🔥 \033[1mMapa de Calor:\033[0m     http://localhost:{GATEWAY_PORT}/mapa-calor/
   📈 \033[1mEstrés de Malla:\033[0m   http://localhost:{GATEWAY_PORT}/estres-malla/
   📁 \033[1mLogs en disco:\033[0m     logs/suite_unab.log
   ⌨️  \033[33mPresiona Ctrl+C en esta ventana para apagar todos los servicios\033[0m
\033[36m========================================================================\033[0m
"""
    print(banner)


def open_browser():
    time.sleep(2.0)
    url = f"http://localhost:{GATEWAY_PORT}/index.html"
    logger_runner.info(f"Abriendo navegador automáticamente en {url} ...")
    webbrowser.open(url)


def main():
    logger_runner.info("Iniciando orquestador Suite UNAB...")

    # 1. Asegurar que los puertos estén libres
    clean_stale_ports([GATEWAY_PORT, MAPA_PORT, ESTRES_PORT])

    # 2. Levantar Django: Mapa de Calor (8792)
    logger_runner.info(f"Levantando backend Mapa de Calor en 127.0.0.1:{MAPA_PORT}...")
    env_mapa = os.environ.copy()
    env_mapa["FORCE_SCRIPT_NAME"] = "/mapa-calor"
    env_mapa["DEBUG"] = "True"
    env_mapa["PYTHONUNBUFFERED"] = "1"
    proc_mapa = subprocess.Popen(
        [sys.executable, "manage.py", "runserver", f"127.0.0.1:{MAPA_PORT}", "--noreload"],
        cwd=MAPA_DIR,
        env=env_mapa,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )
    t_mapa = threading.Thread(target=stream_reader, args=(proc_mapa.stdout, logger_mapa), daemon=True)
    t_mapa.start()

    # 3. Levantar Django: Estrés de Malla (8793)
    logger_runner.info(f"Levantando backend Estrés de Malla en 127.0.0.1:{ESTRES_PORT}...")
    env_estres = os.environ.copy()
    env_estres["FORCE_SCRIPT_NAME"] = "/estres-malla"
    env_estres["PYTHONUNBUFFERED"] = "1"
    proc_estres = subprocess.Popen(
        [sys.executable, "manage.py", "runserver", f"127.0.0.1:{ESTRES_PORT}", "--noreload"],
        cwd=ESTRES_DIR,
        env=env_estres,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )
    t_estres = threading.Thread(target=stream_reader, args=(proc_estres.stdout, logger_estres), daemon=True)
    t_estres.start()

    # 4. Iniciar Gateway HTTP Server (8791)
    logger_runner.info(f"Iniciando Gateway inverso en 0.0.0.0:{GATEWAY_PORT}...")
    httpd = ThreadingGatewayServer(("0.0.0.0", GATEWAY_PORT), SuiteGatewayHandler)

    # 5. Programar apertura del navegador
    t_browser = threading.Thread(target=open_browser, daemon=True)
    t_browser.start()

    # Mostrar Banner
    print_banner()

    # Manejador de apagado limpio
    shutdown_done = False

    def shutdown(signum=None, frame=None):
        nonlocal shutdown_done
        if shutdown_done:
            return
        shutdown_done = True
        print("\n")
        logger_runner.warning("Deteniendo Suite UNAB y apagando todos los servicios...")

        # Detener servidor web
        threading.Thread(target=httpd.shutdown, daemon=True).start()

        # Detener procesos Django
        kill_proc_tree(proc_mapa)
        kill_proc_tree(proc_estres)

        clean_stale_ports([GATEWAY_PORT, MAPA_PORT, ESTRES_PORT])
        logger_runner.info("Todos los servicios fueron detenidos exitosamente. ¡Hasta luego!")
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    try:
        httpd.serve_forever()
    except (KeyboardInterrupt, SystemExit):
        shutdown()


if __name__ == "__main__":
    main()
