from flask import Flask, render_template, flash
from routes.admin_routes import admin_bp
from routes.track_routes import track_bp
from config import Config
from extensions import mail
from database.db import ensure_schema
import os
from datetime import datetime

app = Flask(__name__)

# 1. Load configuration and set secret key
app.config.from_object(Config)
app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]

# 2. Initialize extensions
mail.init_app(app)

# 3. Ensure database schema is up to date
try:
    ensure_schema()
except Exception as e:
    print("Database initialization failed:", e)

# 3. Register Blueprints (Cleanly registered once)
app.register_blueprint(admin_bp, url_prefix="/admin")
app.register_blueprint(track_bp)

@app.route("/")
def home():
    return render_template("home.html", current_year=datetime.now().year)

@app.route("/health")
def health():
    return "OK", 200
    
# 4. Global Error Handlers
@app.errorhandler(404)
def page_not_found(e):
    data = {"current_year": datetime.now().year}
    return render_template("404.html", data=data), 404

if __name__ == "__main__":
    # Use Railway's PORT variable, or default to 5000 for local testing
    port = int(os.environ.get("PORT", 5000))
    # Bind to 0.0.0.0 to allow external connections
    app.run(host="0.0.0.0", port=port)