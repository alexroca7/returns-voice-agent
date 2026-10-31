import os

import psycopg

def get_connection():
    return psycopg.connect(
        host="localhost",
        dbname=os.environ.get("DB_NAME", "venison"),
        user="alexroca",
    )
