from dao import utilities_dao

def get_all_classes_per_manager(manager_email):
    conn = utilities_dao.db_connect()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM cooking_class WHERE USER_email = ?", (manager_email,))

    cooking_classes = cursor.fetchall()
    cooking_classes.sort(key=lambda c: c["id"], reverse=True)

    utilities_dao.close_connection(conn, cursor)

    return cooking_classes

def get_single_cooking_class(id):
    conn = utilities_dao.db_connect()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM cooking_class WHERE id = ?", (id,))
    cooking_class = cursor.fetchone()

    utilities_dao.close_connection(conn, cursor)

    return cooking_class

def get_sessions_per_manager(manager_email):
    conn = utilities_dao.db_connect()
    cursor = conn.cursor()

    query = """
        SELECT CLASS_SESSION.*,
            (SELECT COUNT(*)
             FROM BOOKING
             WHERE BOOKING.CLASS_SESSION_id = CLASS_SESSION.id
               AND BOOKING.status = 'ENROLLED') AS enrolled_count
        FROM CLASS_SESSION, COOKING_CLASS
        WHERE COOKING_CLASS.id = CLASS_SESSION.COOKING_CLASS_id
            AND COOKING_CLASS.USER_email = ?
        """

    cursor.execute(query, (manager_email,))
    sessions = cursor.fetchall()

    sessions.sort(key=lambda s: (utilities_dao.DAYS.index(s["day_of_week"]), s["start_time"]))

    utilities_dao.close_connection(conn, cursor)
    return sessions

def get_session_rating(session_id):
    conn = utilities_dao.db_connect()
    cursor = conn.cursor()

    query = """
        SELECT AVG(rating) AS avg_rating
        FROM BOOKING
        WHERE CLASS_SESSION_id = ? AND rating IS NOT NULL
    """
    cursor.execute(query, (session_id,))
    result = cursor.fetchone()

    utilities_dao.close_connection(conn, cursor)

    if result and result["avg_rating"] is not None:
        return round(result["avg_rating"], 1)
    return None

def get_all_sessions():
    conn = utilities_dao.db_connect()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * 
        FROM CLASS_SESSION 
        JOIN COOKING_CLASS ON CLASS_SESSION.COOKING_CLASS_id = COOKING_CLASS.id
        """)
    sessions = cursor.fetchall()
    sessions.sort(key=lambda s: (utilities_dao.DAYS.index(s["day_of_week"]), s["start_time"]))

    utilities_dao.close_connection(conn, cursor)
    return sessions

def get_single_session(session_id):
    conn = utilities_dao.db_connect()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM CLASS_SESSION
        JOIN COOKING_CLASS ON CLASS_SESSION.COOKING_CLASS_id = COOKING_CLASS.id
        WHERE CLASS_SESSION.id = ?
        """, (session_id,))

    session = cursor.fetchone()

    utilities_dao.close_connection(conn, cursor)

    return session

def get_ingredients_per_class(cooking_class_id):
    conn = utilities_dao.db_connect()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT *
    FROM INGREDIENT
    WHERE COOKING_CLASS_id = ?
    """, (cooking_class_id,))
    
    ingredients = cursor.fetchall()

    utilities_dao.close_connection(conn, cursor)

    return ingredients

def get_all_ingredients():
    conn = utilities_dao.db_connect()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM ingredient")
    ingredients = cursor.fetchall()

    utilities_dao.close_connection(conn, cursor)

    return ingredients

def get_available_spots(session_id):
    conn = utilities_dao.db_connect()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT max_capacity - (
            SELECT COUNT(*) 
            FROM BOOKING 
            WHERE CLASS_SESSION_id = CLASS_SESSION.id AND status = 'ENROLLED') AS available_spots
        FROM CLASS_SESSION
        WHERE CLASS_SESSION.id = ?
        """, (session_id,))

    result = cursor.fetchone()
    utilities_dao.close_connection(conn, cursor)

    if result and result[0] is not None:
        return int(result[0])
    return 0

def get_class_rating(cooking_class_id):
    conn = utilities_dao.db_connect()
    cursor = conn.cursor()

    query = """
        SELECT AVG(rating) AS average_rating, COUNT(rating) AS tot_ratings
        FROM BOOKING, CLASS_SESSION
        WHERE BOOKING.CLASS_SESSION_id = CLASS_SESSION.id
          AND CLASS_SESSION.COOKING_CLASS_id = ?
          AND BOOKING.rating IS NOT NULL
        """
    cursor.execute(query, (cooking_class_id,))
    result = cursor.fetchone()
    utilities_dao.close_connection(conn, cursor)

    if result and result["average_rating"] is not None:
        return float(result["average_rating"]), int(result["tot_ratings"])
    return None, 0

def add_cooking_class(title, cuisine, duration, difficulty, chef_name, description, dietary_category, photo_1, photo_2, photo_3, current_user_email, ingredients):
    conn = utilities_dao.db_connect()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO COOKING_CLASS (title, cuisine, duration, difficulty, chef_name, description, dietary_category, photo_1, photo_2, photo_3, USER_email)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (title, cuisine, duration, difficulty, chef_name, description, dietary_category, photo_1, photo_2, photo_3, current_user_email))

    class_id = cursor.lastrowid

    for ingredient in ingredients:
        cursor.execute("INSERT INTO INGREDIENT (name, COOKING_CLASS_id) VALUES (?, ?)", (ingredient, class_id))

    utilities_dao.close_connection(conn, cursor)

def add_session(cooking_class_id, day_of_week, start_time, kitchen, max_capacity):
    conn = utilities_dao.db_connect()
    cursor = conn.cursor()

    query ="INSERT INTO CLASS_SESSION (COOKING_CLASS_id, day_of_week, start_time, kitchen, max_capacity) VALUES (?, ?, ?, ?, ?)"
    cursor.execute(query, (cooking_class_id, day_of_week, start_time, kitchen, max_capacity))

    utilities_dao.close_connection(conn, cursor)

def delete_session(session_id):
    conn = utilities_dao.db_connect()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM CLASS_SESSION WHERE id = ?", (session_id,))

    utilities_dao.close_connection(conn, cursor)