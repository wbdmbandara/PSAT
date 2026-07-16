import uuid
import csv
from io import StringIO
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, make_response, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from database.db import get_connection
from emails.email_service import send_email, send_simulation_email
from flask_paginate import Pagination, get_page_parameter

# 1. THIS DEFINITION MUST COME BEFORE ANY ROUTES
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
    if "user_id" not in session:
        return redirect(url_for("admin.login"))
        
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # 1. Total Emails Sent
        cursor.execute("SELECT COUNT(*) FROM email_logs")
        total_emails = cursor.fetchone()[0] or 0

        # 2. Total Clicks
        cursor.execute("SELECT COUNT(*) FROM click_logs")
        total_clicks = cursor.fetchone()[0] or 0

        # 3. Total Compromises (Credential Submissions)
        cursor.execute("SELECT COUNT(*) FROM login_attempts")
        total_compromises = cursor.fetchone()[0] or 0

        # 4. Active Campaigns
        cursor.execute("SELECT COUNT(*) FROM campaigns")
        active_campaigns = cursor.fetchone()[0] or 0

        # 5. Calculate Rates (Avoid division by zero)
        click_rate = round((total_clicks / total_emails * 100), 1) if total_emails > 0 else 0.0
        compromise_rate = round((total_compromises / total_emails * 100), 1) if total_emails > 0 else 0.0

        # 6. Fetch Recent Activity (Combine tables, sort by most recent)
        recent_activity_query = """
            SELECT 'Simulation Dispatched' as type, sent_time as time, user_id FROM email_logs
            UNION ALL
            SELECT 'Link Clicked' as type, click_time as time, user_id FROM click_logs
            UNION ALL
            SELECT 'Credential Submitted' as type, attempt_time as time, user_id FROM login_attempts
            ORDER BY time DESC LIMIT 4
        """
        cursor.execute(recent_activity_query)
        recent_activities = cursor.fetchall()
        
        # 7. Basic Chart Data setup (using the current stats as the latest data point)
        current_month = datetime.now().strftime("%b")

        data = {
            "user_name": session.get("user_name", "Admin"),
            "current_year": datetime.now().year,
            "total_emails": total_emails,
            "click_rate": click_rate,
            "compromise_rate": compromise_rate,
            "active_campaigns": active_campaigns,
            "recent_activities": recent_activities,
            # Chart datasets (Dummy historical data + real current data)
            "chart_labels": ['Jan', 'Feb', 'Mar', 'Apr', 'May', current_month],
            "chart_clicks": [0, 0, 0, 0, 0, click_rate], 
            "chart_comps": [0, 0, 0, 0, 0, compromise_rate]
        }

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"Dashboard Database Error: {e}")
        # Fallback empty data to prevent the app from crashing if DB fails
        data = {
            "user_name": session.get("user_name", "Admin"),
            "current_year": datetime.now().year,
            "total_emails": 0, "click_rate": 0.0, "compromise_rate": 0.0, "active_campaigns": 0,
            "recent_activities": [],
            "chart_labels": ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
            "chart_clicks": [0,0,0,0,0,0], "chart_comps": [0,0,0,0,0,0]
        }

    return render_template("dashboard.html", data=data)

@admin_bp.route("/logout", methods=["GET"])
def logout():
    session.clear()
    return redirect(url_for("admin.login"))

