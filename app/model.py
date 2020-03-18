import logging
from typing import NamedTuple

import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Integer, String, Column, Boolean, MetaData

from app.dependency import Connection

metadata = MetaData()
db = declarative_base(metadata=metadata)

log = logging.getLogger(__name__)


class UserFilteredByTime(NamedTuple):
    id: int
    role: str
    subscription_days: str
    subscription_id: str
    show_location: bool
    show_groups: bool


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
                cls.role,
                cls.subscription_days,
                cls.subscription_id,
                cls.show_location,
                cls.show_groups,
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

    @classmethod
    def count_users(cls):
        """
        Количество записей в таблицей Users

        :return:
        """

        sql = sa.select([sa.func.count()]).select_from(cls.__table__)
        return sql


class Model:
    db: Connection

    def __init__(self, db: Connection):
        self.db = db

    async def get_user(self, id: int) -> User:
        """
        Получает данные User, если его нет создает

        :param id:
        :return:
        """

        async with self.db() as connection:
            user = await (await connection.execute(User.search_user(id))).fetchone()
            if user is None:
                await connection.execute(User.add_user(id))
                user = User(id=id)
            return user

    async def update_user(self, id: int, data: dict) -> None:
        """
        Обновляет данные пользователя поданные как словарь

        :param id:
        :param data:
        :return:
        """

        async with self.db() as connection:
            await connection.execute(User.update_user(id, data=data))

    async def get_count_users(self) -> int:
        """
        Считает кол-во пользователей в базе

        :return:
        """

        async with self.db() as connection:
            return (await (await connection.execute(User.count_users())).fetchone())[0]
