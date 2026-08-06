from flask import Blueprint, render_template, redirect, url_for, request, session, flash
from flask_login import login_user, logout_user, login_required, UserMixin
from flask_bcrypt import Bcrypt
from database import users_collection
from bson.objectid import ObjectId

auth_bp = Blueprint("auth", __name__)
bcrypt = Bcrypt()  # Inizializzato qui, ma configurato in app.py


class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data["_id"])
        self.username = user_data["username"]
        self.role = user_data["role"]

    def get_id(self):
        return self.id


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user_data = users_collection.find_one({"username": username})

        if user_data and bcrypt.check_password_hash(user_data["password"], password):
            user = User(user_data)
            login_user(user)
            session["role"] = user.role
            session["username"] = user.username
            if user.role == "admin":
                return redirect(url_for("home.home"))
            elif user.role == "cameriere":
                return redirect(url_for("cameriere.cameriere_root"))
        else:
            flash("Credenziali non valide", "error")
    return render_template("login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    session.clear()
    return redirect(url_for("auth.login"))
