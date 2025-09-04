import os
from dotenv import load_dotenv

# Load variables from .env
load_dotenv()

MYSQL_HOST = os.getenv("DB_HOST", "localhost")
MYSQL_USER = os.getenv("DB_USER", "root")
MYSQL_PASSWORD = os.getenv("DB_PASSWORD", "")
MYSQL_DB = os.getenv("DB_NAME", "lms_db")

SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey123")
