from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from config import Config, url, token

app = Flask(__name__)
app.config.from_object(Config)
app.config['SQLALCHEMY_POOL_RECYCLE'] = 600

db = SQLAlchemy(app)

from app.models import User

# db.drop_all()
db.create_all()

# from telebot import apihelper
# apihelper.proxy = {'http': proxy, 'https': proxy}

from app import models, bot
from app.bot import *


@app.route(f"/telegram/{token}", methods=['POST'])
def get_message():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "!", 200


@app.route("/telegram/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url=f"{url}{token}")
    return "!", 200
