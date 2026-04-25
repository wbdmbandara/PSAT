from flask import Blueprint, render_template, request, redirect, url_for
from werkzeug.security import generate_password_hash
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

        return render_template("login.html?registered=true")

    return render_template("register.html")
    