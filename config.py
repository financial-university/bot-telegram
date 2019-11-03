import os


class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'bot'
    SQLALCHEMY_DATABASE_URI = f"mysql+mysqlconnector://user:pass@ip/db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False


token = ""
url = "https://url/telegram/"
proxy = ""
