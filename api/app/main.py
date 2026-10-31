from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.db import get_connection

app = FastAPI()

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/orders/{order_id}")
def get_order(order_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, customer_id, product_name, is_outlet, order_date FROM orders WHERE id = %s",
        (order_id,)
    )
    row = cur.fetchone()
    conn.close()

    if row is None:
        raise HTTPException(status_code=404, detail="Order not found")

    return {
        "id": row[0],
        "customer_id": row[1],
        "product_name": row[2],
        "is_outlet": row[3],
        "order_date": str(row[4]),
    }


RETURN_WINDOW_DAYS = 30

MESSAGES = {
    "ok": "Tu pedido se puede devolver.",
    "not_found": "No encuentro ningún pedido con esos datos. ¿Puedes repetirme el número de pedido y el código postal?",
    "already_returned": "Este pedido ya tiene una devolución registrada.",
    "outlet": "Lo siento, los productos de outlet no se pueden devolver.",
    "expired": "Lo siento, han pasado más de 30 días desde el pedido y ya no se puede devolver.",
}


class EligibilityRequest(BaseModel):
    order_id: int
    postal_code: str


class EligibilityResponse(BaseModel):
    eligible: bool
    code: Literal["ok", "not_found", "already_returned", "outlet", "expired"]
    message: str


def eligibility_result(code: str) -> dict:
    return {"eligible": code == "ok", "code": code, "message": MESSAGES[code]}


@app.post("/returns/eligibility", response_model=EligibilityResponse)
def check_eligibility(body: EligibilityRequest):
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT o.is_outlet,
                   CURRENT_DATE - o.order_date AS days_old,
                   EXISTS (SELECT 1 FROM returns r WHERE r.order_id = o.id) AS has_return
            FROM orders o
            JOIN customers c ON c.id = o.customer_id
            WHERE o.id = %s AND c.postal_code = %s
            """,
            (body.order_id, body.postal_code.strip()),
        ).fetchone()

    if row is None:
        return eligibility_result("not_found")

    is_outlet, days_old, has_return = row
    if has_return:
        return eligibility_result("already_returned")
    if is_outlet:
        return eligibility_result("outlet")
    if days_old > RETURN_WINDOW_DAYS:
        return eligibility_result("expired")
    return eligibility_result("ok")