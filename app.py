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
    return render_template("public/index.html", session_classes=session_classes)

@app.route("/session_details/<int:session_id>")
def session_details(session_id):
    session_class = cooking_class_dao.get_single_session(session_id)
    ingredients = cooking_class_dao.get_ingredients(session_class["COOKING_CLASS_id"])
    available_spots = cooking_class_dao.get_available_spots(session_id)

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

    return render_template(
        "public/session_details.html",
        session_class=session_class,
        ingredients=ingredients,
        available_spots=available_spots,
        user_status=user_status,
        passed_session=passed_session,
        max_bookings_reached=max_bookings_reached,
        deletable=deletable
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

        already_enrolled = booking_dao.check_existing_booking(current_user.email, session_id)
        if already_enrolled:
            return redirect(url_for("session_details", session_id=session_id))

        total_enrollments = booking_dao.count_user_enrollments(current_user.email)
        available_spots = cooking_class_dao.get_available_spots(session_id)

        if available_spots > 0:
            if total_enrollments >= utilities_dao.MAX_ENROLLMENTS:
                return redirect(url_for("session_details", session_id=session_id))
            status = "ENROLLED"
        else:
            status = "WAITING"

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

        if not booking_dao.check_delete_eligibility(day, time):
            return redirect(url_for("session_details", session_id=session_id))

        success = booking_dao.delete_booking(current_user.email, session_id, day, time)

        if success:
            # TODO: LOGICA DI SCORRIMENTO DELLA LISTA DI ATTESA
            pass
    
    return redirect(url_for("session_details", session_id=session_id))

@app.route("/profile")
@login_required
def profile():
    if current_user.role == "student":
        # from here you will be redirected to the student profile route
        return redirect(url_for("student_profile"))
    elif current_user.role == "manager":
        return redirect(url_for("manager_profile"))
    else:
        return redirect(url_for("home"))

@app.route("/student_profile")
@login_required
def student_profile():
    booked_sessions = booking_dao.get_user_enrolled_sessions(current_user.email)
    return render_template("profiles/student_profile.html", booked_sessions=booked_sessions)

@app.route("/manager_profile")
@login_required
def manager_profile():
    #TODO
    pass


if __name__ == "__main__":
    app.run(debug=True)