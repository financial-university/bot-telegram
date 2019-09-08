from app import db, session
from sqlalchemy import Integer, String, Column, Boolean


class User(db):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, unique=True)
    role = Column(String, default=None)
    menu = Column(String, default="START")
    search_id = Column(String, default=None)
    subscription_time = Column(String, default=None)
    subscription_days = Column(String, default=None)
    subscription_group = Column(String, default=None)
    show_location = Column(Boolean, default=False)
    show_groups = Column(Boolean, default=False)

    @classmethod
    def search_user(cls, id: int) -> 'User':
        """
        Ищет пользователя в базе по id

        :param id:
        :return:
        """

        user = session.query(cls).filter_by(id=id).first()
        if user:
            return user
        user = cls(id=id)
        session.add(user)
        session.commit()
        return user

    @classmethod
    def update_user(cls, user: 'User', **data) -> 'User':
        """
        Обновляет поля пользователя поданные как kwargs

        :param user:
        :param data:
        :return:
        """

        for key, value in data['data'].items():
            if hasattr(user, key):
                setattr(user, key, value)
        session.commit()
        return user