@admin_bp.route("/email-list", methods=["GET"])
def email_list():
    if "user_id" not in session:
        return redirect(url_for("admin.login"))

    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        page = request.args.get("page", type=int, default=1)   # fixed explicit page param
        per_page = 10
        offset = (page - 1) * per_page
        search_query = request.args.get("search", "", type=str).strip()

        if search_query:
            search_pattern = f"%{search_query}%"

            cursor.execute(
                """
                SELECT COUNT(*)
                FROM users
                WHERE created_by = %s
                  AND (email LIKE %s OR name LIKE %s)
                """,
                (session["user_id"], search_pattern, search_pattern),
            )
            total_records = cursor.fetchone()[0]

            cursor.execute(
                """
                SELECT *
                FROM users
                WHERE created_by = %s
                  AND (email LIKE %s OR name LIKE %s)
                ORDER BY id DESC
                LIMIT %s OFFSET %s
                """,
                (session["user_id"], search_pattern, search_pattern, per_page, offset),
            )
            list_data = cursor.fetchall()
        else:
            cursor.execute(
                "SELECT COUNT(*) FROM users WHERE created_by = %s",
                (session["user_id"],),
            )
            total_records = cursor.fetchone()[0]

            cursor.execute(
                """
                SELECT *
                FROM users
                WHERE created_by = %s
                ORDER BY id DESC
                LIMIT %s OFFSET %s
                """,
                (session["user_id"], per_page, offset),
            )
            list_data = cursor.fetchall()

        pagination = Pagination(
            page=page,
            total=total_records,
            per_page=per_page,
            css_framework="bootstrap5",
            show_single_page=True,
            record_name="users",
        )

        data = {
            "user_name": session["user_name"],
            "current_year": datetime.now().year,
            "email_list": list_data,
            "pagination": pagination,
            "search_query": search_query,
        }
        return render_template("email_list.html", data=data)

    except Exception as e:
        flash(f"Failed to fetch email list: {e}", "danger")
        data = {
            "user_name": session.get("user_name", ""),
            "current_year": datetime.now().year,
            "email_list": [],
            "pagination": None,
            "search_query": request.args.get("search", "")
        }
        return render_template("email_list.html", data=data)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@admin_bp.route("/add-email", methods=["POST"])
def add_email():
    if "user_id" not in session:
        return redirect(url_for("admin.login"))

    email = request.form.get("email")
    name = request.form.get("name")
    created_at = datetime.now()

    if(email_exists(email)):
        flash(f"Email {email} already exists.", "warning")
        return redirect(url_for("admin.email_list"))

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
        flash(f"Email {email} added successfully.", "success")
        return redirect(url_for("admin.email_list"))
    except Exception as e:
        error_msg = f"Failed to add email: {e}"
        data = {
            "user_name": session.get("user_name", ""),
            "current_year": datetime.now().year,
            "email_list": []
        }
        flash(error_msg, "danger")
        return render_template("email_list.html", data=data)

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
                # duplicate email check
                cursor.execute("SELECT * FROM users WHERE email = %s AND id != %s AND created_by = %s", (email, email_id, session["user_id"]))
                if cursor.fetchone():
                    flash(f"Email {email} already exists.", "warning")
                    return redirect(url_for("admin.email_list"))

                cursor.execute(
                    "UPDATE users SET email = %s, name = %s WHERE id = %s AND created_by = %s",
                    (email, name, email_id, session["user_id"])
                )
                conn.commit()
                flash(f"Email '{email}' updated successfully.", "success")
            except Exception as e:
                conn.rollback()
                error_msg = f"Failed to update email: {e}"
                flash(error_msg, "danger")
                return render_template("edit_email.html", data={
                    "user_name": session["user_name"],
                    "current_year": datetime.now().year,
                    "email_data": {"id": email_id, "email": email, "name": name}
                })
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
        flash(error_msg, "danger")
        return render_template("edit_email.html", data={
            "user_name": session.get("user_name", ""),
            "current_year": datetime.now().year,
            "email_data": None
        })

@admin_bp.route("/delete-email/<int:email_id>", methods=["POST"])
def delete_email(email_id):
    if "user_id" not in session:
        return redirect(url_for("admin.login"))

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE id = %s AND created_by = %s", (email_id, session["user_id"]))
        email_data = cursor.fetchone()

        cursor.execute(
            "DELETE FROM users WHERE id = %s AND created_by = %s",
            (email_id, session["user_id"])
        )
        conn.commit()
        flash(f"Email '{email_data[1]}' deleted successfully.", "success")
    except Exception as e:
        conn.rollback()
        error_code = e.args[0] if len(e.args) > 0 else None
        if error_code == 1451:
            error_msg = "Cannot delete email because it is linked to other records (e.g., email logs)."
        else:
            error_msg = f"Failed to delete email: {e}"
        flash(error_msg, "danger")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for("admin.email_list"))

