from dao import utilities_dao

def get_user_by_email(email):
    conn = utilities_dao.db_connect()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM user WHERE email = ?", (email,))
    user = cursor.fetchone()

    utilities_dao.close_connection(conn, cursor)

    return user

def add_user(first_name, last_name, email, password_hash, role):
    conn = utilities_dao.db_connect()
    cursor = conn.cursor()
  
    try:
        cursor.execute("INSERT INTO user (first_name, last_name, email, password_hash, role) VALUES (?, ?, ?, ?, ?)",
            (first_name, last_name, email, password_hash, role))
        success = True
    except Exception:
        success = False
    finally:
        utilities_dao.close_connection(conn, cursor)

    return success

def get_manager_stats(email):
    conn = utilities_dao.db_connect()
    cursor = conn.cursor()

    stats = {
        "total_classes": 0,
        "total_sessions": 0,
        "total_enrollments": 0,
        "total_waiting_students": 0,
        "most_popular_cuisine": None,
        "highest_rated_class": None,
        "highest_avg_rating": 0.0
    }

    #1. Tot number of cooking classes created by the manager
    query = "SELECT COUNT(*) AS total_classes FROM COOKING_CLASS WHERE USER_email = ?"
    cursor.execute(query, (email,))
    stats["total_classes"] = cursor.fetchone()["total_classes"]

    #2. Total number of sessions created by the manager
    query = """SELECT COUNT(*) AS total_sessions
        FROM CLASS_SESSION, COOKING_CLASS
        WHERE CLASS_SESSION.COOKING_CLASS_id = COOKING_CLASS.id
          AND COOKING_CLASS.USER_email = ?
        """
    cursor.execute(query, (email,))
    stats["total_sessions"] = cursor.fetchone()["total_sessions"]

    #3. Total enrollments in all sessions created by the manager
    query = """
        SELECT COUNT(*) AS total_enrollments
        FROM BOOKING, CLASS_SESSION, COOKING_CLASS
        WHERE BOOKING.CLASS_SESSION_id = CLASS_SESSION.id
          AND CLASS_SESSION.COOKING_CLASS_id = COOKING_CLASS.id
          AND COOKING_CLASS.USER_email = ?
          AND BOOKING.status = 'ENROLLED'
          """
    cursor.execute(query, (email,))
    stats["total_enrollments"] = cursor.fetchone()["total_enrollments"]

    #4. Total number of students on the waiting list for all sessions created by the manager
    query = """
        SELECT COUNT(DISTINCT BOOKING.user_email) AS total_waiting_students
        FROM BOOKING, CLASS_SESSION, COOKING_CLASS
        WHERE BOOKING.CLASS_SESSION_id = CLASS_SESSION.id
          AND CLASS_SESSION.COOKING_CLASS_id = COOKING_CLASS.id
          AND COOKING_CLASS.USER_email = ?
          AND BOOKING.status = 'WAITING'
          """
    cursor.execute(query, (email,))
    stats["total_waiting_students"] = cursor.fetchone()["total_waiting_students"]

    #5. Most popular cuisine per enrolled students
    query = """
        SELECT COOKING_CLASS.cuisine, COUNT(*) AS enrolled_count
        FROM BOOKING, CLASS_SESSION, COOKING_CLASS
        WHERE BOOKING.CLASS_SESSION_id = CLASS_SESSION.id
          AND CLASS_SESSION.COOKING_CLASS_id = COOKING_CLASS.id
          AND COOKING_CLASS.USER_email = ?
          AND BOOKING.status = 'ENROLLED'
        GROUP BY COOKING_CLASS.cuisine
        ORDER BY enrolled_count DESC
        """
    cursor.execute(query, (email,))
    row = cursor.fetchone()
    if row:
        stats["most_popular_cuisine"] = row["cuisine"]

    #6. Class with the highest average rating
    query = """
        SELECT COOKING_CLASS.title, AVG(BOOKING.rating) AS avg_rate
        FROM BOOKING, CLASS_SESSION, COOKING_CLASS
        WHERE BOOKING.CLASS_SESSION_id = CLASS_SESSION.id
          AND CLASS_SESSION.COOKING_CLASS_id = COOKING_CLASS.id
          AND COOKING_CLASS.USER_email = ?
          AND BOOKING.rating IS NOT NULL
        GROUP BY COOKING_CLASS.id
        ORDER BY avg_rate DESC
        """
    cursor.execute(query, (email,))
    row = cursor.fetchone()
    if row and row["avg_rate"] is not None:
        stats["highest_rated_class"] = row["title"]
        stats["highest_avg_rating"] = round(float(row["avg_rate"]), 1)

    utilities_dao.close_connection(conn, cursor)

    return stats