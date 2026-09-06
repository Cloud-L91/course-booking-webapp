from flask import Flask, render_template, request, redirect, url_for
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from dao import cooking_class_dao, booking_dao, user_dao, utilities_dao
from user import User

app = Flask(__name__)
app.config["SECRET_KEY"] = "gli_occhi_del_cuore"

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@app.route("/")
def home():
    session_classes = cooking_class_dao.get_all_sessions()

    passed_sessions = []
    for session in session_classes:
        if booking_dao.check_end_of_session(session["day_of_week"], session["start_time"], session["duration"]):
            passed_sessions.append(session["id"])

    user_bookings = {}
    if current_user.is_authenticated:
        for session in session_classes:
            status = booking_dao.check_existing_booking(current_user.email, session["id"])
            if status:
                user_bookings[session["id"]] = status

    return render_template("public/index.html", session_classes=session_classes, user_bookings=user_bookings, passed_sessions=passed_sessions)

@app.route("/session_details/<int:session_id>")
def session_details(session_id):
    session_class = cooking_class_dao.get_single_session(session_id)
    ingredients = cooking_class_dao.get_ingredients_per_class(session_class["COOKING_CLASS_id"])
    available_spots = cooking_class_dao.get_available_spots(session_id)
    name_manager = user_dao.get_user_by_email(session_class["USER_email"])
    name_manager = f"{name_manager['first_name']} {name_manager['last_name']}"

    day = session_class["day_of_week"]
    time = session_class["start_time"]
    duration = session_class["duration"]
    deletable = booking_dao.check_delete_eligibility(day, time)
    passed_session = booking_dao.check_end_of_session(day, time, duration)

    user_status = None
    max_bookings_reached = False

    if current_user.is_authenticated and current_user.role == "student":
        user_status = booking_dao.check_existing_booking(current_user.email, session_id)
        total_enrollments = booking_dao.count_user_enrollments(current_user.email)
        max_bookings_reached = (total_enrollments >= utilities_dao.MAX_ENROLLMENTS)

    rating, total_votes = cooking_class_dao.get_class_rating(session_class["COOKING_CLASS_id"])

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
        name_manager=name_manager
        )

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        form_user = request.form.to_dict()
        email = form_user.get("email")
        password = form_user.get("password")

        db_user = user_dao.get_user_by_email(email)

        if not db_user:
            print("The user does not exist")
            return render_template("authentication/login.html", error="User not found")
        elif not check_password_hash(db_user["password_hash"], password):
            print("The password is incorrect")
            return render_template("authentication/login.html", error="Incorrect password")
        else:
            logged_in_user = User(
                email=db_user["email"],
                first_name=db_user["first_name"],
                last_name=db_user["last_name"],
                password=db_user["password_hash"],
                role=db_user["role"]
            )
            result = login_user(logged_in_user)
            print(result)
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
        form_data = request.form.to_dict()
        first_name = form_data.get("first_name")
        last_name = form_data.get("last_name")
        email = form_data.get("email")
        password = form_data.get("password")
        confirm_password = form_data.get("confirm_password")
        role = form_data.get("role")

        if not all([first_name, last_name, email, password, confirm_password, role]):
            return render_template("authentication/register.html", error="All fields are required")

        if password != confirm_password:
            return render_template("authentication/register.html", error="Passwords do not match")

        existing_user = user_dao.get_user_by_email(email)
        if existing_user:
            return render_template("authentication/register.html", error="User already exists")

        password_hash = generate_password_hash(password)
        success = user_dao.add_user(first_name, last_name, email, password_hash, role)
    
        if not success:
            return render_template("authentication/register.html", error="Failed to register user") 
        else:
            return redirect(url_for("login"))
    return render_template("authentication/register.html")

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