@admin_bp.route("/import-emails", methods=["GET", "POST"])
def import_emails():
    if "user_id" not in session:
        return redirect(url_for("admin.login"))

    if request.method == "POST":
        file = request.files.get("csv_file")
        if not file or file.filename == '':
            flash("No file selected for uploading.", "danger")
            return render_template("import_emails.html", data={
                "user_name": session.get("user_name", ""),
                "current_year": datetime.now().year
            })

        try:
            conn = get_connection()
            cursor = conn.cursor()

            stream = StringIO(file.stream.read().decode("utf-8-sig", errors="replace"), newline=None)
            csv_input = csv.reader(stream)

            header_skipped = False
            inserted_count = 0
            duplicate_count = 0
            errors_count = 0

            for row in csv_input:
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
            flash(error_msg, "danger")
            return render_template("email_list.html", data={
                "user_name": session.get("user_name", ""),
                "current_year": datetime.now().year,
                "email_list": []
            })
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

        flash(f"Import Summary: {inserted_count} inserted, {duplicate_count} duplicates skipped, {errors_count} errors.", "info")
        return redirect(url_for("admin.email_list"))

    return render_template("import_emails.html", data={
        "user_name": session.get("user_name", ""),
        "current_year": datetime.now().year
    })

def email_exists(email):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = %s AND created_by = %s", (email, session["user_id"]))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        return user is not None
    except Exception as e:
        print(f"An error occurred while checking email existence: {e}")
        return False

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

# 2. THIS NEW DISPATCH TRIGGER ROUTE SITS COMFORTABLY AT THE BOTTOM
@admin_bp.route('/send-simulation/<int:email_id>', methods=['POST'])
def trigger_simulation(email_id):
    """
    Fetches the selected email, records the dispatch in the email_logs table,
    and sends the simulation email using the user's database ID as the identifier.
    """
    if "user_id" not in session:
        return redirect(url_for("admin.login"))

    conn = get_connection()
    try:
        cursor = conn.cursor()
        
        cursor.execute("SELECT email FROM users WHERE id = %s", (email_id,))
        target = cursor.fetchone()
        
        if not target:
            flash("Target user not found.", "danger")
            cursor.close()
            conn.close()
            return redirect(url_for('admin.email_list'))
            
        target_email = target[0]

        cursor.execute("SELECT id FROM campaigns LIMIT 1")
        campaign = cursor.fetchone()
        
        if campaign:
            campaign_id = campaign[0]
        else:
            cursor.execute(
                "INSERT INTO campaigns (campaign_name, description) VALUES (%s, %s)",
                ("Default Awareness Campaign", "Automated tracking campaign for baseline testing")
            )
            conn.commit()
            campaign_id = cursor.lastrowid

        query = """
            INSERT INTO email_logs (campaign_id, user_id, sent_time, status) 
            VALUES (%s, %s, NOW(), 'Sent')
        """
        cursor.execute(query, (campaign_id, email_id))
        conn.commit()
        cursor.close()
        conn.close()

        success = send_simulation_email(target_email, email_id)
        
        if success:
            flash(f"Simulation template safely dispatched to {target_email}!", "success")
        else:
            flash("Database log recorded, but SMTP server failed to deliver email.", "warning")

    except Exception as e:
        print(f"Database tracking compilation failed: {str(e)}")
        flash("Internal tracker registration logic failure.", "danger")
        if conn:
            conn.close()

    return redirect(url_for('admin.email_list'))

