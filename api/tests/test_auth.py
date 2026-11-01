import os

import pytest

# conftest.py ya fijó API_KEY antes de que se recojan los tests.
TEST_API_KEY = os.environ["API_KEY"]

# Endpoints protegidos: (método, ruta, cuerpo)
PROTECTED = [
    ("GET", "/orders/1", None),
    ("POST", "/returns/eligibility", {"order_id": 1, "postal_code": "28001"}),
    ("POST", "/returns", {"order_id": 1, "postal_code": "28001", "resolution": "refund"}),
]


def call(client, method, path, body, headers=None):
    return client.request(method, path, json=body, headers=headers)


@pytest.mark.parametrize("method, path, body", PROTECTED)
def test_with_correct_key_is_allowed(client, method, path, body):
    assert call(client, method, path, body).status_code == 200


@pytest.mark.parametrize("method, path, body", PROTECTED)
def test_without_key_is_401(anon_client, method, path, body):
    r = call(anon_client, method, path, body)
    assert r.status_code == 401
    assert r.json() == {"detail": "API key inválida o ausente"}


@pytest.mark.parametrize("method, path, body", PROTECTED)
# Último caso: bytes no ASCII (httpx no deja enviarlos como str). No debe romper la API.
@pytest.mark.parametrize(
    "wrong", ["clave-incorrecta", "", TEST_API_KEY + "x", "ñandú".encode()], ids=["distinta", "vacia", "prefijo", "no-ascii"]
)
def test_with_wrong_key_is_401(anon_client, method, path, body, wrong):
    r = call(anon_client, method, path, body, headers={"X-API-Key": wrong})
    assert r.status_code == 401
    assert r.json() == {"detail": "API key inválida o ausente"}


def test_unauthorized_post_returns_does_not_insert(anon_client, db):
    before = db.execute("SELECT count(*) FROM returns").fetchone()[0]
    r = anon_client.post(
        "/returns", json={"order_id": 1, "postal_code": "28001", "resolution": "refund"}
    )
    assert r.status_code == 401
    assert db.execute("SELECT count(*) FROM returns").fetchone()[0] == before


def test_health_is_open(anon_client):
    r = anon_client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_docs_are_open_and_offer_authorize_button(anon_client):
    assert anon_client.get("/docs").status_code == 200
    schema = anon_client.get("/openapi.json").json()
    scheme = schema["components"]["securitySchemes"]["APIKeyHeader"]
    assert scheme == {"type": "apiKey", "in": "header", "name": "X-API-Key"}
    # /health no declara seguridad; el resto sí.
    assert "security" not in schema["paths"]["/health"]["get"]
    assert schema["paths"]["/returns"]["post"]["security"] == [{"APIKeyHeader": []}]
