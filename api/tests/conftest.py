import os
from pathlib import Path

# Forzamos la base de test ANTES de importar la app. Es asignación directa (no setdefault)
# para que un DB_NAME=venison del entorno nunca haga que los tests vacíen la base real.
os.environ["DB_NAME"] = "venison_test"

import psycopg
import pytest
from fastapi.testclient import TestClient

from app.db import get_connection
from app.main import app

SEED_SQL = Path(__file__).resolve().parents[2] / "db" / "seed.sql"


@pytest.fixture(autouse=True)
def reset_db():
    """Recarga el seed antes de cada test: así el orden de los tests no importa."""
    with psycopg.connect(host="localhost", dbname="venison_test", user="alexroca", autocommit=True) as conn:
        conn.execute(SEED_SQL.read_text())
    yield


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def db():
    """Conexión para comprobar directamente qué hay en la base."""
    with get_connection() as conn:
        yield conn
