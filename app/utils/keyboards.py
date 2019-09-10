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
    Отправляет главную клавиатуру для студента

    :return:
    """

    markup = ReplyKeyboardMarkup(row_width=2)

    markup.add(KeyboardButton("Сегодня"), KeyboardButton("Завтра"))
    markup.add(KeyboardButton("Сегодня и завтра"))
    markup.add(KeyboardButton("Эта неделя"), KeyboardButton("Следующая неделя"))
    markup.add(KeyboardButton("Расписание на определенный день"))
    if user.role == "student":
        markup.add(KeyboardButton("Поиск расписания преподавателя"))
    elif user.role == "teacher":
        markup.add(KeyboardButton("Поиск расписания группы"))
    markup.add(KeyboardButton("≡ Настройки"))

    return markup
