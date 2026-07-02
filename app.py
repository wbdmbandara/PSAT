from flask import Flask, render_template
from routes.admin_routes import admin_bp
from routes.track_routes import track_bp
from config import Config
from extensions import mail
import os

app = Flask(__name__)

# 1. Load configuration and set secret key
app.config.from_object(Config)
app.config["SECRET_KEY"] = os.urandom(24)

# 2. Initialize extensions
mail.init_app(app)

# 3. Register Blueprints (Cleanly registered once)
app.register_blueprint(admin_bp, url_prefix="/admin")
app.register_blueprint(track_bp)

@app.route("/")
def home():
    return "PSAT System is running!"

# 4. Global Error Handlers
@app.errorhandler(404)
def page_not_found(e):
    data = {"current_year": __import__("datetime").datetime.now().year}
    return render_template("404.html", data=data), 404

if __name__ == "__main__":
    app.run(debug=True)