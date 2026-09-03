import sqlite3
import datetime
from werkzeug.security import generate_password_hash, check_password_hash

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
CURRENT_DAY = "Wednesday"
CURRENT_TIME = "13:00"
MAX_ENROLLMENTS = 4
MIN_TIME_BEFORE_SESSION = datetime.timedelta(hours=12)

DATABASE = "database/project3_database.db"

def db_connect():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def close_connection(conn, cursor):
    conn.commit()
    cursor.close()
    conn.close()

def get_week_time(day, time_str):
    hours, minutes = time_str.split(":")
    return datetime.timedelta(days=DAYS.index(day), hours=int(hours), minutes=int(minutes))

def get_minutes(time_str):
    return datetime.timedelta(minutes=int(time_str))
