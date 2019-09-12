import os


class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'telegram'
    SQLALCHEMY_DATABASE_URI = "postgresql://postgres:postgres@localhost:5432/telegram"
    SQLALCHEMY_TRACK_MODIFICATIONS = False


token = ""
proxy = "socks5://127.0.0.1:9050"
