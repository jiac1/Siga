"""
tests/test_estres_malla.py
Pruebas unitarias y de integración para la app Django Estrés de Malla (MallaIQ).
Valida modelos ORM, autenticación, procesamiento de Excel de mallas y actas con el motor engine.py.
"""

import os
import sys
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ESTRES_DIR = os.path.join(BASE_DIR, "suite-unab", "apps", "estres-malla")
if ESTRES_DIR not in sys.path:
    sys.path.insert(0, ESTRES_DIR)

# Inicializar Django con la configuración de Estrés de Malla
os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"
os.environ["DEBUG"] = "True"
os.environ["FORCE_SCRIPT_NAME"] = "/estres-malla"

import django
django.setup()

from django.test import TestCase, Client, override_settings
from accounts.models import Organization, User
from malla.models import Carrera, Asignatura
from malla import engine


@override_settings(ALLOWED_HOSTS=["localhost", "127.0.0.1", "testserver"])
class TestEstresMalla(TestCase):

    def setUp(self):
        self.client = Client()
        self.ejemplos_dir = os.path.join(ESTRES_DIR, "ejemplos")
        self.malla_excel = os.path.join(self.ejemplos_dir, "malla.xlsx")
        self.actas_excel = os.path.join(self.ejemplos_dir, "actas.xlsx")

        # Crear organización y usuario de prueba
        self.org = Organization.objects.create(
            nombre="Universidad Andrés Bello Test",
            slug="unab-test",
            activa=True
        )
        self.user = User.objects.create_user(
            username="docente_test",
            password="password_seguro_123",
            organization=self.org,
            rol=User.Rol.DOCENTE
        )

    def test_unauthenticated_user_redirected_to_login(self):
        """Un usuario anónimo debe ser redirigido a la pantalla de login."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 302)
        self.assertIn("/accounts/login/", res.url)

    def test_login_page_renders_cleanly(self):
        """GET a login debe responder 200 y contener el formulario de acceso."""
        res = self.client.get("/accounts/login/")
        self.assertEqual(res.status_code, 200)
        content = res.content.decode("utf-8")
        self.assertIn("MallaIQ", content)
        self.assertIn("Ingresar", content)
        self.assertIn("name=\"username\"", content)
        self.assertIn("name=\"password\"", content)

    def test_login_with_invalid_credentials(self):
        """POST con credenciales incorrectas debe re-renderizar el formulario con error."""
        res = self.client.post("/accounts/login/", {
            "username": "docente_test",
            "password": "password_incorrecta"
        })
        self.assertEqual(res.status_code, 200)
        content = res.content.decode("utf-8")
        self.assertTrue("incorrectos" in content or "inválidas" in content)

    def test_login_with_valid_credentials(self):
        """POST con credenciales válidas debe autenticar y redirigir al dashboard."""
        res = self.client.post("/accounts/login/", {
            "username": "docente_test",
            "password": "password_seguro_123"
        })
        self.assertEqual(res.status_code, 302)

    def test_models_orm_carrera_and_asignaturas(self):
        """Verifica la persistencia y relaciones entre Organization, Carrera y Asignatura."""
        carrera = Carrera.objects.create(
            organization=self.org,
            codigo="INF-TEST-01",
            nombre="Ingeniería Civil Informática Test",
            campus="Santiago",
            n_semestres=10
        )
        asig = Asignatura.objects.create(
            carrera=carrera,
            codigo="INF101",
            nombre="Introducción a la Programación",
            semestre=1,
            creditos=5,
            prerrequisitos="—"
        )
        self.assertEqual(str(carrera), f"Ingeniería Civil Informática Test (INF-TEST-01) — {self.org}")
        self.assertEqual(str(asig), "INF101 — Introducción a la Programación (S1)")
        self.assertEqual(carrera.asignaturas.count(), 1)

    def test_engine_leer_malla_real_file(self):
        """El motor debe parsear correctamente el archivo malla.xlsx real de ejemplo."""
        self.assertTrue(os.path.exists(self.malla_excel), "malla.xlsx no existe")
        df_malla = engine.leer_malla(self.malla_excel)
        self.assertGreaterEqual(len(df_malla), 10, "La malla debe tener al menos 10 asignaturas de prueba")
        for col in ["semestre", "codigo", "nombre", "creditos", "prerrequisitos"]:
            self.assertIn(col, df_malla.columns, f"Falta columna {col} en DataFrame de malla")

    def test_engine_leer_actas_real_file(self):
        """El motor debe parsear correctamente el archivo actas.xlsx real de ejemplo."""
        self.assertTrue(os.path.exists(self.actas_excel), "actas.xlsx no existe")
        df_actas = engine.leer_actas(self.actas_excel)
        self.assertGreaterEqual(len(df_actas), 4, "El acta debe contener asignaturas con historial")
        self.assertIn("codigo", df_actas.columns)
        self.assertIn("pct_aprob", df_actas.columns)

    def test_engine_procesar_and_generar_html(self):
        """El motor debe cruzar malla y actas, calcular métricas y generar HTML completo."""
        res_calc = engine.procesar(path_actas=self.actas_excel, path_malla=self.malla_excel)
        self.assertGreaterEqual(res_calc["n_asignaturas"], 10)
        self.assertGreater(res_calc["n_con_datos"], 0)
        self.assertIn("js_data", res_calc)

        # Simular objeto carrera para generar HTML
        carrera_dummy = Carrera(
            organization=self.org,
            codigo="INF-DUMMY",
            nombre="Ingeniería Civil Informática",
            umbral_verde=85,
            umbral_amarillo=70,
            umbral_naranjo=55
        )
        html_salida = engine.generar_html(res_calc, carrera_dummy, periodo="202510")
        self.assertIn("<!DOCTYPE html>", html_salida)
        self.assertIn("Estrés de Malla", html_salida)
        self.assertIn(carrera_dummy.nombre, html_salida)


if __name__ == "__main__":
    unittest.main()
