"""
sznLogger - Motor de Logging Unificado para Suite UNAB
Adaptado de Toodles para soportar logging coloreado en consola,
rotación de archivos y compatibilidad segura con streams UTF-8 en Windows.
"""

import logging
from logging.handlers import RotatingFileHandler
import os
import re
import sys
import time

# Directorio de logs
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGS_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOGS_DIR, exist_ok=True)
LOG_FILE_PATH = os.path.join(LOGS_DIR, "suite_unab.log")

# Inicialización segura del archivo de logs
try:
    if not os.path.exists(LOG_FILE_PATH):
        with open(LOG_FILE_PATH, "a", encoding="utf-8") as f:
            f.write(f"--- SUITE UNAB LOG INICIADO [{time.strftime('%Y-%m-%d %H:%M:%S')}] ---\n")
except Exception as e:
    sys.__stderr__.write(f"No se pudo inicializar el archivo de logs en disco: {e}\n")

# Asegurar codificación UTF-8 en streams estándar de Windows (previene UnicodeEncodeError)
for _stream in (sys.stdout, sys.stderr, sys.__stdout__, sys.__stderr__):
    if _stream and hasattr(_stream, 'reconfigure'):
        try:
            _stream.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            pass

# Regex compilados para rendimiento
_ANSI_RE = re.compile(r'\x1b\[[0-9;]*m')
_TIMESTAMP_RE = re.compile(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}')


class DualStreamWriter:
    """Duplica cualquier print() o excepción a consola y a logs/suite_unab.log con timestamp."""

    def __init__(self, original_stream, log_file_path):
        self.original_stream = original_stream
        self.log_file_path = log_file_path
        self._file = None
        self._at_line_start = True

    def _get_file(self):
        if self._file is None or self._file.closed:
            self._file = open(self.log_file_path, "a", encoding="utf-8", buffering=1)
        return self._file

    def write(self, message):
        if not message:
            return
        try:
            self.original_stream.write(message)
        except Exception:
            pass

        try:
            f = self._get_file()
            clean = _ANSI_RE.sub('', message)

            if _TIMESTAMP_RE.match(clean):
                f.write(clean)
                self._at_line_start = clean.endswith('\n')
                return

            output = []
            for ch in clean:
                if ch == '\n':
                    output.append('\n')
                    self._at_line_start = True
                else:
                    if self._at_line_start:
                        output.append(f"{time.strftime('%Y-%m-%d %H:%M:%S')} | ")
                        self._at_line_start = False
                    output.append(ch)

            f.write(''.join(output))
        except Exception:
            pass

    def flush(self):
        try:
            self.original_stream.flush()
        except Exception:
            pass
        try:
            if self._file and not self._file.closed:
                self._file.flush()
        except Exception:
            pass

    def fileno(self):
        return self.original_stream.fileno()

    @property
    def encoding(self):
        return getattr(self.original_stream, 'encoding', 'utf-8')


def enable_stdout_redirection():
    """Activa la duplicación de sys.stdout y sys.stderr hacia logs/suite_unab.log."""
    if not isinstance(sys.stdout, DualStreamWriter):
        sys.stdout = DualStreamWriter(sys.__stdout__, LOG_FILE_PATH)
    if not isinstance(sys.stderr, DualStreamWriter):
        sys.stderr = DualStreamWriter(sys.__stderr__, LOG_FILE_PATH)


# Formatos de texto
CONSOLE_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)-14s | %(message)s"
FILE_FORMAT    = "%(asctime)s [%(levelname)s] %(name)s (%(filename)s:%(lineno)d): %(message)s"
DATE_FORMAT    = "%Y-%m-%d %H:%M:%S"


class ColoredFormatter(logging.Formatter):
    """Formateador con códigos de color ANSI para la consola de Suite UNAB."""
    COLORS = {
        logging.DEBUG:    "\033[36m",             # Cyan
        logging.INFO:     "\033[32m",             # Verde
        logging.WARNING:  "\033[33m",             # Amarillo
        logging.ERROR:    "\033[31m",             # Rojo
        logging.CRITICAL: "\033[41m\033[37m",     # Rojo fondo / Texto blanco
    }
    RESET = "\033[0m"

    def format(self, record):
        color = self.COLORS.get(record.levelno, self.RESET)
        levelname_original = record.levelname
        record.levelname = f"{color}{levelname_original}{self.RESET}"
        formatted = super().format(record)
        record.levelname = levelname_original
        return formatted


class SafeStreamWrapper:
    """Wrapper para evitar UnicodeEncodeError en consolas Windows (cp1252/cp850)."""
    def __init__(self, stream):
        self.stream = stream

    def write(self, data):
        if not data:
            return
        try:
            self.stream.write(data)
        except UnicodeEncodeError:
            target_enc = getattr(self.stream, 'encoding', None) or 'utf-8'
            safe_str = data.encode(target_enc, errors='replace').decode(target_enc, errors='replace')
            try:
                self.stream.write(safe_str)
            except Exception:
                pass
        except Exception:
            pass

    def flush(self):
        try:
            self.stream.flush()
        except Exception:
            pass


def setup_logger(name: str = "suite", log_level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    if logger.handlers:
        return logger

    # 1. Console Handler con colores y stream seguro
    console_handler = logging.StreamHandler(SafeStreamWrapper(sys.__stdout__))
    console_handler.setFormatter(ColoredFormatter(CONSOLE_FORMAT, datefmt=DATE_FORMAT))
    logger.addHandler(console_handler)

    # 2. File Handler rotativo (5 MB, 3 backups)
    file_handler = RotatingFileHandler(
        LOG_FILE_PATH, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(logging.Formatter(FILE_FORMAT, datefmt=DATE_FORMAT))
    logger.addHandler(file_handler)

    return logger


# Activar redirección automática
enable_stdout_redirection()

# Logger raíz de Suite UNAB
root_logger = setup_logger("suite")


def get_logger(submodule: str) -> logging.Logger:
    """Retorna un logger hijo para un subsistema específico (ej: get_logger('mapa'))."""
    return logging.getLogger(f"suite.{submodule}")
