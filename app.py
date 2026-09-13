from flask import Flask, flash, render_template, request, redirect, url_for
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from dao import cooking_class_dao, booking_dao, user_dao, utilities_dao
from user import User

app = Flask(__name__)
app.config["SECRET_KEY"] = "gli_occhi_del_cuore"

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    db_user = user_dao.get_user_by_email(user_id)
    if not db_user:
        return None
    return User(
        email=db_user["email"],
        first_name=db_user["first_name"],
        last_name=db_user["last_name"],
        password=db_user["password_hash"],
        role=db_user["role"]
    )

# GIORNO E ORA ATTUALI VISIBILI IN TUTTI I TEMPLATE
@app.context_processor
def inject_current_time():
    return {"current_day": utilities_dao.CURRENT_DAY, "current_time": utilities_dao.CURRENT_TIME}

# PAGINE PUBBLICHE
@app.route("/")
def home():
    session_classes = cooking_class_dao.get_all_sessions()

    passed_sessions = []
    for session in session_classes:
        if utilities_dao.check_end_of_session(session["day_of_week"], session["start_time"], session["duration"]):
            passed_sessions.append(session["id"])

    # UNA SOLA QUERY PER OTTENERE TUTTE LE PRENOTAZIONI DELL'UTENTE LOGGATO
    user_bookings = {}
    if current_user.is_authenticated:
        for booking in booking_dao.get_user_bookings(current_user.email):
            user_bookings[booking["CLASS_SESSION_id"]] = booking["status"]

    return render_template("public/index.html", session_classes=session_classes, user_bookings=user_bookings, passed_sessions=passed_sessions)

@app.route("/session_details/<int:session_id>")
def session_details(session_id):
    session_class = cooking_class_dao.get_single_session(session_id)
    if not session_class:
        return redirect(url_for("home"))

    ingredients = cooking_class_dao.get_ingredients_per_class(session_class["COOKING_CLASS_id"])
    available_spots = cooking_class_dao.get_available_spots(session_id)
    rating, total_votes = cooking_class_dao.get_class_rating(session_class["COOKING_CLASS_id"])

    manager = user_dao.get_user_by_email(session_class["USER_email"])
    name_manager = f"{manager['first_name']} {manager['last_name']}"

    day = session_class["day_of_week"]
    time = session_class["start_time"]
    duration = session_class["duration"]

    deletable = utilities_dao.check_delete_eligibility(day, time)
    passed_session = utilities_dao.check_end_of_session(day, time, duration)
    session_started = utilities_dao.check_end_of_session(day, time, 0)
    session_in_progress = session_started and not passed_session

    user_status = None
    max_bookings_reached = False
    has_conflict = False

    if current_user.is_authenticated and current_user.role == "student":
        user_status = booking_dao.check_existing_booking(current_user.email, session_id)
        max_bookings_reached = booking_dao.count_user_enrollments(current_user.email) >= utilities_dao.MAX_ENROLLMENTS
        has_conflict = booking_dao.check_time_conflict(current_user.email, session_id)

    return render_template(
        "public/session_details.html",
        session_class=session_class,
        session_id=session_id,
        ingredients=ingredients,
        available_spots=available_spots,
        user_status=user_status,
        passed_session=passed_session,
        max_bookings_reached=max_bookings_reached,
        rating=rating,
        total_votes=total_votes,
        deletable=deletable,
        session_in_progress=session_in_progress,
        has_conflict=has_conflict,
        name_manager=name_manager,
        max_enrollments=utilities_dao.MAX_ENROLLMENTS
        )

# AUTENTICAZIONE
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        db_user = user_dao.get_user_by_email(email)

        if not db_user:
            return render_template("authentication/login.html", error="User not found")

        if not check_password_hash(db_user["password_hash"], password):
            return render_template("authentication/login.html", error="Incorrect password")

        login_user(load_user(email))
        return redirect(url_for("home"))

    return render_template("authentication/login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")
        role = request.form.get("role")

        error = utilities_dao.validate_registration_format(first_name, last_name, email, password, confirm_password, role)
        if error:
            return render_template("authentication/register.html", error=error)
        
        if user_dao.get_user_by_email(email):
            return render_template("authentication/register.html", error="User already exists")

        user_dao.add_user(first_name, last_name, email, generate_password_hash(password), role)
        flash("Account created!", "success")
        return redirect(url_for("login"))

    return render_template("authentication/register.html")

