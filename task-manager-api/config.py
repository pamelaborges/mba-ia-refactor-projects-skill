import os

SECRET_KEY = os.environ["SECRET_KEY"]
DEBUG = os.environ.get("FLASK_DEBUG", "false").lower() == "true"

SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
