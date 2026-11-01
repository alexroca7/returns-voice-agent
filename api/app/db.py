import os

import psycopg


def get_connection():
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError(
            "Falta la variable de entorno DATABASE_URL. "
            "Defínela en el archivo .env (mira .env.example)."
        )
    return psycopg.connect(url)
