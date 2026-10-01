from fastapi import FastAPI, HTTPException
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