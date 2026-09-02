from dao import utilities_dao

def get_all_classes_per_manager(manager_email):
    conn = utilities_dao.db_connect()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM cooking_class WHERE manager_email = ?", (manager_email,))

    cooking_classes = cursor.fetchall()

    utilities_dao.close_connection(conn, cursor)

    return cooking_classes

def get_single_cooking_class(id):
    conn = utilities_dao.db_connect()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM cooking_class WHERE id = ?", (id,))
    cooking_class = cursor.fetchone()

    utilities_dao.close_connection(conn, cursor)

    return cooking_class

def get_all_sessions():
    conn = utilities_dao.db_connect()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT * 
    FROM CLASS_SESSION 
    JOIN COOKING_CLASS ON CLASS_SESSION.COOKING_CLASS_id = COOKING_CLASS.id
    """)
    sessions = cursor.fetchall()

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

def get_ingredients(cooking_class_id):
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
