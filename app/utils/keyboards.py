from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from telebot.types import ReplyKeyboardMarkup, KeyboardButton


def choice_role_keyboard():
    """
    Отправляет клавиатуру выбора роли

    :return:
    """

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

    markup = ReplyKeyboardMarkup(one_time_keyboard=True, row_width=2)

    if user.search_id:
        markup.add(KeyboardButton("Расписание на определенный день"))
    markup.add(KeyboardButton("Расписание преподавателя"))
    markup.add(KeyboardButton("Расписание группы"))

    markup.add(KeyboardButton("← Назад"))

    return markup


def settings_keyboard(user):
    """
    Возвращает клавиатуру настроек

    :param user:
    :return:
    """

    markup = ReplyKeyboardMarkup(row_width=2)

    markup.add(KeyboardButton("Отображение расписания"))
    if user.role and user.search_id and (user.subscription_time is None or user.subscription_time == "CHANGES"):
        markup.add(KeyboardButton("Подписаться на расписание"))
    else:
        if user.subscription_days is not None and user.subscription_days != "CHANGES":
            if user.role and user.search_id:
                markup.add(KeyboardButton("Изменить подписку на расписание"))
            markup.add(KeyboardButton("Отписаться от подписки на расписание"))
    markup.add(KeyboardButton("← Назад"))

    return markup


def subscribe_choice_time_keyboard():
    """
    Возвращает клавиатуру выбора времени подписки

    :return:
    """

    markup = ReplyKeyboardMarkup(row_width=3)

    markup.add(KeyboardButton("7:00"), KeyboardButton("7:30"), KeyboardButton("8:00"))
    markup.add(KeyboardButton("9:00"), KeyboardButton("10:40"), KeyboardButton("12:05"))
    markup.add(KeyboardButton("20:00"), KeyboardButton("21:30"), KeyboardButton("22:00"))
    markup.add(KeyboardButton("Отмена"))

    return markup


def choice_day_keyboard():
    """
    Возвращает клавиатуру выбора дня подписки

    :return:
    """

    markup = ReplyKeyboardMarkup(row_width=3)

    markup.add(KeyboardButton("Текущий день"), KeyboardButton("Следующий день"))
    markup.add(KeyboardButton("Текущий и следующий день"))
    markup.add(KeyboardButton("Эта неделя"), KeyboardButton("Следующая неделя"))
    markup.add(KeyboardButton("Отмена"))

    return markup


def display_in_schedule_keyboard(user):
    """
    Возвращает inline клавиатуру выбора показа строк в расписании

    :return:
    """

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(f"Группы в расписании {'✅' if user.show_groups is True else '❌'}",
                                    callback_data="groups_in_schedule"))
    markup.add(InlineKeyboardButton(f"Корпус в расписании {'✅' if user.show_location is True else '❌'}",
                                    callback_data="location_in_schedule"))

    return markup
