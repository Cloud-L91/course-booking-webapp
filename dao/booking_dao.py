from dao import utilities_dao, cooking_class_dao

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