from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy import create_engine
from config import SQLALCHEMY_DATABASE_URI

engine = create_engine(SQLALCHEMY_DATABASE_URI, pool_size=30, max_overflow=10)

db = declarative_base()
session = scoped_session(sessionmaker(bind=engine))

from app import models
from app.models import User
from app.bot import *

# db.metadata.drop_all()
db.metadata.create_all(engine)
