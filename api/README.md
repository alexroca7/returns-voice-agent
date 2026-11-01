# API de devoluciones

API (FastAPI + PostgreSQL) para consultar si un pedido se puede devolver y registrar la devolución.

Todos los comandos se ejecutan desde la carpeta `api/`.

## Requisitos

- [uv](https://docs.astral.sh/uv/) instalado.
- PostgreSQL en marcha en tu máquina, con una base llamada `venison` (esquema y datos en `../db/`).

## 0. Configurar el archivo `.env`

La configuración va en variables de entorno, no en el código. Copia la plantilla y rellena tus valores:

```bash
cp .env.example .env
```

| Variable | Para qué sirve |
|---|---|
| `DATABASE_URL` | Conexión completa a la base real: `postgresql://usuario:contraseña@host:5432/base` |
| `TEST_DATABASE_URL` | Conexión a la base de tests. Su nombre debe terminar en `_test` |
| `API_KEY` | Clave que los clientes envían en la cabecera `X-API-Key` |

`.env` no se sube a git. Si falta `DATABASE_URL` o `API_KEY`, la API da un error que lo explica.

## 1. Arrancar el servidor

```bash
uv sync                                                  # instala las dependencias (solo la primera vez)
uv run --env-file .env uvicorn app.main:app --reload     # arranca la API leyendo el .env
```

- API: <http://localhost:8000>
- Documentación interactiva: <http://localhost:8000/docs>

Todos los endpoints exigen la cabecera `X-API-Key`, salvo `GET /health`. Sin clave o con una clave incorrecta responden `401`.

- **En `/docs`:** pulsa el botón **Authorize**, pega tu `API_KEY` y ya puedes probar los endpoints.
- **Con curl:**
  ```bash
  curl -H "X-API-Key: TU_CLAVE" http://localhost:8000/orders/1
  ```

Endpoints: `GET /health`, `GET /orders/{id}`, `POST /returns/eligibility` y `POST /returns`.

## 2. Crear la base de datos de tests (`venison_test`)

Los tests usan su propia base para no tocar tus datos reales. Se crea una sola vez, desde la raíz del repo:

```bash
createdb venison_test
psql venison_test -f db/schema.sql
```

No hace falta cargar el seed: los tests lo recargan solos antes de cada prueba. Los tests **vacían** esa base, y por eso se niegan a ejecutarse si `TEST_DATABASE_URL` apunta a una base cuyo nombre no termina en `_test`.

## 3. Ejecutar los tests

```bash
uv run --env-file .env pytest -v
```

Deberías ver `42 passed`. Si falla con "database venison_test does not exist", repite el paso 2.
