from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


async def choice_role_keyboard() -> ReplyKeyboardMarkup:
    """
    Отправляет клавиатуру выбора роли

    :return:
    """

    markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)

    markup.add(KeyboardButton("Студент"))
    markup.add(KeyboardButton("Преподаватель"))

    return markup


async def main_keyboard() -> ReplyKeyboardMarkup:
    """
    Возвращает главную клавиатуру

    :return:
    """

    markup = ReplyKeyboardMarkup(row_width=4, resize_keyboard=True)

    markup.add(KeyboardButton("Сегодня"), KeyboardButton("Завтра"))
    markup.add(KeyboardButton("Эта неделя"), KeyboardButton("Следующая неделя"))

    markup.add(KeyboardButton("Поиск"))

    markup.add(KeyboardButton("Настройки"))

    return markup
