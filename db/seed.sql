-- Clientes
INSERT INTO customers (name, email, postal_code) VALUES
('Marta Gómez', 'marta.gomez@example.com', '28001'),
('Javier Ruiz', 'javier.ruiz@example.com', '08002'),
('Lucía Fernández', 'lucia.fernandez@example.com', '41003'),
('Carlos Ortega', 'carlos.ortega@example.com', '46004'),
('Elena Torres', 'elena.torres@example.com', '28005');

-- Pedidos (algunos de hace más de 30 días, algunos de outlet)
INSERT INTO orders (customer_id, product_name, is_outlet, order_date) VALUES
(1, 'Camiseta azul, talla M', FALSE, CURRENT_DATE - INTERVAL '5 days'),
(1, 'Sudadera gris, talla L', FALSE, CURRENT_DATE - INTERVAL '45 days'),
(2, 'Pantalón negro, talla 42', FALSE, CURRENT_DATE - INTERVAL '10 days'),
(3, 'Camiseta blanca, talla S', TRUE,  CURRENT_DATE - INTERVAL '3 days'),
(3, 'Chaqueta vaquera, talla M', FALSE, CURRENT_DATE - INTERVAL '20 days'),
(4, 'Zapatillas blancas, talla 43', FALSE, CURRENT_DATE - INTERVAL '60 days'),
(4, 'Gorra negra', TRUE,  CURRENT_DATE - INTERVAL '2 days'),
(5, 'Vestido verde, talla M', FALSE, CURRENT_DATE - INTERVAL '15 days'),
(5, 'Bufanda roja', FALSE, CURRENT_DATE - INTERVAL '1 days'),
(2, 'Cinturón marrón', FALSE, CURRENT_DATE - INTERVAL '35 days');