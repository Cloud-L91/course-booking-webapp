import sqlite3

FIRST_DAY = "Monday"
LAST_DAY = "Sunday"
CURRENT_DAY = "Wednesday"
CURRENT_TIME = "13:00"
MAX_ENROLLMENTS = 4

DATABASE = "database/project3_database.db"

def db_connect():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def close_connection(conn, cursor):
    conn.commit()
    cursor.close()
    conn.close()