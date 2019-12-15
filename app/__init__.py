import logging
import time
from threading import Thread

import telebot
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy

from config import Config, WEBHOOK_LISTEN, WEBHOOK_PORT, WEBHOOK_URL_BASE, WEBHOOK_URL_PATH

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)

from app.models import User

# db.drop_all()
db.create_all()

from app import models
from app.bot import start_workers, bot


@app.route('/', methods=['GET', 'HEAD'])
def index():
    return ''


@app.route(WEBHOOK_URL_PATH, methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    else:
        abort(403)


@app.route('/api/users_count', methods=['GET'])
def users_count():
    return jsonify(count=models.User.len())


# bot.remove_webhook()

time.sleep(1)

bot.set_webhook(url=WEBHOOK_URL_BASE + WEBHOOK_URL_PATH)

workers_flow = Thread(target=start_workers).start()

app.run(host=WEBHOOK_LISTEN,
        port=WEBHOOK_PORT,
        debug=True)
