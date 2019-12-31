from app import db


class User(db.Model):
    __tablename__ = "users"
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_row_format": "DYNAMIC"}

    id = db.Column(db.Integer, primary_key=True, index=True, unique=True)  # ID чата
    login = db.Column(db.String(256), default=None)  # Ник человека
    role = db.Column(
        db.String(256), default=None
    )  # Роль пользователя "teacher" или "student"
    menu = db.Column(db.String(256), default="START")  # Текущее меню пользователя
    search_id = db.Column(db.String(256), default=None)  # ID группы или преподавателя
    search_display = db.Column(
        db.String(256), default=None
    )  # Название группы или ФИО преподавателя
    search_additional = db.Column(db.String(256), default=None)  # Поле для поиска
    subscription_time = db.Column(db.String(256), default=None)  # Поле времени подписки
    subscription_days = db.Column(db.String(256), default=None)  # Поле дня подписки
    subscription_id = db.Column(db.String(256), default=None)  # Поле id подписки
    show_location = db.Column(
        db.Boolean, default=False
    )  # Поле отвечающее за показ расположения корпуса
    show_groups = db.Column(db.Boolean, default=False)  # Поле отвечающее за показ групп

    @classmethod
    def search_user(cls, id: int) -> "User":
        """
        Ищет пользователя в базе по id

        :param id:
        :return:
        """

        user = db.session.query(cls).filter_by(id=id).first()
        if user:
            return user
        user = cls(id=id)
        db.session.add(user)
        db.session.commit()
        return user

    @classmethod
    def update_user(cls, user: "User", **data) -> "User":
        """
        Обновляет поля пользователя поданные как kwargs

        :param user:
        :param data:
        :return:
        """

        for key, value in data["data"].items():
            if hasattr(user, key):
                setattr(user, key, value)
        db.session.commit()
        return user

    @classmethod
    def filter_by_time(cls, time):
        """
        Ищет всех пользователей с временем подписки time

        :param time:
        :return:
        """

        return db.session.query(cls).filter_by(subscription_time=time).all()

    @classmethod
    def len(cls):
        """
        Возвращает кол-во записей в таблице

        :return:
        """

        return db.session.query(cls).count()