# PROFILI
@app.route("/profile")
@login_required
def profile():
    if current_user.role == "student":
        return redirect(url_for("student_profile"))
    elif current_user.role == "manager":
        return redirect(url_for("manager_profile"))
    else:
        return redirect(url_for("home"))

@app.route("/student_profile")
@login_required
def student_profile():
    if current_user.role != "student":
        return redirect(url_for("home"))

    all_sessions = booking_dao.get_user_enrolled_sessions(current_user.email)
    all_sessions = utilities_dao.sort_sessions_chronologically(all_sessions)

    upcoming_sessions = []
    past_sessions = []
    on_waiting_list = []

    for session in all_sessions:
        session = dict(session)
        ended = utilities_dao.check_end_of_session(session["day_of_week"], session["start_time"], session["duration"])

        if session["status"] == "WAITING":
            if not ended:
                session["waiting_position"] = booking_dao.get_waiting_list_positions(current_user.email, session["id"])
                on_waiting_list.append(session)
        elif ended:
            past_sessions.append(session)
        else:
            session["deletable"] = utilities_dao.check_delete_eligibility(session["day_of_week"], session["start_time"])
            upcoming_sessions.append(session)

    return render_template(
        "student/student_profile.html",
        upcoming_sessions=upcoming_sessions,
        past_sessions=past_sessions,
        on_waiting_list=on_waiting_list,
        max_enrollments=utilities_dao.MAX_ENROLLMENTS
        )

@app.route("/manager_profile")
@login_required
def manager_profile():
    if current_user.role != "manager":
        return redirect(url_for("home"))

    stats = user_dao.get_manager_stats(current_user.email)

    # LISTE DI STUDENTI ISCRITTI E IN ATTESA PER OGNI SESSIONE DEL MANAGER
    session_classes = [dict(s) for s in cooking_class_dao.get_sessions_per_manager(current_user.email)]
    for session in session_classes:
        session["enrolled_students"] = user_dao.get_students_by_session_and_status(session["id"], "ENROLLED")
        session["waiting_students"] = user_dao.get_students_by_session_and_status(session["id"], "WAITING")
        session["available_spots"] = session["max_capacity"] - session["enrolled_count"]

    # CLASSI DEL MANAGER CON RATING, INGREDIENTI, SESSIONI E NUMERO DI STUDENTI IN ATTESA
    all_classes = [dict(c) for c in cooking_class_dao.get_all_classes_per_manager(current_user.email)]
    for cooking_class in all_classes:
        rating, _ = cooking_class_dao.get_class_rating(cooking_class["id"])
        cooking_class["avg_rating"] = rating
        cooking_class["ingredients"] = cooking_class_dao.get_ingredients_per_class(cooking_class["id"])
        cooking_class["sessions"] = [s for s in session_classes if s["COOKING_CLASS_id"] == cooking_class["id"]]
        cooking_class["waiting_total"] = sum(len(s["waiting_students"]) for s in cooking_class["sessions"])

    return render_template("manager/manager_profile.html", all_classes=all_classes, session_classes=session_classes, stats=stats)

