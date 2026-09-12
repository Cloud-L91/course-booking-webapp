import sqlite3
import datetime

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
CURRENT_DAY = "Wednesday"
CURRENT_TIME = "13:00"
MAX_ENROLLMENTS = 4
MIN_TIME_BEFORE_SESSION = datetime.timedelta(hours=12)

DATABASE = "database/project3_database.db"

def db_connect():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
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

def check_delete_eligibility(day, time):
    session_time = get_week_time(day, time)
    current_time = get_week_time(CURRENT_DAY, CURRENT_TIME)
    return session_time - current_time >= MIN_TIME_BEFORE_SESSION

def check_end_of_session(day, time, duration):
    session_start_time = get_week_time(day, time)
    session_duration = get_minutes(duration)
    session_end_time = session_start_time + session_duration
    current_time = get_week_time(CURRENT_DAY, CURRENT_TIME)
    return current_time >= session_end_time

def check_intervals_overlap(day1, time1, duration1, day2, time2, duration2):
    start1 = get_week_time(day1, time1)
    end1 = start1 + get_minutes(duration1)
    start2 = get_week_time(day2, time2)
    end2 = start2 + get_minutes(duration2)

    return start1 < end2 and start2 < end1
