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
CREATE TABLE returns (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(id),
    reason TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);