@admin_bp.route("/report/<report_type>", methods=["GET"])
def view_report(report_type):
    if "user_id" not in session:
        return redirect(url_for("admin.login"))
    
    conn = get_connection()
    cursor = conn.cursor()
    
    title = ""
    headers = []
    rows = []
    
    try:
        if report_type == "emails":
            title = "Email Dispatch Report"
            headers = ["Name", "Email Address", "Sent Time", "Status"]
            cursor.execute("""
                SELECT u.name, u.email, el.sent_time, el.status 
                FROM email_logs el 
                JOIN users u ON el.user_id = u.id 
                ORDER BY el.sent_time DESC
            """)
            rows = cursor.fetchall()
            
        elif report_type == "clicks":
            title = "Overall Click Rate Report"
            headers = ["Name", "Email Address", "Click Time", "IP Address"]
            cursor.execute("""
                SELECT u.name, u.email, cl.click_time, cl.ip_address 
                FROM click_logs cl 
                JOIN users u ON cl.user_id = u.id 
                ORDER BY cl.click_time DESC
            """)
            rows = cursor.fetchall()
            
        elif report_type == "logins":
            title = "Compromise (Login Attempts) Report"
            headers = ["Name", "Email Address", "Attempt Time", "IP Address"]
            cursor.execute("""
                SELECT u.name, u.email, la.attempt_time, la.ip_address 
                FROM login_attempts la 
                JOIN users u ON la.user_id = u.id 
                ORDER BY la.attempt_time DESC
            """)
            rows = cursor.fetchall()      
            
        elif report_type == "campaigns":
            title = "Campaign Overview Report"
            headers = ["Campaign ID", "Campaign Name", "Status", "Template Used"]
            cursor.execute("""
                SELECT id, campaign_name, status, template_name 
                FROM campaigns 
                ORDER BY id DESC
            """)
            rows = cursor.fetchall()
            
        else:
            return redirect(url_for("admin.dashboard"))
            
    except Exception as e:
        print(f"Error fetching report: {e}")
    finally:
        cursor.close()
        conn.close()
    
    data = {
        "user_name": session.get("user_name", "Admin"),
        "current_year": datetime.now().year,
        "title": title,
        "headers": headers,
        "rows": rows
    }
    return render_template("report.html", data=data)

@admin_bp.route("/create-campaign", methods=["GET", "POST"])
def create_campaign():
    if "user_id" not in session:
        return redirect(url_for("admin.login"))

    conn = get_connection()
    cursor = conn.cursor()

    if request.method == "POST":
        name = request.form.get("campaign_name")
        desc = request.form.get("description")
        template = request.form.get("template_name")
        target_ids = request.form.getlist("target_users") # Gets list of checked user IDs

        try:
            # 1. Create the campaign
            cursor.execute(
                "INSERT INTO campaigns (campaign_name, description, status, template_name) VALUES (%s, %s, %s, %s)",
                (name, desc, 'Draft', template)
            )
            campaign_id = cursor.lastrowid

            # 2. Link targets by creating 'Pending' email logs
            for uid in target_ids:
                cursor.execute(
                    "INSERT INTO email_logs (campaign_id, user_id, status) VALUES (%s, %s, 'Pending')",
                    (campaign_id, uid)
                )
            
            conn.commit()
            # Note: For now we redirect to dashboard. Later this will go to a 'Campaign List' page.
            return redirect(url_for("admin.dashboard")) 
        except Exception as e:
            conn.rollback()
            print(f"Error creating campaign: {e}")
            # Fall through to re-render the form with an error (you can add flash messages later)
        
    # GET request: Fetch users for the target checklist
    try:
        cursor.execute("SELECT id, name, email FROM users WHERE created_by = %s", (session["user_id"],))
        users_list = cursor.fetchall()
    except Exception as e:
        print(f"Error fetching users: {e}")
        users_list = []
    finally:
        cursor.close()
        conn.close()

    data = {
        "user_name": session.get("user_name", "Admin"),
        "current_year": datetime.now().year,
        "users": users_list
    }
    return render_template("create_campaign.html", data=data)

