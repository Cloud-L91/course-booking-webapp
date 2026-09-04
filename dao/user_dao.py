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