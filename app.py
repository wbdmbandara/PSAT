from flask import Flask, render_template, redirect, url_for, flash, request
from routes.admin_routes import admin_bp
from config import Config
from extensions import mail
import os

app = Flask(__name__)
app.config.from_object(Config)

# initialize mail
mail.init_app(app)

app.config["SECRET_KEY"] = os.urandom(24)

@app.route("/")
def home():
    return "PSAT System is running!"

app.register_blueprint(admin_bp, url_prefix="/admin")

if __name__ == "__main__":
    app.run(debug=True)