@app.route("/enroll/<int:session_id>", methods=["POST"])
@login_required
def enroll(session_id):
    if request.method == "POST":
        if current_user.role != "student":
            return redirect(url_for("session_details", session_id=session_id))

        if booking_dao.check_existing_booking(current_user.email, session_id):
            return redirect(url_for("session_details", session_id=session_id))

        total_enrollments = booking_dao.count_user_enrollments(current_user.email)
        available_spots = cooking_class_dao.get_available_spots(session_id)

        if available_spots <= 0:
            status = "WAITING"
        elif total_enrollments >= utilities_dao.MAX_ENROLLMENTS:
            return redirect(url_for("session_details", session_id=session_id))
        else:
            status = "ENROLLED"

        booking_dao.enroll_user_in_session(status, session_id, current_user.email)

    return redirect(url_for("session_details", session_id=session_id))

@app.route("/delete_booking/<int:session_id>", methods=["POST"])
@login_required
def delete_booking(session_id):
    if request.method == "POST":
        if current_user.role != "student":
            return redirect(url_for("session_details", session_id=session_id))

        session_class = cooking_class_dao.get_single_session(session_id)
        day = session_class["day_of_week"]
        time = session_class["start_time"]

        user_status = booking_dao.check_existing_booking(current_user.email, session_id)
        if not user_status:
            return redirect(url_for("session_details", session_id=session_id))

        if user_status == "ENROLLED" and not booking_dao.check_delete_eligibility(day, time):
            return redirect(url_for("session_details", session_id=session_id))

        success = booking_dao.delete_booking(current_user.email, session_id, day, time)

        if success:
            # TODO: LOGICA DI SCORRIMENTO DELLA LISTA DI ATTESA
            pass
    
    return redirect(url_for("session_details", session_id=session_id))

@app.route("/rate_session/<int:session_id>", methods=["POST"])
@login_required
def rate_session(session_id):
    if request.method == "POST":
        if current_user.role != "student":
            return redirect(url_for("session_details", session_id=session_id))

        rating = request.form.get("rating", type=int)
        current_rating = booking_dao.get_user_rating(current_user.email, session_id)

        if current_rating is None and rating and 1 <= rating <= 5:
            booking_dao.set_user_rating(current_user.email, session_id, rating)

    return redirect(url_for("student_profile"))

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
    all_sessions = booking_dao.get_user_enrolled_sessions(current_user.email)
    all_sessions.sort(key=lambda s: (utilities_dao.DAYS.index(s["day_of_week"]), s["start_time"]))

    upcoming_sessions = []
    past_sessions = []

    for session in all_sessions:
        day = session["day_of_week"]
        time = session["start_time"]
        duration = session["duration"]

        if booking_dao.check_end_of_session(day, time, duration):
            past_sessions.append(session)
        else:
            upcoming_sessions.append(session)

    return render_template("student/student_profile.html", upcoming_sessions=upcoming_sessions, past_sessions=past_sessions)

@app.route("/manager_profile")
@login_required
def manager_profile():
    all_classes = cooking_class_dao.get_all_classes_per_manager(current_user.email)
    session_classes = cooking_class_dao.get_sessions_per_manager(current_user.email)
    all_ingredients = cooking_class_dao.get_all_ingredients()
   
    return render_template("manager/manager_profile.html", all_classes=all_classes, session_classes=session_classes, all_ingredients=all_ingredients)

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
        raw_ingredients = request.form.get("ingredients","")

        ingredients = [ingredient.strip() for ingredient in raw_ingredients.splitlines() if ingredient.strip()]

        file_1 = request.files.get("photo_1")
        file_2 = request.files.get("photo_2")
        file_3 = request.files.get("photo_3")

        photo_1 = file_1.filename if file_1 else None
        photo_2 = file_2.filename if file_2 else None
        photo_3 = file_3.filename if file_3 else None

        for f in [file_1, file_2, file_3]:
            if f and f.filename:
                f.save(f"static/img/classes/{f.filename}")

        cooking_class_dao.add_cooking_class(title, cuisine, duration, difficulty, chef_name, description, dietary_category, photo_1, photo_2, photo_3, current_user.email, ingredients)

        return redirect(url_for("manager_profile"))

    return render_template("/manager/create_class.html")

@app.route("/create_session", methods=["GET", "POST"])
@login_required
def create_session():
    if current_user.role != "manager":
        return redirect(url_for("home"))

    return render_template("/manager/create_session.html")

if __name__ == "__main__":
    app.run(debug=True)