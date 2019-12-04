from flask import Flask, request, abort
from flask_sqlalchemy import SQLAlchemy
from threading import Thread
from config import Config, WEBHOOK_LISTEN, WEBHOOK_PORT, WEBHOOK_URL_BASE, WEBHOOK_URL_PATH

app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)

from app.models import User

# db.drop_all()
db.create_all()

from app import models, bot
from app.bot import *


@app.route("/", methods=["GET", "HEAD"])
def index():
    return ""


@app.route(WEBHOOK_URL_PATH, methods=["POST"])
def webhook():
    if request.headers.get("content-type") == "application/json":
        json_string = request.get_data().decode("utf-8")
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ""
    else:
        abort(403)


bot.remove_webhook()

time.sleep(0.1)

bot.set_webhook(url=WEBHOOK_URL_BASE + WEBHOOK_URL_PATH)

workers_flow = Thread(target=start_workers).start()

app.run(host=WEBHOOK_LISTEN,
        port=WEBHOOK_PORT,
        debug=True)
