from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from telebot.types import ReplyKeyboardMarkup, KeyboardButton


def choice_role_keyboard():
    """
    Отправляет клавиатуру выбора роли

    :return:
    """

    # markup = InlineKeyboardMarkup()
    # markup.row_width = 2
    # markup.add(InlineKeyboardButton("Студент", callback_data="choice_student"),
    #            InlineKeyboardButton("Преподаватель", callback_data="choice_teacher"))

    markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)

    markup.add(KeyboardButton("Студент"))
    markup.add(KeyboardButton("Преподаватель"))

    return markup


def main_keyboard(user):
    """
    Возвращает главную клавиатуру

    :return:
    """

    markup = ReplyKeyboardMarkup(row_width=4)

    markup.add(KeyboardButton("Сегодня"), KeyboardButton("Завтра"))
    markup.add(KeyboardButton("Эта неделя"), KeyboardButton("Следующая неделя"))

    markup.add(KeyboardButton("Поиск"))

    markup.add(KeyboardButton("≡ Настройки"))

    return markup


def search_keyboard(user):
    """
    Возвращает меню поиска

    :param user:
    :return:
    """

    markup = ReplyKeyboardMarkup(row_width=2)

    if user.search_id:
        markup.add(KeyboardButton("Расписание на определенный день"))
    markup.add(KeyboardButton("Расписание другого преподавателя"))
    markup.add(KeyboardButton("Расписание другой группы"))

    markup.add(KeyboardButton("← Назад"))

    return markup


def settings_keyboard(user):
    """
    Возвращает клавиатуру настроек

    :param user:
    :return:
    """

    markup = ReplyKeyboardMarkup(row_width=2)

    if user.role == "teacher":
        markup.add(KeyboardButton("Выбрать другого преподавателя"))
    elif user.role == "student":
        markup.add(KeyboardButton("Изменить группу"))
    else:
        markup.add(KeyboardButton("Настроить бота"))
    markup.add(KeyboardButton("Группы в расписании"), KeyboardButton("Корпус в расписании"))
    if user.role and user.search_id and user.subscription_time is None and user.subscription_time == "CHANGES":
        markup.add(KeyboardButton("Подписаться на расписание"))
    else:
        if user.subscription_days is not None and user.subscription_days != "CHANGES":
            if user.role and user.search_id:
                markup.add(KeyboardButton("Изменить подписку на расписание"))
            markup.add(KeyboardButton("Отписаться от подписки на расписание"))
    markup.add(KeyboardButton("← Назад"))

    return markup
