from dao import utilities_dao

def enroll_user_in_session(status, session_id, user_email,):
    conn = utilities_dao.db_connect()
    cursor = conn.cursor()
    
    cursor.execute("INSERT INTO BOOKING (status, CLASS_SESSION_id, USER_email) VALUES (?, ?, ?)", (status, session_id, user_email))
    utilities_dao.close_connection(conn, cursor)

def check_existing_booking(user_email, session_id):
    conn = utilities_dao.db_connect()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM BOOKING WHERE USER_email = ? AND CLASS_SESSION_id = ?",
        (user_email, session_id)
    )
    booking = cursor.fetchone()

    utilities_dao.close_connection(conn, cursor)

    if booking:
        return booking["status"]

    return None

def count_user_enrollments(user_email):
    conn = utilities_dao.db_connect()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM BOOKING WHERE USER_email = ? AND status = 'ENROLLED'",
        (user_email,)
    )
    enrollment_count = cursor.fetchone()[0]

    utilities_dao.close_connection(conn, cursor)

    return enrollment_count

def check_delete_eligibility(day, time):
    session_time = utilities_dao.get_week_time(day, time)
    current_time = utilities_dao.get_week_time(utilities_dao.CURRENT_DAY, utilities_dao.CURRENT_TIME)
    return session_time - current_time >= utilities_dao.MIN_TIME_BEFORE_SESSION

def check_end_of_session(day, time, duration):
    session_start_time = utilities_dao.get_week_time(day, time)
    session_duration = utilities_dao.get_minutes(duration)
    session_end_time = session_start_time + session_duration
    current_time = utilities_dao.get_week_time(utilities_dao.CURRENT_DAY, utilities_dao.CURRENT_TIME)
    return current_time >= session_end_time

def delete_booking(user_email, session_id, day, time):
    if day == utilities_dao.CURRENT_DAY and time < utilities_dao.CURRENT_TIME:
        return False

    conn = utilities_dao.db_connect()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM BOOKING WHERE USER_email = ? AND CLASS_SESSION_id = ?", (user_email, session_id))

    utilities_dao.close_connection(conn, cursor)
    return True

def get_user_bookings(user_email):
    conn = utilities_dao.db_connect()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * 
        FROM BOOKING 
        WHERE BOOKING.USER_email = ?
    """, (user_email,))
    bookings = cursor.fetchall()

    utilities_dao.close_connection(conn, cursor)
    return bookings

def get_user_enrolled_sessions(user_email):
    conn = utilities_dao.db_connect()
    cursor = conn.cursor()

    query = """
        SELECT 
            CLASS_SESSION.id,
            COOKING_CLASS.title,
            COOKING_CLASS.cuisine,
            COOKING_CLASS.chef_name,
            COOKING_CLASS.duration,
            CLASS_SESSION.day_of_week,
            CLASS_SESSION.start_time,
            CLASS_SESSION.kitchen,
            BOOKING.rating
        FROM BOOKING, CLASS_SESSION, COOKING_CLASS
        WHERE BOOKING.CLASS_SESSION_id = CLASS_SESSION.id
          AND CLASS_SESSION.COOKING_CLASS_id = COOKING_CLASS.id
          AND BOOKING.USER_email = ?
          AND BOOKING.status = 'ENROLLED'
    """
    cursor.execute(query, (user_email,))
    booked_sessions = cursor.fetchall()

    utilities_dao.close_connection(conn, cursor)
    return booked_sessions