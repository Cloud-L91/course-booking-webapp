import sqlite3
import datetime, time

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
CURRENT_DAY = "Wednesday"
CURRENT_TIME = "13:00"
MAX_ENROLLMENTS = 4
MIN_TIME_BEFORE_SESSION = datetime.timedelta(hours=12)

DATABASE = "database/project3_database.db"

# FUNZIONE DI APERTURA DELLA CONNESSIONE AL DATABASE CON ATTIVAZIONE DELLE FOREIGN KEY
def db_connect():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

# CHIUSURA DELLA CONNESSIONE AL DATABASE E DEL CURSOR PER EVITARE TROPPE RIPETIZIONI DI CODICE
def close_connection(conn, cursor):
    conn.commit()
    cursor.close()
    conn.close()

# PRENDE IL GIORNO E L'ORA DELLA SETTIMANA E RESTITUISCE UN OGGETTO datetime.timedelta PER FACILITARE IL CONFRONTO TRA ORARI
def get_week_time(day, time_str):
    hours, minutes = time_str.split(":")
    return datetime.timedelta(days=DAYS.index(day), hours=int(hours), minutes=int(minutes))

# CONVERTI IL TEMPO IN MINUTI PER FACILITARE IL CONFRONTO
def get_minutes(time_str):
    return datetime.timedelta(minutes=int(time_str))

# ORDINA SESSIONI PER GIORNO E ORA
def sort_sessions_chronologically(sessions_list):
    sessions_list.sort(key=lambda s: (DAYS.index(s["day_of_week"]), s["start_time"]))
    return sessions_list

# CONTROLLO SE LA SESSIONE PUÒ ESSERE ELIMINATA (ALMENO 12 ORE PRIMA DELL'INIZIO)
def check_delete_eligibility(day, time):
    session_time = get_week_time(day, time)
    current_time = get_week_time(CURRENT_DAY, CURRENT_TIME)
    return session_time - current_time >= MIN_TIME_BEFORE_SESSION

# CONTROLLA SE L'ORARIO DELLA SESSIONE SI SOVRAPPONE CON QUELLO DI UN'ALTRA SESSIONE O SE RISULTA PASSATA
# IMPOSTANDO duration A 0, SI CONSIDERA SOLO L'ORARIO DI INIZIO PER SESSIONI ANCORA IN CORSO
def check_end_of_session(day, time, duration):
    session_start_time = get_week_time(day, time)
    session_duration = get_minutes(duration)
    session_end_time = session_start_time + session_duration
    current_time = get_week_time(CURRENT_DAY, CURRENT_TIME)
    return current_time >= session_end_time

# CONTROLLO SOVRAPPOSIZIONE ORARIA TRA DUE SESSIONI
def check_intervals_overlap(day1, time1, duration1, day2, time2, duration2):
    start1 = get_week_time(day1, time1)
    end1 = start1 + get_minutes(duration1)
    start2 = get_week_time(day2, time2)
    end2 = start2 + get_minutes(duration2)

    return start1 < end2 and start2 < end1

# CONTROLLO BACK-END DEL FORMATO DELL'ORARIO INSERITO NELLA CREAZIONE E MODIFICA DI UNA SESSIONE DAL MANAGER
def validate_time_format(time_str):
    try:
        datetime.datetime.strptime(time_str, "%H:%M")
        return True
    except (ValueError, TypeError):
        return False

# CONTROLLO BACK-END DEL FORMATO DEI DATI INSERITI NELLA REGISTRAZIONE DI UN UTENTE
def validate_registration_format(first_name, last_name, email, password, confirm_password, role):
        if not all([first_name, last_name, email, password, confirm_password, role]):
            return "All fields are required"

        if not (2 <= len(first_name) <= 50) or not (2 <= len(last_name) <= 50):
            return"First and last name must be between 2 and 50 characters"

        if not (5 <= len(email) <= 50):
            return "Email must be between 5 and 50 characters"

        if not (6 <= len(password) <= 30):
            return "Password must be between 6 and 30 characters"

        if password != confirm_password:
            return "Passwords do not match"

        if role not in ["student", "manager"]:
            return "Invalid role"

# CONTROLLO BACK-END DEL FORMATO DEI DATI INSERITI NELLA CREAZIONE DI UNA CLASSE DAL MANAGER
def validate_class_format(title, cuisine, duration, difficulty, chef_name, description, dietary_category, ingredients):
    if not 2 <= len(title) <= 30:
        return "Title must be between 2 and 30 characters"

    if not 2 <= len(cuisine) <= 30:
        return "Cuisine must be between 2 and 30 characters"

    if not 30 <= duration <= 240:
        return "Duration must be between 30 and 240 minutes"

    if difficulty not in ["Beginner", "Intermediate", "Advanced"]:
        return "Invalid difficulty level"

    if not 2 <= len(chef_name) <= 30:
        return "Chef name must be between 2 and 30 characters"

    if len(description) > 500:
        return "Description cannot exceed 500 characters"

    if dietary_category not in ["Standard", "Vegetarian", "Vegan", "Gluten-free"]:
        return "Invalid dietary category"

    if len(ingredients) < 4:
        return "Please insert at least 4 ingredients"

    return None  # VA TUTTO BENE

# CONTROLLO BACK-END DEL FORMATO DEI DATI INSERITI NELLA CREAZIONE E MODIFICA DI UNA SESSIONE DAL MANAGER
def validate_session_format(day_of_week, start_time, kitchen, max_capacity):

    if day_of_week not in DAYS:
        return "Invalid day of the week."

    if not validate_time_format(start_time):
        return "Invalid time format. Please use HH:MM format."

    if not (2 < len(kitchen) < 30):
        return "Kitchen name must be between 2 and 30 characters."
    
    if not max_capacity or not (1 <= int(max_capacity) <= 10):
        return "Max capacity must be between 1 and 10"

    # EVITA DI SCHEDULARE SESSIONI PRIMA DI ORA (È SITO DI CUCINA, NON IL TARDIS)
    if check_end_of_session(day_of_week, start_time, 0):
        return "Cannot schedule a session in the past."

    return None  # VA TUTTO BENE

def save_class_photos(email, uploaded_photos):
    timestamp = int(time.time())
    photo_filenames = []

    for file in uploaded_photos:
        if not file or not file.filename:
            return None, "All three photos are required."

    for i in range(3):
        file = uploaded_photos[i]
        filename = f"{email}_{timestamp}_{i+1}_{file.filename}"
        file.save(f"static/img/classes/{filename}")
        photo_filenames.append(filename)

    return photo_filenames, None