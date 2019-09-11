from app import db, session
from sqlalchemy import Integer, String, Column, Boolean


class User(db):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, unique=True)  # ID записи в БД
    role = Column(String, default=None)  # Роль пользователя "teacher" или "student"
    menu = Column(String, default="START")  # Текущее меню пользователя
    search_id = Column(String, default=None)  # ID группы или преподавателя
    search_display = Column(String, default=None)  # Название группы или ФИО преподавателя
    search_day = Column(String, default=None)  # Поле для поиска определенного дня
    subscription_time = Column(String, default=None)   # Поле времени подписки
    subscription_days = Column(String, default=None)   # Поле дня подписки
    subscription_id = Column(String, default=None)    # Поле id подписки
    show_location = Column(Boolean, default=False)    # Поле отвечающее за показ расположения корпуса
    show_groups = Column(Boolean, default=False)    # Поле отвечающее за показ групп

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
