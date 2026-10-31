import pytest

import app.main as main

# Datos del seed (db/seed.sql): (order_id, postal_code)
OK_ORDER = (1, "28001")  # 5 días
NOT_FOUND_ORDER = (999, "28001")  # no existe
WRONG_POSTAL = (1, "08002")  # el pedido 1 es del 28001
RETURNED_ORDER = (8, "28005")  # ya tiene devolución en el seed
OUTLET_ORDER = (4, "41003")
EXPIRED_ORDER = (2, "28001")  # 45 días
LIMIT_ORDER = (11, "28001")  # exactamente 30 días

ELIGIBILITY_CASES = [
    (OK_ORDER, True, "ok"),
    (NOT_FOUND_ORDER, False, "not_found"),
    (WRONG_POSTAL, False, "not_found"),
    (RETURNED_ORDER, False, "already_returned"),
    (OUTLET_ORDER, False, "outlet"),
    (EXPIRED_ORDER, False, "expired"),
    (LIMIT_ORDER, True, "ok"),
]


def count_returns(db) -> int:
    return db.execute("SELECT count(*) FROM returns").fetchone()[0]


# ---------- POST /returns/eligibility ----------

@pytest.mark.parametrize("order, eligible, code", ELIGIBILITY_CASES)
def test_eligibility(client, order, eligible, code):
    r = client.post("/returns/eligibility", json={"order_id": order[0], "postal_code": order[1]})
    assert r.status_code == 200
    body = r.json()
    assert body["eligible"] is eligible
    assert body["code"] == code
    assert body["message"] == main.MESSAGES[code]


def test_eligibility_not_found_messages_are_identical(client):
    """Pedido inexistente y CP incorrecto no deben poder distinguirse."""
    a = client.post("/returns/eligibility", json={"order_id": 999, "postal_code": "28001"}).json()
    b = client.post("/returns/eligibility", json={"order_id": 1, "postal_code": "08002"}).json()
    assert a == b


def test_eligibility_ignores_postal_code_whitespace(client):
    r = client.post("/returns/eligibility", json={"order_id": 1, "postal_code": " 28001 "})
    assert r.json()["code"] == "ok"


def test_eligibility_missing_field_is_422(client):
    r = client.post("/returns/eligibility", json={"order_id": 1})
    assert r.status_code == 422


# ---------- POST /returns ----------

def test_create_return_registers_and_stores_row(client, db):
    r = client.post(
        "/returns",
        json={"order_id": 1, "postal_code": "28001", "resolution": "refund", "reason": "Me queda grande"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["registered"] is True
    assert body["code"] == "registered"
    assert body["message"] == main.MESSAGES["registered"]
    assert body["return_id"] is not None

    row = db.execute(
        "SELECT order_id, reason, status, resolution FROM returns WHERE id = %s", (body["return_id"],)
    ).fetchone()
    assert row == (1, "Me queda grande", "pending", "refund")


def test_create_return_reason_is_optional(client, db):
    r = client.post("/returns", json={"order_id": 11, "postal_code": "28001", "resolution": "exchange"})
    body = r.json()
    assert body["registered"] is True
    row = db.execute("SELECT reason, resolution FROM returns WHERE id = %s", (body["return_id"],)).fetchone()
    assert row == (None, "exchange")


def test_create_return_twice_second_is_already_returned(client, db):
    payload = {"order_id": 1, "postal_code": "28001", "resolution": "refund"}
    first = client.post("/returns", json=payload).json()
    second = client.post("/returns", json=payload).json()
    assert first["registered"] is True
    assert second["registered"] is False
    assert second["code"] == "already_returned"
    assert second["return_id"] is None
    assert db.execute("SELECT count(*) FROM returns WHERE order_id = 1").fetchone()[0] == 1


@pytest.mark.parametrize(
    "order, code",
    [
        (OUTLET_ORDER, "outlet"),
        (EXPIRED_ORDER, "expired"),
        (NOT_FOUND_ORDER, "not_found"),
        (WRONG_POSTAL, "not_found"),
        (RETURNED_ORDER, "already_returned"),
    ],
)
def test_create_return_rejections_do_not_insert(client, db, order, code):
    before = count_returns(db)
    r = client.post(
        "/returns", json={"order_id": order[0], "postal_code": order[1], "resolution": "refund"}
    )
    assert r.status_code == 200
    body = r.json()
    assert body["registered"] is False
    assert body["code"] == code
    assert body["return_id"] is None
    assert count_returns(db) == before


def test_create_return_invalid_resolution_is_422(client, db):
    before = count_returns(db)
    r = client.post("/returns", json={"order_id": 1, "postal_code": "28001", "resolution": "gift"})
    assert r.status_code == 422
    assert count_returns(db) == before


def test_create_return_missing_resolution_is_422(client):
    r = client.post("/returns", json={"order_id": 1, "postal_code": "28001"})
    assert r.status_code == 422


def test_create_return_race_unique_violation_is_already_returned(client, db, monkeypatch):
    """Simula la carrera: la comprobación previa dice 'ok' pero el pedido ya tiene devolución.
    El INSERT choca con UNIQUE(order_id) y debe responderse already_returned, no un 500."""
    monkeypatch.setattr(main, "eligibility_code", lambda conn, order_id, postal_code: "ok")
    before = count_returns(db)
    r = client.post(
        "/returns", json={"order_id": 8, "postal_code": "28005", "resolution": "refund"}
    )
    assert r.status_code == 200
    body = r.json()
    assert body["registered"] is False
    assert body["code"] == "already_returned"
    assert body["return_id"] is None
    assert count_returns(db) == before
