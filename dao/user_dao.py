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
  
    cursor.execute("INSERT INTO user (first_name, last_name, email, password_hash, role) VALUES (?, ?, ?, ?, ?)",
        (first_name, last_name, email, password_hash, role))

    utilities_dao.close_connection(conn, cursor)

def get_students_by_session_and_status(session_id, status):
    conn = utilities_dao.db_connect()
    cursor = conn.cursor()

    query = """
        SELECT *
        FROM USER, BOOKING
        WHERE BOOKING.USER_email = USER.email
            AND USER.role = 'student'
            AND BOOKING.CLASS_SESSION_id = ? AND BOOKING.status = ?
        """

    cursor.execute(query, (session_id, status))
    students = cursor.fetchall()
    utilities_dao.close_connection(conn, cursor)

    return students

def get_manager_stats(email):
    conn = utilities_dao.db_connect()
    cursor = conn.cursor()

    stats = {
        "total_classes": 0,
        "total_sessions": 0,
        "total_enrollments": 0,
        "total_waiting_students": 0,
        "most_popular_cuisines": [],
        "highest_rated_classes": [],
        "highest_avg_rating": 0.0
    }

    #1. TOTAL number of COOKING CLASSES created by the manager
    query = "SELECT COUNT(*) AS total_classes FROM COOKING_CLASS WHERE USER_email = ?"
    cursor.execute(query, (email,))
    stats["total_classes"] = cursor.fetchone()["total_classes"]

    #2. TOTAL number of SESSIONS created by the manager
    query = """
        SELECT COUNT(*) AS total_sessions
        FROM CLASS_SESSION, COOKING_CLASS
        WHERE CLASS_SESSION.COOKING_CLASS_id = COOKING_CLASS.id
            AND COOKING_CLASS.USER_email = ?
        """
    cursor.execute(query, (email,))
    stats["total_sessions"] = cursor.fetchone()["total_sessions"]

    #3. TOTAL ENROLLMENTS in all sessions created by the manager
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

    #4. Total number of students on the WAITING LIST for all sessions created by the manager
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

    #5. Most POPULAR CUISINE per enrolled students
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
    rows = cursor.fetchall()

    top_cuisines = []
    if rows:
        max_enrolled_count = rows[0]["enrolled_count"]
        for row in rows:
            if row["enrolled_count"] == max_enrolled_count:
                top_cuisines.append(row["cuisine"])

    stats["most_popular_cuisines"] = top_cuisines

    #6. Class with the HIGHEST AVERAGE RATING
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
    rows = cursor.fetchall()

    top_classes = []
    if rows and rows[0]["avg_rate"] is not None:
        stats["highest_avg_rating"] = round(float(rows[0]["avg_rate"]), 1)
        for row in rows:
            if round(float(row["avg_rate"]), 1) == stats["highest_avg_rating"]:
                top_classes.append(row["title"])

    stats["highest_rated_classes"] = top_classes

    utilities_dao.close_connection(conn, cursor)

    return stats