# AZIONI DELLO STUDENTE
@app.route("/enroll/<int:session_id>", methods=["POST"])
@login_required
def enroll(session_id):
    if current_user.role != "student":
        return redirect(url_for("session_details", session_id=session_id))

    if booking_dao.check_existing_booking(current_user.email, session_id):
        flash("You are already registered for this session.", "info")
        return redirect(url_for("session_details", session_id=session_id))

    session_class = cooking_class_dao.get_single_session(session_id)
    if not session_class:
        flash("Session not found.", "danger")
        return redirect(url_for("home"))

    day = session_class["day_of_week"]
    time = session_class["start_time"]

    # NO ISCRIZIONI A SESSIONI GIA' IN CORSO O TERMINATE
    if utilities_dao.check_end_of_session(day, time, 0):
        flash("You cannot register for this session.", "warning")
        return redirect(url_for("session_details", session_id=session_id))

    # VINCOLI SUL NUMERO MASSIMO DI ISCRIZIONI E SUI CONFLITTI DI ORARIO
    max_reached = booking_dao.count_user_enrollments(current_user.email) >= utilities_dao.MAX_ENROLLMENTS
    has_conflict = booking_dao.check_time_conflict(current_user.email, session_id)

    # RITORNA None SE L'UTENTE NON PUO' ISCRIVERSI, ALTRIMENTI RITORNA "ENROLLED" O "WAITING"
    result_status = booking_dao.enroll_user_in_session(session_id, current_user.email, max_reached, has_conflict)

    if result_status is None:
        if max_reached:
            flash("You have reached the maximum number of enrollments.", "warning")
        elif has_conflict:
            flash("You have a time conflict with another session.", "warning")
    elif result_status == "ENROLLED":
        flash("Successfully enrolled in the session!", "success")
    elif result_status == "WAITING":
        flash("Class is full: you have been added to the waiting list.", "warning")

    return redirect(url_for("session_details", session_id=session_id))

@app.route("/delete_booking/<int:session_id>", methods=["POST"])
@login_required
def delete_booking(session_id):
    if current_user.role != "student":
        return redirect(url_for("session_details", session_id=session_id))

    user_status = booking_dao.check_existing_booking(current_user.email, session_id)
    if not user_status:
        return redirect(url_for("session_details", session_id=session_id))

    session_class = cooking_class_dao.get_single_session(session_id)
    day = session_class["day_of_week"]
    time = session_class["start_time"]

    # LIMITE 12H IMPEDISCE LA CANCELLAZIONE
    if user_status == "ENROLLED" and not utilities_dao.check_delete_eligibility(day, time):
        flash("You cannot delete your enrollment less than 12 hours before the session.", "warning")
        return redirect(url_for("session_details", session_id=session_id))

    booking_dao.delete_booking(current_user.email, session_id)
    
    if user_status == "ENROLLED":
        flash("Booking cancelled successfully.", "success")
    else:
        flash("You have left the waiting list.", "info")

    return redirect(url_for("session_details", session_id=session_id))

@app.route("/rate_session/<int:session_id>", methods=["POST"])
@login_required
def rate_session(session_id):
    if current_user.role != "student":
        return redirect(url_for("home"))

    # LO STUDENTE VALUTA SOLO A SESSIONE TERMINATA
    session_class = cooking_class_dao.get_single_session(session_id)
    if not utilities_dao.check_end_of_session(session_class["day_of_week"], session_class["start_time"], session_class["duration"]):
        flash("You can only rate sessions that have ended.", "warning")
        return redirect(url_for("student_profile"))

    rating = request.form.get("rating", type=int)
    current_rating = booking_dao.get_user_rating(current_user.email, session_id)

    if current_rating is None and rating and 1 <= rating <= 5:
        booking_dao.set_user_rating(current_user.email, session_id, rating)
        flash("Rating submitted successfully! Thank you for your feedback!", "success")

    return redirect(url_for("student_profile"))

