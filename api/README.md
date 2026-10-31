# API de devoluciones

API (FastAPI + PostgreSQL) para consultar si un pedido se puede devolver y registrar la devolución.

Todos los comandos se ejecutan desde la carpeta `api/`.

## Requisitos

- [uv](https://docs.astral.sh/uv/) instalado.
- PostgreSQL en marcha en tu máquina, con una base llamada `venison` (esquema y datos en `../db/`).

## 1. Arrancar el servidor

```bash
uv sync                                  # instala las dependencias (solo la primera vez)
uv run uvicorn app.main:app --reload     # arranca la API
```

- API: <http://localhost:8000>
- Documentación interactiva, donde puedes probar los endpoints: <http://localhost:8000/docs>

Endpoints: `GET /health`, `GET /orders/{id}`, `POST /returns/eligibility` y `POST /returns`.

## 2. Crear la base de datos de tests (`venison_test`)

Los tests usan su propia base para no tocar tus datos reales. Se crea una sola vez, desde la raíz del repo:

```bash
createdb venison_test
psql venison_test -f db/schema.sql
```

No hace falta cargar el seed: los tests lo recargan solos antes de cada prueba.

## 3. Ejecutar los tests

```bash
uv run pytest -v
```

Deberías ver `21 passed`. Si falla con "database venison_test does not exist", repite el paso 2.
