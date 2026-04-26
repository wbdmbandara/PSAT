from flask import Blueprint, render_template, request, redirect, url_for
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
from flask import session
from datetime import datetime
from database.db import get_connection

admin_bp = Blueprint('admin', __name__)

@admin_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        

        name = request.form.get("name")
        email = request.form.get("email")
        email_verified = 0
        password = generate_password_hash(request.form.get("password"))
        created_at = datetime.now()
        conn = get_connection()
        cursor = conn.cursor()

        # check if email already exists
        cursor.execute("SELECT * FROM admins WHERE email = %s", (email,))
        existing_user = cursor.fetchone()
        if existing_user:
            cursor.close()
            conn.close()
            return render_template("register.html", error="Email already exists")

        cursor.execute(
            "INSERT INTO admins (name, email, email_verified, password, created_at) VALUES (%s, %s, %s, %s, %s)",
            (name, email, email_verified, password, created_at)
        )

        conn.commit()
        cursor.close()
        conn.close()

        return render_template("login.html", success="Registration successful. Please log in.")

    return render_template("register.html")
    
@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM admins WHERE email = %s", (email,))
        user = cursor.fetchone()

        cursor.close()
        conn.close()

        if user and check_password_hash(user[4], password):
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE admins SET last_login = NOW() WHERE id = %s", (user[0],))
            conn.commit()
            cursor.close()
            conn.close()

            session["user_id"] = user[0]
            session["user_name"] = user[1]
            return redirect(url_for("admin.dashboard"))
        else:
            return render_template("login.html", error="Invalid email or password")

    return render_template("login.html")

@admin_bp.route("/dashboard", methods=["GET"])
def dashboard():
    # check if user is logged in
    if "user_id" not in session:
        return redirect(url_for("admin.login"))
    data = {
        "user_name": session["user_name"],
        "current_year": datetime.now().year,
    }
    return render_template("dashboard.html", data=data)
