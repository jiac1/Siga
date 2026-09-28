"""
tests/test_runner_gateway.py
Pruebas de integración del Gateway HTTP y Reverse Proxy de run_suite.py.
Valida el enrutamiento estático, redirecciones, proxy inverso y reescritura de cabeceras.
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import os
import socket
import sys
import threading
import time
import unittest
import urllib.request
import urllib.error

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import run_suite


def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


class MockDjangoBackendHandler(BaseHTTPRequestHandler):
    """Servidor mock para simular las respuestas de Django detrás del proxy."""

    def log_message(self, format, *args):
        pass

    def do_GET(self):
        if self.path == "/mock-redirect":
            self.send_response(302)
            self.send_header("Location", f"http://127.0.0.1:{self.server.server_port}/dashboard/")
            self.end_headers()
            return

        if self.path == "/relative-redirect":
            self.send_response(302)
            self.send_header("Location", "/accounts/login/")
            self.end_headers()
            return

        # Responder con eco de headers y path recibido
        headers_dict = {k: v for k, v in self.headers.items()}
        data = {
            "received_path": self.path,
            "received_headers": headers_dict,
        }
        body = json.dumps(data).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Set-Cookie", "sessionid=test_session_123; Path=/")
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body_received = self.rfile.read(length).decode("utf-8", errors="replace")
        data = {
            "method": "POST",
            "received_path": self.path,
            "received_body": body_received,
        }
        res = json.dumps(data).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(res)))
        self.end_headers()
        self.wfile.write(res)


class TestRunnerGateway(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # 1. Asignar puertos libres para testing
        cls.gateway_port = find_free_port()
        cls.mock_backend_port = find_free_port()

        # Configurar run_suite para apuntar al mock backend en mapa_calor
        run_suite.GATEWAY_PORT = cls.gateway_port
        run_suite.MAPA_PORT = cls.mock_backend_port

        # 2. Iniciar Mock Backend Django
        cls.mock_server = HTTPServer(("127.0.0.1", cls.mock_backend_port), MockDjangoBackendHandler)
        cls.mock_thread = threading.Thread(target=cls.mock_server.serve_forever, daemon=True)
        cls.mock_thread.start()

        # 3. Iniciar Gateway
        cls.gateway_server = run_suite.ThreadingGatewayServer(
            ("127.0.0.1", cls.gateway_port), run_suite.SuiteGatewayHandler
        )
        cls.gateway_thread = threading.Thread(target=cls.gateway_server.serve_forever, daemon=True)
        cls.gateway_thread.start()
        time.sleep(0.3)

    @classmethod
    def tearDownClass(cls):
        cls.gateway_server.shutdown()
        cls.mock_server.shutdown()

    def url(self, path):
        return f"http://127.0.0.1:{self.gateway_port}{path}"

    def test_static_root_serves_index_html(self):
        """GET / debe servir suite-unab/index.html con status 200 y HTML válido."""
        req = urllib.request.Request(self.url("/"))
        with urllib.request.urlopen(req, timeout=3) as res:
            self.assertEqual(res.status, 200)
            content = res.read().decode("utf-8", errors="replace")
            self.assertIn("<title>Suite UNAB</title>", content)

    def test_static_shared_tokens_css(self):
        """GET /shared/tokens.css debe servir el CSS compartido."""
        req = urllib.request.Request(self.url("/shared/tokens.css"))
        with urllib.request.urlopen(req, timeout=3) as res:
            self.assertEqual(res.status, 200)
            content = res.read().decode("utf-8", errors="replace")
            self.assertIn("--su-navy", content)

    def test_static_app_malla_html(self):
        """GET /apps/malla/index.html debe servir el portal de mallas."""
        req = urllib.request.Request(self.url("/apps/malla/index.html"))
        with urllib.request.urlopen(req, timeout=3) as res:
            self.assertEqual(res.status, 200)
            content = res.read().decode("utf-8", errors="replace")
            self.assertIn("Mallas interactivas", content)

    def test_redirect_mapa_calor_trailing_slash(self):
        """GET /mapa-calor sin barra final debe redireccionar 301 a /mapa-calor/."""
        class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
            def http_error_301(self, req, fp, code, msg, headers):
                return fp
        opener = urllib.request.build_opener(NoRedirectHandler)
        res = opener.open(self.url("/mapa-calor"))
        self.assertEqual(res.status, 301)
        self.assertEqual(res.headers.get("Location"), "/mapa-calor/")

    def test_redirect_apps_mapa_calor(self):
        """GET /apps/mapa-calor/ debe redireccionar 302 a /mapa-calor/."""
        class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
            def http_error_302(self, req, fp, code, msg, headers):
                return fp
        opener = urllib.request.build_opener(NoRedirectHandler)
        res = opener.open(self.url("/apps/mapa-calor/"))
        self.assertEqual(res.status, 302)
        self.assertEqual(res.headers.get("Location"), "/mapa-calor/")

    def test_proxy_strips_prefix_for_views(self):
        """El proxy debe despojar el prefijo /mapa-calor para las vistas backend."""
        req = urllib.request.Request(self.url("/mapa-calor/procesar/"))
        with urllib.request.urlopen(req, timeout=3) as res:
            self.assertEqual(res.status, 200)
            data = json.loads(res.read().decode("utf-8"))
            self.assertEqual(data["received_path"], "/procesar/")

    def test_proxy_preserves_prefix_for_static(self):
        """El proxy debe preservar /mapa-calor/static/ para que StaticFilesHandler lo capture."""
        req = urllib.request.Request(self.url("/mapa-calor/static/test.css"))
        with urllib.request.urlopen(req, timeout=3) as res:
            self.assertEqual(res.status, 200)
            data = json.loads(res.read().decode("utf-8"))
            self.assertEqual(data["received_path"], "/mapa-calor/static/test.css")

    def test_proxy_forwarded_headers(self):
        """El proxy debe inyectar cabeceras X-Forwarded-Host, Port, Proto y Host unificado."""
        req = urllib.request.Request(self.url("/mapa-calor/inspect-headers/"))
        with urllib.request.urlopen(req, timeout=3) as res:
            data = json.loads(res.read().decode("utf-8"))
            headers = data["received_headers"]
            self.assertEqual(headers.get("Host"), f"localhost:{self.gateway_port}")
            self.assertEqual(headers.get("X-Forwarded-Host"), f"localhost:{self.gateway_port}")
            self.assertEqual(headers.get("X-Forwarded-Port"), str(self.gateway_port))
            self.assertEqual(headers.get("X-Forwarded-Proto"), "http")

    def test_proxy_post_request_body_transmission(self):
        """El proxy debe transmitir correctamente el payload POST hacia el backend."""
        payload = json.dumps({"clave": "valor_de_prueba"}).encode("utf-8")
        req = urllib.request.Request(
            self.url("/mapa-calor/api/datos/"),
            data=payload,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=3) as res:
            self.assertEqual(res.status, 200)
            data = json.loads(res.read().decode("utf-8"))
            self.assertEqual(data["method"], "POST")
            self.assertIn("valor_de_prueba", data["received_body"])

    def test_proxy_location_header_rewriting(self):
        """Las redirecciones del backend deben reescribirse hacia el puerto del gateway."""
        class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
            def http_error_302(self, req, fp, code, msg, headers):
                return fp
        opener = urllib.request.build_opener(NoRedirectHandler)

        # Caso 1: Redirección absoluta del backend
        res1 = opener.open(self.url("/mapa-calor/mock-redirect"))
        loc1 = res1.headers.get("Location")
        self.assertIn(f"http://localhost:{self.gateway_port}", loc1)
        self.assertNotIn(str(self.mock_backend_port), loc1)

        # Caso 2: Redirección relativa sin prefijo
        res2 = opener.open(self.url("/mapa-calor/relative-redirect"))
        loc2 = res2.headers.get("Location")
        self.assertTrue(loc2.startswith("/mapa-calor/accounts/login/"))

    def test_static_file_404_not_found(self):
        """Un archivo estático inexistente debe responder 404 limpiamente."""
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(self.url("/archivo_inexistente_9999.xyz"))
        self.assertEqual(ctx.exception.code, 404)

    def test_method_not_allowed_on_static(self):
        """Una petición POST a un archivo estático debe responder 405 Method Not Allowed."""
        req = urllib.request.Request(self.url("/index.html"), data=b"post_invalido")
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(req)
        self.assertEqual(ctx.exception.code, 405)


if __name__ == "__main__":
    unittest.main()
