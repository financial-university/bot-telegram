import os


class Config(object):
    SECRET_KEY = os.environ.get("SECRET_KEY") or "secret"
    # SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'server.db')
    SQLALCHEMY_DATABASE_URI = f"mysql+mysqlconnector://log:pass@localhost/db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DB_SETTINGS = {"pool_recycle": 1800}  # MySQL
    # DB_SETTINGS = {'pool_size': 30, 'max_overflow': 10} # PostgeSQL


API_TOKEN = "token"

WEBHOOK_HOST = "url"
WEBHOOK_PORT = 8443
WEBHOOK_LISTEN = "0.0.0.0"

WEBHOOK_URL_BASE = f"https://{WEBHOOK_HOST}"
WEBHOOK_URL_PATH = f"/{API_TOKEN}/"
