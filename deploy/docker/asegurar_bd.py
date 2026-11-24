"""Crea la base de datos del servicio si no existe (PostgreSQL / Amazon RDS).

Cada servicio con estado usa su propia base dentro de la misma instancia RDS
(core, estres_malla): sus tablas de Django (auth, admin, sessions) colisionarían
si compartieran base. Se ejecuta en la tarea "migrar" antes de las migraciones.
"""
import os
import sys
from urllib.parse import urlparse

url = os.environ.get("DATABASE_URL", "")
if not url.startswith(("postgres://", "postgresql://")):
    sys.exit(0)  # SQLite u otro motor: nada que hacer

import psycopg  # noqa: E402
from psycopg import errors, sql  # noqa: E402

partes = urlparse(url)
nombre = partes.path.lstrip("/")
admin = partes._replace(path="/postgres").geturl()
with psycopg.connect(admin, autocommit=True) as con:
    try:
        con.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(nombre)))
        print(f"Base de datos creada: {nombre}")
    except errors.DuplicateDatabase:
        pass
