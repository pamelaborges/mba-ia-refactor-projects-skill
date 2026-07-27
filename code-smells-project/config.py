import os

SECRET_KEY = os.environ["SECRET_KEY"]
ADMIN_TOKEN = os.environ["ADMIN_TOKEN"]
DEBUG = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
ENV = os.environ.get("ENV", "development")
ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "*").split(",")
DB_PATH = os.environ.get("DB_PATH", "loja.db")
