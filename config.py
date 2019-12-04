import os


class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'bot'
    SQLALCHEMY_DATABASE_URI = f"mysql+mysqlconnector://log:pass@localhost/telegram"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DB_SETTINGS = {'pool_recycle': 1800}  # MySQL


API_TOKEN = ""

WEBHOOK_HOST = "url"
WEBHOOK_PORT = 8443
WEBHOOK_LISTEN = "0.0.0.0"

WEBHOOK_URL_BASE = f"https://{WEBHOOK_HOST}"
WEBHOOK_URL_PATH = f"/{API_TOKEN}/"
