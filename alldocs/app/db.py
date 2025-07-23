import psycopg2

def get_db_conn():
    return psycopg2.connect(
        host="localhost",
        database="postgres",
        user="postgres",
        password="postgres"
    )

