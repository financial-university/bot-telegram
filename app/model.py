import logging

import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Integer, String, Column, Boolean, MetaData

from app.dependency import Connection

metadata = MetaData()
db = declarative_base(metadata=metadata)

log = logging.getLogger(__name__)


class User(db):
    __tablename__ = "users"
    __table__: sa.sql.schema.Table

    id = Column(Integer, primary_key=True, index=True, unique=True)
    login = Column(String(256), default=None)
    role = Column(String(256), default=None)
    menu = Column(String(256), default="START")
    search_id = Column(String(256), default=None)
    search_display = Column(String(256), default=None)
    search_additional = Column(String(256), default=None)
    subscription_time = Column(String(256), default=None)
    subscription_days = Column(String(256), default=None)
    subscription_id = Column(String(256), default=None)
    show_location = Column(Boolean, default=False)
    show_groups = Column(Boolean, default=False)

    @classmethod
    def filter_by_time(cls, time: str) -> sa.sql:
        """
        Ищет всех пользователей с временем подписки time

        :param time: время в формате 'hh:mm'
        :return:
        """

        return sa.select(
            [
                cls.id,
                cls.login,
                cls.role,
                cls.menu,
                cls.search_id,
                cls.search_display,
                cls.search_additional,
                cls.show_location,
                cls.show_groups,
                cls.subscription_days,
            ]
        ).where(cls.subscription_time == time)

    @classmethod
    def search_user(cls, id: int) -> sa.sql:
        """
        Ищет пользователя в базе по id

        :param id:
        :return:
        """

        return sa.select(["*"]).select_from(cls.__table__).where(cls.id == id)

    @classmethod
    def add_user(cls, id: int) -> sa.sql:
        """
        Добавляет нового пользователя

        :param id:
        :return:
        """

        return cls.__table__.insert().values([dict(id=id)])

    @classmethod
    def update_user(cls, id: int, data) -> sa.sql:
        """
        Обновляет поля пользователя поданные как kwargs

        :param id:
        :param data:
        :return:
        """

        sql = cls.__table__.update().values(data).where(cls.id == id)
        return sql


class Model:
    db: Connection

    def __init__(self, db: Connection):
        self.db = db

    async def get_user(self, id: int) -> User:
        """
        Получает юзера

        :param id:
        :return:
        """

        async with self.db() as connect:
            user = await (await connect.execute(User.search_user(id))).fetchone()
            if user is None:
                await connect.execute(User.add_user(id))
                user = User(id=id)
        return user

    async def update_user(self, id: int, data: dict) -> None:
        async with self.db() as conn:
            await conn.execute(User.update_user(id, data=data))


# class User(db.Model):
#     __tablename__ = "users"
#
#     id = db.Column(db.Integer, primary_key=True, index=True, unique=True)  # ID чата
#     login = db.Column(db.String(256), default=None)  # Ник человека
#     role = db.Column(
#         db.String(256), default=None
#     )  # Роль пользователя "teacher" или "student"
#     menu = db.Column(db.String(256), default="START")  # Текущее меню пользователя
#     search_id = db.Column(db.String(256), default=None)  # ID группы или преподавателя
#     search_display = db.Column(
#         db.String(256), default=None
#     )  # Название группы или ФИО преподавателя
#     search_additional = db.Column(db.String(256), default=None)  # Поле для поиска
#     subscription_time = db.Column(db.String(256), default=None)  # Поле времени подписки
#     subscription_days = db.Column(db.String(256), default=None)  # Поле дня подписки
#     subscription_id = db.Column(db.String(256), default=None)  # Поле id подписки
#     show_location = db.Column(
#         db.Boolean, default=False
#     )  # Поле отвечающее за показ расположения корпуса
#     show_groups = db.Column(db.Boolean, default=False)  # Поле отвечающее за показ групп
#
#     @classmethod
#     def search_user(cls, id: int) -> "User":
#         """
#         Ищет пользователя в базе по id
#
#         :param id:
#         :return:
#         """
#
#         user = db.session.query(cls).filter_by(id=id).first()
#         if user:
#             return user
#         user = cls(id=id)
#         db.session.add(user)
#         db.session.commit()
#         return user
#
#     @classmethod
#     def update_user(cls, user: "User", **data) -> "User":
#         """
#         Обновляет поля пользователя поданные как kwargs
#
#         :param user:
#         :param data:
#         :return:
#         """
#
#         for key, value in data["data"].items():
#             if hasattr(user, key):
#                 setattr(user, key, value)
#         db.session.commit()
#         return user
#
#     @classmethod
#     def filter_by_time(cls, time):
#         """
#         Ищет всех пользователей с временем подписки time
#
#         :param time:
#         :return:
#         """
#
#         return db.session.query(cls).filter_by(subscription_time=time).all()
#
#     @classmethod
#     def len(cls):
#         """
#         Возвращает кол-во записей в таблице
#
#         :return:
#         """
#
#         return db.session.query(cls).count()
