from flask import Flask, render_template, request, redirect, url_for
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from dao import cooking_class_dao, user_dao
from user import User

app = Flask(__name__)
app.config["SECRET_KEY"] = "gli_occhi_del_cuore"

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

FIRST_DAY = "Monday"
LAST_DAY = "Sunday"
CURRENT_DAY = "Wednesday"
CURRENT_TIME = "13:00"

@app.route("/")
def home():
    session_classes = cooking_class_dao.get_all_sessions()
    return render_template("public/index.html", session_classes=session_classes)

@app.route("/session_details/<int:session_id>")
def session_details(session_id):
    session_class = cooking_class_dao.get_single_session(session_id)
    ingredients = cooking_class_dao.get_ingredients(session_class["COOKING_CLASS_id"])
    available_spots = cooking_class_dao.get_available_spots(session_id)

    return render_template("public/session_details.html", session_class=session_class, ingredients=ingredients, available_spots=available_spots)

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
            login_user(logged_in_user)
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
        username = form_data.get("username")
        email = form_data.get("email")
        password = form_data.get("password")

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

if __name__ == "__main__":
    app.run(debug=True)