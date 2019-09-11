import telebot
import logging
import time

from app.models import User
from app.utils.keyboards import *
from app.utils.server import *
from config import token
from telebot.types import ReplyKeyboardRemove

logger = telebot.logger
telebot.logger.setLevel(logging.DEBUG)
bot = telebot.TeleBot(token)


@bot.message_handler(commands=["start"])
def start(message):
    """
    Отправляет приглашение пользователю

    :param message:
    :return:
    """

    user = User.search_user(message.chat.id)
    User.update_user(user=user, data=dict(id=message.chat.id, role=None, menu="START", search_id=None,
                                          subscription_time=None, subscription_days=None, subscription_group=None,
                                          show_location=False, show_groups=False))
    bot.send_message(message.chat.id, "Привет!\n\nДля просмотра раписания требутся выбрать кто ты",
                     reply_markup=choice_role_keyboard())


@bot.message_handler(regexp="студент|преподаватель")
def student(message):
    """
    Отправляет предложение о смене группы

    :param message:
    :return:
    """

    user = User.search_user(message.chat.id)
    if message.text == "Студент":
        User.update_user(user=user, data=dict(id=message.chat.id, role="student", menu="CHOICE_GROUP"))
        bot.send_message(message.chat.id, "Напишите название вашей группы\n\nНапример «ПИ18-1»",
                         reply_markup=ReplyKeyboardRemove())
    elif message.text == "Преподаватель":
        User.update_user(user=user, data=dict(id=message.chat.id, role="teacher", menu="CHOICE_NAME"))
        bot.send_message(message.chat.id, "Напишите ваше ФИО\n\nНапример «Коротеев Михаил Викторович»",
                         reply_markup=ReplyKeyboardRemove())


@bot.message_handler(regexp="Сегодня|Завтра|Эта неделя|Следующая неделя|Расписание на определенный день|≡ Настройки")
def schedule(message):
    """
    Обрабатывает сообщения связанные с расписанием

    :param message:
    :return:
    """

    user = User.search_user(message.chat.id)
    if user.search_id is not None:
        if message.text == "Сегодня":
            bot.send_message(message.chat.id, format_schedule(user, days=1))
        elif message.text == "Завтра":
            bot.send_message(message.chat.id, format_schedule(user, start_day=1, days=1))
        elif message.text == "Эта неделя":
            bot.send_message(message.chat.id, format_schedule(user, days=7))
        elif message.text == "Следующая неделя":
            bot.send_message(message.chat.id, format_schedule(user, start_day=7, days=7))
        elif message.text == "Расписание на определенный день":
            user = User.update_user(user, data=dict(menu="SEARCH_DAY", search_day="CHANGES"))
            bot.send_message(message.chat.id, "Напишите дату, что бы получить ее расписание\n\nНапример «01.10.2019» "
                                              "или «01.10»", reply_markup=ReplyKeyboardRemove())
        elif message.text == "≡ Настройки":
            user = User.update_user(user, data=dict(menu="SETTINGS"))
            bot.send_message(message.chat.id, "Выберите то, что трубется настроить",
                             reply_markup=settings_keyboard(user))
    else:
        if user.role is None:
            bot.send_message(message.chat.id, "Выберите кто вы, прежде чем запрашивать расписание",
                             reply_markup=choice_role_keyboard())
        else:
            bot.send_message(message.chat.id, "Не удалось получить расписание", reply_markup=main_keyboard(user))


@bot.message_handler(content_types=["text"])
def check_other_messages(message):
    """
    Проверяет сообщения, которые не может обработать API Telebot

    :param message:
    :return:
    """

    user = User.search_user(message.chat.id)
    if user.menu == "CHOICE_GROUP":
        group = get_group(message.text)
        if group.has_error is False:
            user = User.update_user(user=user, data=dict(search_id=group.data[1], menu="MAIN_MENU"))
            bot.send_message(message.chat.id, f"Ваша группа изменена на «{group.data[0]}»",
                             reply_markup=main_keyboard(user))
        else:
            bot.send_message(message.chat.id, f"Не удалось найти вашу группу. Введите вашу группу еще раз",
                             reply_markup=ReplyKeyboardRemove())
    elif user.menu == "CHOICE_NAME":
        teachers = get_teacher(message.text)
        if teachers.has_error is False:
            User.update_user(user=user, data=dict(search_id=teachers.data[0][0], menu="MAIN_MENU"))
            bot.send_message(message.chat.id, f"Пользователь: «{teachers.data[0][1]}»",
                             reply_markup=main_keyboard(user))
        else:
            bot.send_message(message.chat.id, f"Не удалось Вас. Введите ваше ФИО еще раз",
                             reply_markup=ReplyKeyboardRemove())
    elif user.menu == "SEARCH_DAY" and user.search_day == "CHANGES":
        date = message.text
        try:
            if len(date.split(".")) == 3:
                date = datetime.datetime.strptime(date, '%d.%m.%Y')
            elif len(date.split(".")) == 2:
                date = datetime.datetime.strptime(f"{date}.{datetime.datetime.now().year}", '%d.%m.%Y')
            else:
                raise ValueError
        except ValueError:
            date = None
        user = User.update_user(user, data=dict(menu="MAIN_MENU", search_day=None))
        if date is not None:
            bot.send_message(message.chat.id, format_schedule(user=user, date=date), reply_markup=main_keyboard(user))
        else:
            bot.send_message(message.chat.id, f"Неправильная дата", reply_markup=main_keyboard(user))
    elif user.menu == "SETTINGS":
        if message.text == "← Назад":
            user = User.update_user(user, data=dict(menu="MAIN_MENU"))
            bot.send_message(message.chat.id, "Выберите пункт меню", reply_markup=main_keyboard(user))
    elif user.menu == "SEARCH_MENU":
        if message.text == "← Назад":
            user = User.update_user(user, data=dict(menu="MAIN_MENU"))
            bot.send_message(message.chat.id, "Выберите пункт меню", reply_markup=main_keyboard(user))
    elif message.text == "Поиск":
        user = User.update_user(user, data=dict(menu="SEARCH_MENU"))
        bot.send_message(message.chat.id, "Выберите пункт меню", reply_markup=search_keyboard(user))
    elif message.text.lower() == "меню":
        user = User.update_user(user, data=dict(menu="MAIN_MENU"))
        bot.send_message(message.chat.id, "Перевели вас в главное меню", reply_markup=main_keyboard(user))


while True:
    try:
        bot.polling(none_stop=True)
    except Exception as error:
        print("Server Error: ", error)
        time.sleep(1)
