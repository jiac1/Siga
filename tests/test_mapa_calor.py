"""
tests/test_mapa_calor.py
Pruebas unitarias y de integración para la app Django Mapa de Calor.
Valida renderizado de vistas, carga y procesamiento del Excel de salas, y descarga del reporte.
"""

import base64
import os
import sys
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAPA_DIR = os.path.join(BASE_DIR, "suite-unab", "apps", "mapa-calor")
if MAPA_DIR not in sys.path:
    sys.path.insert(0, MAPA_DIR)

# Inicializar Django con la configuración de Mapa de Calor
os.environ["DJANGO_SETTINGS_MODULE"] = "heatmap_project.settings"
os.environ["DEBUG"] = "True"
os.environ["FORCE_SCRIPT_NAME"] = "/mapa-calor"

import django
django.setup()

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory
from heatmap import views


class TestMapaCalor(unittest.TestCase):

    def setUp(self):
        self.rf = RequestFactory()
        self.ejemplos_dir = os.path.join(MAPA_DIR, "ejemplos")
        self.excel_prueba = os.path.join(self.ejemplos_dir, "mapa_calor_prueba.xlsx")

    def test_home_view(self):
        """GET / debe renderizar la página de inicio de Mapa de Calor con status 200."""
        req = self.rf.get("/")
        res = views.home(req)
        self.assertEqual(res.status_code, 200)
        content = res.content.decode("utf-8")
        self.assertIn("Mapa de Calor", content)
        self.assertIn("Arrastra tu archivo aquí", content)

    def test_procesar_get_method_not_allowed(self):
        """GET /procesar/ debe responder 405 Method Not Allowed."""
        req = self.rf.get("/procesar/")
        res = views.procesar(req)
        self.assertEqual(res.status_code, 405)

    def test_procesar_without_file(self):
        """POST /procesar/ sin archivo debe mostrar mensaje de error amigable."""
        req = self.rf.post("/procesar/")
        req.session = {}
        res = views.procesar(req)
        self.assertEqual(res.status_code, 200)
        self.assertIn("No se recibió ningún archivo", res.content.decode("utf-8"))

    def test_procesar_invalid_extension(self):
        """POST /procesar/ con archivo no .xlsx debe ser rechazado."""
        archivo_invalido = SimpleUploadedFile("prueba.txt", b"contenido no valido", content_type="text/plain")
        req = self.rf.post("/procesar/", {"archivo": archivo_invalido})
        req.session = {}
        res = views.procesar(req)
        self.assertEqual(res.status_code, 200)
        self.assertIn("Solo se aceptan archivos .xlsx", res.content.decode("utf-8"))

    def test_procesar_real_excel_example(self):
        """POST /procesar/ con el archivo de ejemplo real debe generar el mapa de calor exitosamente."""
        self.assertTrue(os.path.exists(self.excel_prueba), "El archivo de ejemplo no existe")
        with open(self.excel_prueba, "rb") as f:
            archivo_excel = SimpleUploadedFile(
                "mapa_calor_prueba.xlsx", f.read(),
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        req = self.rf.post("/procesar/", {"archivo": archivo_excel})
        req.session = {}
        res = views.procesar(req)

        self.assertEqual(res.status_code, 200)
        content = res.content.decode("utf-8")
        self.assertIn("Resultados del Heatmap", content)
        self.assertIn("Salas únicas", content)
        self.assertIn("excel_data", req.session, "Debe persistir el Excel en base64 en la sesión")

    def test_descargar_excel_sin_sesion(self):
        """GET /descargar/ sin procesar previamente debe responder 404."""
        req = self.rf.get("/descargar/")
        req.session = {}
        res = views.descargar_excel(req)
        self.assertEqual(res.status_code, 404)

    def test_descargar_excel_con_sesion(self):
        """GET /descargar/ con Excel en sesión debe devolver el archivo binario XLSX."""
        fake_xlsx_bytes = b"PK\x03\x04" + b"\x00" * 50  # Simula cabecera ZIP de archivo XLSX
        req = self.rf.get("/descargar/")
        req.session = {
            "excel_data": base64.b64encode(fake_xlsx_bytes).decode("utf-8"),
            "excel_nombre": "reporte_heatmap.xlsx",
        }
        res = views.descargar_excel(req)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(
            res["Content-Type"],
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        self.assertIn("attachment; filename=", res["Content-Disposition"])
        self.assertTrue(res.content.startswith(b"PK\x03\x04"))


if __name__ == "__main__":
    unittest.main()
