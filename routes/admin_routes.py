from flask import Blueprint, render_template, request, redirect, url_for, make_response
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
from flask import session
from datetime import datetime
from database.db import get_connection
from emails.email_service import send_email

admin_bp = Blueprint('admin', __name__)

@admin_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        email_verified = 0
        password = generate_password_hash(request.form.get("password"))
        created_at = datetime.now()
        try:
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
        except Exception as e:
            error_msg = f"An error occurred during registration: {e}"
            return render_template("register.html", error=error_msg)

    return render_template("register.html")
    
@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        try:
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM admins WHERE email = %s", (email,))
            user = cursor.fetchone()

            cursor.close()
            conn.close()

            if user and check_password_hash(user[4], password):
                try:
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute("UPDATE admins SET last_login = NOW() WHERE id = %s", (user[0],))
                    conn.commit()
                    cursor.close()
                    conn.close()
                except Exception as e:
                    error_msg = f"Failed to update last login: {e}"
                    return render_template("login.html", error=error_msg)

                session["user_id"] = user[0]
                session["user_name"] = user[1]
                return redirect(url_for("admin.dashboard"))
            else:
                return render_template("login.html", error="Invalid email or password")
        except Exception as e:
            error_msg = f"An error occurred during login: {e}"
            return render_template("login.html", error=error_msg)

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

@admin_bp.route("/logout", methods=["GET"])
def logout():
    session.clear()
    return redirect(url_for("admin.login"))

@admin_bp.route("/email-list", methods=["GET"])
def email_list():
    # check if user is logged in
    if "user_id" not in session:
        return redirect(url_for("admin.login"))

    try:
        # fetch email list from database users table
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE created_by = %s", (session["user_id"],))
        email_list = cursor.fetchall()
        cursor.close()
        conn.close()
        data = {
            "user_name": session["user_name"],
            "current_year": datetime.now().year,
            "email_list": email_list
        }
        return render_template("email_list.html", data=data)
    except Exception as e:
        error_msg = f"Failed to fetch email list: {e}"
        data = {
            "user_name": session.get("user_name", ""),
            "current_year": datetime.now().year,
            "email_list": []
        }
        return render_template("email_list.html", data=data, error=error_msg)

@admin_bp.route("/add-email", methods=["POST"])
def add_email():
    if "user_id" not in session:
        return redirect(url_for("admin.login"))

    email = request.form.get("email")
    name = request.form.get("name")
    created_at = datetime.now()

    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (email, name, created_at, created_by) VALUES (%s, %s, %s, %s)",
            (email, name, created_at, session["user_id"])
        )
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for("admin.email_list"))
    except Exception as e:
        error_msg = f"Failed to add email: {e}"
        data = {
            "user_name": session.get("user_name", ""),
            "current_year": datetime.now().year,
            "email_list": []
        }
        return render_template("email_list.html", data=data, error=error_msg)

@admin_bp.route("/edit-email/<int:email_id>", methods=["GET", "POST"])
def edit_email(email_id):
    if "user_id" not in session:
        return redirect(url_for("admin.login"))

    try:
        conn = get_connection()
        cursor = conn.cursor()

        if request.method == "POST":
            email = request.form.get("email")
            name = request.form.get("name")

            try:
                cursor.execute(
                    "UPDATE users SET email = %s, name = %s WHERE id = %s AND created_by = %s",
                    (email, name, email_id, session["user_id"])
                )
                conn.commit()
            except Exception as e:
                conn.rollback()
                error_msg = f"Failed to update email: {e}"
                return render_template("edit_email.html", data={
                    "user_name": session["user_name"],
                    "current_year": datetime.now().year,
                    "email_data": {"id": email_id, "email": email, "name": name}
                }, error=error_msg)
            finally:
                cursor.close()
                conn.close()

            return redirect(url_for("admin.email_list"))

        cursor.execute("SELECT * FROM users WHERE id = %s AND created_by = %s", (email_id, session["user_id"]))
        email_data = cursor.fetchone()
        cursor.close()
        conn.close()

        if not email_data:
            return redirect(url_for("admin.email_list"))

        data = {
            "user_name": session["user_name"],
            "current_year": datetime.now().year,
            "email_data": email_data
        }
        return render_template("edit_email.html", data=data)
    except Exception as e:
        error_msg = f"An error occurred: {e}"
        return render_template("edit_email.html", data={
            "user_name": session.get("user_name", ""),
            "current_year": datetime.now().year,
            "email_data": None
        }, error=error_msg)

