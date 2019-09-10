import telebot
import logging

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


@bot.message_handler(regexp="студент")
def student(message):
    """
    Отправляет студенту предложение о смене группы

    :param message:
    :return:
    """

    user = User.search_user(message.chat.id)
    User.update_user(user=user, data=dict(id=message.chat.id, role="student", menu="CHOICE_GROUP"))
    bot.send_message(message.chat.id, "Напишите название вашей группы\n\nНапример «ПИ18-1»",
                     reply_markup=ReplyKeyboardRemove())


@bot.message_handler(regexp="преподаватель")
def teacher(message):
    """
    Отправляет преподавателю предложение о смене группы

    :param message:
    :return:
    """

    user = User.search_user(message.chat.id)
    User.update_user(user=user, data=dict(id=message.chat.id, role="teacher", menu="CHOICE_NAME"))
    bot.send_message(message.chat.id, "Напишите ваше ФИО\n\nНапример «Коротеев Михаил Викторович»",
                     reply_markup=ReplyKeyboardRemove())


@bot.message_handler(regexp="Сегодня|Завтра|Сегодня и завтра|Эта неделя|Следующая неделя")
def schedule(message):
    user = User.search_user(message.chat.id)
    if user.search_id is not None:
        if message.text == "Сегодня":
            bot.send_message(message.chat.id, format_schedule(user, days=1))
        elif message.text == "Завтра":
            bot.send_message(message.chat.id, format_schedule(user, start_day=1, days=1))
        elif message.text == "Сегодня и завтра":
            bot.send_message(message.chat.id, format_schedule(user, days=2))
        elif message.text == "Эта неделя":
            bot.send_message(message.chat.id, format_schedule(user, days=7))
        elif message.text == "Следующая неделя":
            bot.send_message(message.chat.id, format_schedule(user, start_day=7, days=7))
    else:
        bot.send_message(message.chat.id, "Выберите группу, прежде чем запрашивать расписание")



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
            user = User.update_user(user=user, data=dict(search_id=group.data[1], menu="STUDENT_MAIN_MENU"))
            bot.send_message(message.chat.id, f"Ваша группа изменена на «{group.data[0]}»",
                             reply_markup=main_keyboard(user))
        else:
            bot.send_message(message.chat.id, f"Не удалось найти вашу группу. Введите вашу группу еще раз",
                             reply_markup=ReplyKeyboardRemove())
    elif user.menu == "CHOICE_NAME":
        teachers = get_teacher(message.text)
        if teachers.has_error is False:
            User.update_user(user=user, data=dict(search_id=teachers.data[0][0], menu="STUDENT_MAIN_MENU"))
            bot.send_message(message.chat.id, f"Пользователь: «{teachers.data[0][1]}»",
                             reply_markup=main_keyboard(user))
        else:
            bot.send_message(message.chat.id, f"Не удалось Вас. Введите ваше ФИО еще раз",
                             reply_markup=ReplyKeyboardRemove())


bot.polling(none_stop=True)
