import sqlite3

DATABASE = "database/project3_database.db"

def db_connect():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def close_connection(conn, cursor):
    conn.commit()
    cursor.close()
    conn.close()