@admin_bp.route("/delete-email/<int:email_id>", methods=["POST"])
def delete_email(email_id):
    if "user_id" not in session:
        return redirect(url_for("admin.login"))

    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM users WHERE id = %s AND created_by = %s",
            (email_id, session["user_id"])
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        error_msg = f"Failed to delete email: {e}"
        return render_template("email_list.html", data={
            "user_name": session.get("user_name", ""),
            "current_year": datetime.now().year,
            "email_list": []
        }, error=error_msg)
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for("admin.email_list"))

# import csv file and add to database
@admin_bp.route("/import-emails", methods=["GET", "POST"])
def import_emails():
    if "user_id" not in session:
        return redirect(url_for("admin.login"))

    if request.method == "POST":
        file = request.files.get("csv_file")
        # Check if a file was actually selected (browsers sometimes submit empty filenames)
        if not file or file.filename == '':
            return render_template("import_emails.html", data={
                "user_name": session.get("user_name", ""),
                "current_year": datetime.now().year
            }, error="No file selected")

        try:
            conn = get_connection()
            cursor = conn.cursor()

            # read csv file and insert into database
            import csv
            from io import StringIO

            stream = StringIO(file.stream.read().decode("utf-8-sig", errors="replace"), newline=None)
            csv_input = csv.reader(stream)

            header_skipped = False
            inserted_count = 0
            duplicate_count = 0
            errors_count = 0

            for row_num, row in enumerate(csv_input, start=1):
                if len(row) != 2:
                    continue 
                email, name = row

                email = email.strip()
                name = name.strip()
                
                if not header_skipped and email.lower() == 'email':
                    header_skipped = True
                    continue
                    
                if len(email) > 255:
                    errors_count += 1
                    continue

                created_at = datetime.now()

                if email_exists(email):
                    duplicate_count += 1
                    continue

                cursor.execute(
                    "INSERT INTO users (email, name, created_at, created_by) VALUES (%s, %s, %s, %s)",
                    (email, name, created_at, session.get("user_id"))
                )
                inserted_count += 1

            conn.commit()
        except Exception as e:
            conn.rollback()
            error_msg = f"Failed to import emails: {e}"
            return render_template("email_list.html", data={
                "user_name": session.get("user_name", ""),
                "current_year": datetime.now().year,
                "email_list": []
            }, error=error_msg)
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

        session["import_summary"] = {
            "inserted": inserted_count,
            "duplicates": duplicate_count,
            "errors": errors_count
        }
        return redirect(url_for("admin.email_list"))

    return render_template("import_emails.html", data={
        "user_name": session.get("user_name", ""),
        "current_year": datetime.now().year
    })

# check email exists in the database
def email_exists(email):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        return user is not None
    except Exception as e:
        print(f"An error occurred while checking email existence: {e}")
        return False

# Download Sample CSV
@admin_bp.route("/download-sample-csv", methods=["GET"])
def download_sample_csv():
    sample_csv = "email,name\nexample@example.com,Example User"
    response = make_response(sample_csv)
    response.headers["Content-Disposition"] = "attachment; filename=sample.csv"
    response.headers["Content-Type"] = "text/csv"
    return response

@admin_bp.route("/send-test-email", methods=["GET"])
def send_test_email():

    send_email(
        to="dilshanmadusanka20160@gmail.com",
        subject="PSAT Test Email",
        template="emails/test_email.html",
        name="Dilshan"
    )

    return "Email Sent Successfully!"