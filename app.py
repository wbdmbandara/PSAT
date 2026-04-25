from flask import Flask, render_template, redirect, url_for, flash, request
from routes.admin_routes import admin_bp

app = Flask(__name__)

@app.route("/")
def home():
    return "PSAT System is running!"

app.register_blueprint(admin_bp, url_prefix="/admin")


# @app.route("/register", methods=["GET", "POST"])
# def register():
#     if request.method == "POST":
        

#         name = request.form.get("name")
#         email = request.form.get("email")
#         email_verified = 0
#         password = generate_password_hash(request.form.get("password"))
#         created_at = datetime.now()
#         conn = get_connection()
#         cursor = conn.cursor()

#         cursor.execute(
#             "INSERT INTO admins (name, email, email_verified, password, created_at) VALUES (%s, %s, %s, %s, %s)",
#             (name, email, email_verified, password, created_at)
#         )

#         conn.commit()
#         cursor.close()
#         conn.close()

#         return render_template("login.html?registered=true")

#     return render_template("register.html")

if __name__ == "__main__":
    app.run(debug=True)