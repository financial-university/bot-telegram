from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)

from app.models import User

# db.drop_all()
db.create_all()

from app import models, bot
from app.bot import *