# AZIONI DEL MANAGER
@app.route("/create_class", methods=["GET", "POST"])
@login_required
def create_class():
    if current_user.role != "manager":
        return redirect(url_for("home"))

    if request.method == "POST":
        title = request.form.get("title")
        cuisine = request.form.get("cuisine")
        duration = request.form.get("duration", type=int)
        difficulty = request.form.get("difficulty")
        chef_name = request.form.get("chef_name")
        description = request.form.get("description")
        dietary_category = request.form.get("dietary_category")
        raw_ingredients = request.form.get("ingredients", "")
        uploaded_photos = [
            request.files.get("photo_1"),
            request.files.get("photo_2"),
            request.files.get("photo_3")
        ]

        ingredients = [ingredient.strip() for ingredient in raw_ingredients.splitlines() if ingredient.strip()]

        # CONTROLLI BACK-END DEI FORMAT E DEI VINCOLI SUI CAMPI PER LA CREAZIONE DI UNA CLASSE
        error = utilities_dao.validate_class_format(title, cuisine, duration, difficulty, chef_name, description, dietary_category, ingredients)
        if error:
            return render_template("manager/create_class.html", error=error)

        # FOTO SALVATE CON NOME MANAGER + TIMESTAMP + NUMERO FOTO + NOME FILE, PER EVITARE CONFLITTI TRA MANAGER DIVERSI
        photos, photo_error = utilities_dao.save_class_photos(current_user.email, uploaded_photos)
        if photo_error:
            return render_template("manager/create_class.html", error=photo_error)

        cooking_class_dao.add_cooking_class(title, cuisine, duration, difficulty, chef_name, description,
                                            dietary_category, photos[0], photos[1], photos[2],
                                            current_user.email, ingredients)

        flash("Cooking class created successfully!", "success")
        return redirect(url_for("manager_profile"))

    return render_template("manager/create_class.html")

@app.route("/add_session/<int:class_id>", methods=["POST"])
@login_required
def add_session(class_id):
    if current_user.role != "manager":
        return redirect(url_for("home"))

    # CONTROLLO L'ID PROVENIENTE DAL MODAL CHE APPARTENGA AL MANAGER LOGGATO
    manager_classes = [c["id"] for c in cooking_class_dao.get_all_classes_per_manager(current_user.email)]
    if int(class_id) not in manager_classes:
        flash("Unauthorized class access.", "danger")
        return redirect(url_for("manager_profile"))
    
    day_of_week = request.form.get("day_of_week")
    start_time = request.form.get("start_time")
    kitchen = request.form.get("kitchen")
    max_capacity = request.form.get("max_capacity", type=int)

    # CONTROLLO BACK-END DEI FORMAT E DEI VINCOLI SUI CAMPI PER LA CREAZIONE DI UNA SESSIONE
    error = utilities_dao.validate_session_format(day_of_week, start_time, kitchen, max_capacity)

    if error:
        flash(error, "danger")
        return redirect(url_for("manager_profile"))

    cooking_class_dao.add_session(class_id, day_of_week, start_time, kitchen, max_capacity)
    flash("Session added successfully!", "success")
    return redirect(url_for("manager_profile"))

@app.route("/session/manage/<int:session_id>", methods=["POST"])
@login_required
def manage_session(session_id):
    if current_user.role != "manager":
        return redirect(url_for("home"))

    # SESSIONE CON STUDENTI ISCRITTI O IN ATTESA NON PUO' ESSERE MODIFICATA O ELIMINATA
    enrolled_students = user_dao.get_students_by_session_and_status(session_id, "ENROLLED")
    waiting_students = user_dao.get_students_by_session_and_status(session_id, "WAITING")

    if enrolled_students or waiting_students:
        return redirect(url_for("manager_profile"))

    action = request.form.get("action")

    if action == "delete":
        flash("Session deleted successfully!", "success")
        cooking_class_dao.delete_session(session_id)
        
    elif action == "save":
        day_of_week = request.form.get("day_of_week")
        start_time = request.form.get("start_time")
        kitchen = request.form.get("kitchen")
        max_capacity = request.form.get("max_capacity", type=int)

        error = utilities_dao.validate_session_format(day_of_week, start_time, kitchen, max_capacity)
        if error:
            flash(error, "danger")
            return redirect(url_for("manager_profile"))

        cooking_class_dao.update_session(session_id, day_of_week, start_time, kitchen, max_capacity)
        flash("Session updated successfully!", "success")
        
    return redirect(url_for("manager_profile"))

if __name__ == "__main__":
    app.run(debug=True)
