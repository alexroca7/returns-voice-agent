import psycopg

def get_connection():
    return psycopg.connect(
        host="localhost",
        dbname="venison",
        user="alexroca",
    )