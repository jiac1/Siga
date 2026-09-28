"""
tests/test_szn_logger.py
Pruebas unitarias para el motor de logging unificado sznLogger.
"""

import io
import logging
import os
import re
import sys
import unittest

# Asegurar importación de sznLogger desde la raíz del proyecto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import sznLogger


class TestSznLogger(unittest.TestCase):

    def setUp(self):
        self.logs_dir = os.path.join(BASE_DIR, "logs")
        self.log_file = os.path.join(self.logs_dir, "suite_unab.log")

    def test_log_file_and_directory_creation(self):
        """Verifica que el directorio logs/ y el archivo suite_unab.log existan."""
        self.assertTrue(os.path.isdir(self.logs_dir), "El directorio logs/ no existe")
        self.assertTrue(os.path.exists(self.log_file), "El archivo suite_unab.log no existe")

    def test_colored_formatter_ansi_codes(self):
        """Verifica que ColoredFormatter aplique códigos ANSI por nivel y restaure colores."""
        formatter = sznLogger.ColoredFormatter("%(levelname)s - %(message)s")

        record_info = logging.LogRecord("test", logging.INFO, "path", 1, "Mensaje informativo", (), None)
        formatted_info = formatter.format(record_info)
        self.assertIn("\033[32m", formatted_info, "INFO debe tener color verde ANSI")
        self.assertIn("\033[0m", formatted_info, "Debe restaurar el color con ANSI RESET")

        record_err = logging.LogRecord("test", logging.ERROR, "path", 1, "Mensaje de error", (), None)
        formatted_err = formatter.format(record_err)
        self.assertIn("\033[31m", formatted_err, "ERROR debe tener color rojo ANSI")

        record_warn = logging.LogRecord("test", logging.WARNING, "path", 1, "Mensaje de advertencia", (), None)
        formatted_warn = formatter.format(record_warn)
        self.assertIn("\033[33m", formatted_warn, "WARNING debe tener color amarillo ANSI")

    def test_safe_stream_wrapper_non_ascii(self):
        """Verifica que SafeStreamWrapper no falle ante caracteres especiales o emojis."""
        class MockRestrictedStream:
            def __init__(self):
                self.encoding = "cp1252"
                self.buffer = []

            def write(self, text):
                # Simula una consola Windows que solo admite cp1252
                try:
                    text.encode("cp1252")
                except UnicodeEncodeError as e:
                    raise e
                self.buffer.append(text)

            def flush(self):
                pass

        mock_stream = MockRestrictedStream()
        safe_wrapper = sznLogger.SafeStreamWrapper(mock_stream)

        # Probar caracteres Unicode exóticos y emojis
        text_with_emojis = "Test: 🚀 UNAB — ¡Aprobado con éxito! ✅"
        # SafeStreamWrapper debe capturar UnicodeEncodeError y reemplazar caracteres incompatibles
        try:
            safe_wrapper.write(text_with_emojis)
        except UnicodeEncodeError:
            self.fail("SafeStreamWrapper lanzó UnicodeEncodeError inesperadamente")

        self.assertTrue(len(mock_stream.buffer) > 0, "No se escribió texto en el stream")

    def test_dual_stream_writer_ansi_stripping(self):
        """Verifica que DualStreamWriter limpie códigos ANSI antes de persistir en disco."""
        stream_capture = io.StringIO()
        dual_writer = sznLogger.DualStreamWriter(stream_capture, self.log_file)

        msg_with_ansi = "\033[32m[INFO]\033[0m Mensaje de prueba limpio en disco\n"
        dual_writer.write(msg_with_ansi)
        dual_writer.flush()

        # En consola debe mantener el ANSI
        self.assertEqual(stream_capture.getvalue(), msg_with_ansi)

        # En el archivo de log debe guardarse sin códigos ANSI
        with open(self.log_file, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        self.assertIn("Mensaje de prueba limpio en disco", content)
        ansi_regex = re.compile(r'\x1b\[[0-9;]*m')
        # La última línea escrita no debe contener secuencias ANSI
        last_matching_lines = [l for l in content.splitlines() if "Mensaje de prueba limpio en disco" in l]
        self.assertTrue(len(last_matching_lines) > 0)
        self.assertFalse(ansi_regex.search(last_matching_lines[-1]), "El log en disco no debe contener secuencias ANSI")

    def test_get_logger_submodules(self):
        """Verifica que get_logger genere subloggers bajo el namespace suite.* con nivel INFO."""
        subsystems = ["runner", "gateway", "shell", "mapa", "estres"]
        for sub in subsystems:
            logger = sznLogger.get_logger(sub)
            self.assertEqual(logger.name, f"suite.{sub}")
            self.assertTrue(logger.isEnabledFor(logging.INFO))


if __name__ == "__main__":
    unittest.main()
