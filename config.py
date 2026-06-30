import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    MAIL_SERVER = os.getenv("SMTP_HOST")
    MAIL_PORT = int(os.getenv("SMTP_PORT", 587))

    MAIL_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
    MAIL_USE_SSL = os.getenv("SMTP_USE_SSL", "false").lower() == "true"

    MAIL_USERNAME = os.getenv("SMTP_USER")
    MAIL_PASSWORD = os.getenv("SMTP_PASSWORD")

    MAIL_DEFAULT_SENDER = os.getenv("SMTP_SENDER", os.getenv("SMTP_USER"))