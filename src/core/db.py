import mysql.connector
from contextlib import contextmanager
from src.core.config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME

@contextmanager
def db_cursor(commit=False, dictionary=True):
    connection = mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )
    cursor = connection.cursor(dictionary=dictionary)
    try:
        yield cursor
        if commit:
            connection.commit()
    except Exception as e:
        connection.rollback()
        raise e
    finally:
        cursor.close()
        connection.close()