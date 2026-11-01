import os
from pathlib import Path

import psycopg
import pytest
from psycopg.conninfo import conninfo_to_dict

# --- Salvaguarda: los tests vacían las tablas (el seed hace TRUNCATE). ---
# Solo se ejecutan contra una base cuyo nombre termina en "_test". Esto va ANTES de
# importar la app y antes de tocar la base, y es lo que impide vaciar una base real.
TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")
if not TEST_DATABASE_URL:
    pytest.exit(
        "Falta TEST_DATABASE_URL. Defínela en .env y ejecuta: uv run --env-file .env pytest",
        returncode=2,
    )
_db_name = conninfo_to_dict(TEST_DATABASE_URL).get("dbname") or ""
if not _db_name.endswith("_test"):
    pytest.exit(
        f"TEST_DATABASE_URL apunta a la base '{_db_name}', que no termina en '_test'. "
        "Abortado para no vaciar una base real.",
        returncode=2,
    )

# La app y el seed usarán la base de test; la API key de los tests no depende del .env.
TEST_API_KEY = "test-key"
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ["API_KEY"] = TEST_API_KEY

from fastapi.testclient import TestClient  # noqa: E402

from app.db import get_connection  # noqa: E402
from app.main import app  # noqa: E402

SEED_SQL = Path(__file__).resolve().parents[2] / "db" / "seed.sql"


@pytest.fixture(autouse=True)
def reset_db():
    """Recarga el seed antes de cada test: así el orden de los tests no importa."""
    with psycopg.connect(TEST_DATABASE_URL, autocommit=True) as conn:
        conn.execute(SEED_SQL.read_text())
    yield


@pytest.fixture
def client():
    """Cliente que envía la API key correcta en todas las peticiones."""
    return TestClient(app, headers={"X-API-Key": TEST_API_KEY})


@pytest.fixture
def anon_client():
    """Cliente sin API key."""
    return TestClient(app)


@pytest.fixture
def db():
    """Conexión para comprobar directamente qué hay en la base."""
    with get_connection() as conn:
        yield conn
