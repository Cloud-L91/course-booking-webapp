from dao import utilities_dao

def enroll_user_in_session(status, session_id, user_email,):
    conn = utilities_dao.db_connect()
    cursor = conn.cursor()
    
    cursor.execute("INSERT INTO BOOKING (status, CLASS_SESSION_id, USER_email) VALUES (?, ?, ?)", (status, session_id, user_email))
    utilities_dao.close_connection(conn, cursor)

def check_existing_booking(user_email, session_id):
    conn = utilities_dao.db_connect()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM BOOKING WHERE USER_email = ? AND CLASS_SESSION_id = ?", (user_email, session_id))
    booking = cursor.fetchone()

    utilities_dao.close_connection(conn, cursor)

    if booking:
        return booking["status"]

    return None

def count_user_enrollments(user_email):
    all_sessions = get_user_enrolled_sessions(user_email)

    active_enrollments = 0
    for session in all_sessions:
        if session["status"] == "ENROLLED" and not check_end_of_session(session["day_of_week"], session["start_time"], session["duration"]):
            active_enrollments += 1

    return active_enrollments

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
    conn = utilities_dao.db_connect()
    cursor = conn.cursor()

    cursor.execute("SELECT status FROM BOOKING WHERE USER_email = ? AND CLASS_SESSION_id = ?",(user_email, session_id))
    booking = cursor.fetchone()
    was_enrolled = booking and booking["status"] == "ENROLLED"

    cursor.execute("DELETE FROM BOOKING WHERE USER_email = ? AND CLASS_SESSION_id = ?", (user_email, session_id))

    utilities_dao.close_connection(conn, cursor)

    if was_enrolled:
        promote_waiting_list(session_id)

    return True

def promote_waiting_list(session_id):
    conn = utilities_dao.db_connect()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, USER_email
        FROM BOOKING 
        WHERE CLASS_SESSION_id = ? AND status = 'WAITING' 
        ORDER BY id ASC
        """,
        (session_id,)
    )

    waiting_users = cursor.fetchall()

    promoted = False
    for user in waiting_users:
        if not promoted and count_user_enrollments(user["USER_email"]) < utilities_dao.MAX_ENROLLMENTS:
            cursor.execute("UPDATE BOOKING SET status = 'ENROLLED' WHERE id = ?",(user["id"],))
            promoted = True

    utilities_dao.close_connection(conn, cursor)

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
            BOOKING.status,
            BOOKING.rating
        FROM BOOKING, CLASS_SESSION, COOKING_CLASS
        WHERE BOOKING.CLASS_SESSION_id = CLASS_SESSION.id
          AND CLASS_SESSION.COOKING_CLASS_id = COOKING_CLASS.id
          AND BOOKING.USER_email = ?
          AND BOOKING.status IN ('ENROLLED', 'WAITING')
    """
    cursor.execute(query, (user_email,))
    booked_sessions = cursor.fetchall()

    utilities_dao.close_connection(conn, cursor)
    return booked_sessions

def get_user_rating(user_email, session_id):
    conn = utilities_dao.db_connect()
    cursor = conn.cursor()

    query = """
        SELECT rating
        FROM BOOKING
        WHERE USER_email = ? AND CLASS_SESSION_id = ?
    """
    cursor.execute(query, (user_email, session_id))
    rating = cursor.fetchone()

    utilities_dao.close_connection(conn, cursor)

    if rating:
        return rating["rating"]
    else:
        return None

def set_user_rating(user_email, session_id, rating):
    conn = utilities_dao.db_connect()
    cursor = conn.cursor()

    query = """
        UPDATE BOOKING
        SET rating = ?
        WHERE USER_email = ? AND CLASS_SESSION_id = ? AND rating IS NULL
    """

    cursor.execute(query, (rating, user_email, session_id))
    success = cursor.rowcount > 0

    utilities_dao.close_connection(conn, cursor)

    return success

def insert_in_waiting_list(status,user_email, session_id):
    conn = utilities_dao.db_connect()
    cursor = conn.cursor()

    cursor.execute("INSERT INTO BOOKING (status, CLASS_SESSION_id, USER_email) VALUES (?, ?, ?)", (status, session_id, user_email))
    utilities_dao.close_connection(conn, cursor)

def get_waiting_list_positions(user_email, session_id):
    conn = utilities_dao.db_connect()
    cursor = conn.cursor()

    query = """
        SELECT COUNT(*) AS position
        FROM BOOKING
        WHERE CLASS_SESSION_id = ?
            AND status = 'WAITING'
            AND id <= (
                SELECT id
                FROM BOOKING
                WHERE CLASS_SESSION_id = ?
                    AND USER_email = ?
            )
    """
    cursor.execute(query, (session_id, session_id, user_email))
    waiting_list = cursor.fetchone()

    utilities_dao.close_connection(conn, cursor)
    return waiting_list["position"] if waiting_list else None