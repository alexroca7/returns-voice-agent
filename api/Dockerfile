# Imagen de la API para Lightsail (Linux amd64).
# Se construye desde la carpeta api/:  docker build --platform linux/amd64 -t returns-api api
FROM --platform=linux/amd64 python:3.12-slim

# uv instala las dependencias exactas de uv.lock. Solo se copia el binario; no queda nada más.
COPY --from=ghcr.io/astral-sh/uv:0.12.19 /uv /usr/local/bin/uv

ENV PYTHONUNBUFFERED=1 \
    UV_PYTHON_DOWNLOADS=never \
    UV_COMPILE_BYTECODE=1 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# 1) Dependencias primero: esta capa se reutiliza mientras no cambien pyproject.toml ni uv.lock.
#    --frozen: usa uv.lock tal cual. --no-dev: sin pytest ni httpx. --no-install-project: solo librerías.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# 2) El código de la API (solo app/; tests, .env y .venv quedan fuera por .dockerignore).
COPY app ./app

# 3) No ejecutar como root dentro del contenedor.
RUN useradd --system --no-create-home appuser
USER appuser

EXPOSE 8000

# La configuración (DATABASE_URL, API_KEY) llega por variables de entorno, nunca dentro de la imagen.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
