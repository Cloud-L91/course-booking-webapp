import sqlite3
from dao import utilities_dao

def get_user_by_email(email):
    conn = utilities_dao.db_connect()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM user WHERE email = ?", (email,))
    user = cursor.fetchone()

    utilities_dao.close_connection(conn, cursor)

    return user