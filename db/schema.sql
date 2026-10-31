-- Clientes de la tienda
CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    postal_code TEXT NOT NULL
);

-- Pedidos
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    product_name TEXT NOT NULL,
    is_outlet BOOLEAN NOT NULL DEFAULT FALSE,
    order_date DATE NOT NULL
);

-- Devoluciones
-- UNIQUE en order_id: un pedido solo puede tener una devolución.
-- CHECK en status: solo se permiten estados conocidos.
CREATE TABLE returns (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL UNIQUE REFERENCES orders(id),
    reason TEXT,
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'approved', 'rejected')),
    resolution TEXT CHECK (resolution IN ('refund', 'exchange')),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);