import schedule
import telebot
import logging
import time
import app.utils.calendar as telebot_calendar
import app.utils.strings as strings

from app.models import User
from app.utils.keyboards import *
from app.utils.server import *
from config import API_TOKEN
from telebot.types import ReplyKeyboardRemove

logger = logging.getLogger(__name__)
telebot.logger.setLevel(logging.DEBUG)
logger.addHandler(telebot.logger)

bot = telebot.TeleBot(API_TOKEN, threaded=False)

# SPAM DICT
users = dict()
# CALENDAR DICT
users_calendar_dates = dict()


@bot.message_handler(commands=["start"])
def start_message(message):
    """
    Отправляет приглашение пользователю

    :param message:
    :return:
    """

    user = User.search_user(message.chat.id)
    if user.subscription_days:
        text = "Ваша подписка сброшена\n"
    else:
        text = ""
    User.update_user(user=user, data=dict(id=message.chat.id, role=None, menu="START", search_id=None,
                                          search_display=None, subscription_time=None, subscription_days=None,
                                          subscription_id=None, show_location=False, show_groups=False,
                                          login=message.chat.username))
    bot.send_message(message.chat.id, text + strings.WELCOME,
                     reply_markup=choice_role_keyboard())
    users.update({message.chat.id: dict(time=datetime.datetime.today(),
                                        warnings=0,
                                        ban=False)})


@bot.message_handler(regexp="студент|преподаватель")
def role_message(message):
    """
    Отправляет предложение о смене группы

    :param message:
    :return:
    """

    user = User.search_user(message.chat.id)
    if message.text == "Студент":
        User.update_user(user=user, data=dict(id=message.chat.id, role="student", menu="CHOICE_GROUP"))
        bot.send_message(message.chat.id, strings.GROUP_EXAMPLE,
                         reply_markup=ReplyKeyboardRemove())
    elif message.text == "Преподаватель":
        User.update_user(user=user, data=dict(id=message.chat.id, role="teacher",
                                              menu="CHOICE_NAME", show_groups=True))
        bot.send_message(message.chat.id, strings.TEACHER_EXAMPLE,
                         reply_markup=ReplyKeyboardRemove())


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    """
    Обработка inline callback запросов

    :param call:
    :return:
    """

    user = User.search_user(call.message.chat.id)

    if call.data == "groups_in_schedule":
        user = User.update_user(user=user, data=dict(show_groups=False if user.show_groups is True else True))
        if user.show_groups is True:
            text = "Теперь группы будут показываться в расписании"
        else:
            text = "Теперь группы не будут показываться в расписании"
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              reply_markup=display_in_schedule_keyboard(user), text=text)
    elif call.data == "location_in_schedule":
        user = User.update_user(user=user, data=dict(show_location=False if user.show_location is True else True))
        if user.show_location is True:
            text = "Теперь местоположение будет показываться в расписании"
        else:
            text = "Теперь местоположение не будут показываться в расписании"
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              reply_markup=display_in_schedule_keyboard(user), text=text)
    else:
        data = call.data.split(";")
        if len(data) > 1:
            if user.menu == "SEARCH_DAY" and user.search_additional == "CHANGES":
                type_selected, date = telebot_calendar.calendar_query_handler(bot, call)
                if type_selected == "DAY":
                    User.update_user(user, data=dict(menu="MAIN_MENU", search_additional=None))
                    bot.send_message(chat_id=call.message.chat.id,
                                     text=format_schedule(user=user, date=date), parse_mode="Markdown",
                                     reply_markup=main_keyboard(user))
                elif type_selected == "CANCEL":
                    User.update_user(user, data=dict(menu="MAIN_MENU", search_additional=None))
                    bot.send_message(call.from_user.id, strings.CHOOSE_MENU, reply_markup=main_keyboard(user))


@bot.message_handler(content_types=["text"])
def check_other_messages(message):
    """
    Проверяет сообщения, которые не может обработать API Telebot

    :param message:
    :return:
    """

    user = User.search_user(message.chat.id)

    if user.login is None and user.menu == "START":
        return start_message(message=message)

    if users.get(message.chat.id) is None:
        users[message.chat.id] = dict(time=datetime.datetime.today(), warnings=0, ban=False)
    if users[message.chat.id]["ban"] is False:
        if (datetime.datetime.today() - users[message.chat.id]["time"]).seconds > 60:
            users.update({message.chat.id: dict(time=datetime.datetime.today(),
                                                warnings=0,
                                                ban=False)})
        if (datetime.datetime.today() - users[message.chat.id]["time"]).seconds < 1:
            users.update({message.chat.id: dict(time=datetime.datetime.today(),
                                                warnings=users[message.chat.id]["warnings"] + 1,
                                                ban=users[message.chat.id]["ban"])})
            if users[message.chat.id]["warnings"] > 28:
                bot.send_message(message.chat.id, "❗️ Блокировка на 1 минуту ❗️")
                users.update({message.chat.id: dict(time=datetime.datetime.today(),
                                                    warnings=users[message.chat.id]["warnings"],
                                                    ban=True)})
                return
            elif users[message.chat.id]["warnings"] % 9 == 0:
                bot.send_message(message.chat.id, "❗️ Не спамьте! ❗️")
                return
        else:
            users.update({message.chat.id: dict(time=datetime.datetime.today(),
                                                warnings=users[message.chat.id]["warnings"],
                                                ban=users[message.chat.id]["ban"])})
    else:
        if (datetime.datetime.today() - users[message.chat.id]["time"]).seconds > 60:
            users.update({message.chat.id: dict(time=datetime.datetime.today(),
                                                warnings=0,
                                                ban=False)})
        else:
            return

    if user.menu == "MAIN_MENU":
        if user.search_id is not None:
            if message.text == "Сегодня":
                bot.send_message(message.chat.id, format_schedule(user, days=1), parse_mode="Markdown")
            elif message.text == "Завтра":
                bot.send_message(message.chat.id, format_schedule(user, start_day=1, days=1), parse_mode="Markdown")
            elif message.text == "Эта неделя":
                bot.send_message(message.chat.id,
                                 format_schedule(user, start_day=-datetime.datetime.now().isoweekday() + 1, days=7),
                                 parse_mode="Markdown")
            elif message.text == "Следующая неделя":
                bot.send_message(message.chat.id,
                                 format_schedule(user, start_day=7 - datetime.datetime.now().isoweekday() + 1, days=7),
                                 parse_mode="Markdown")
            elif message.text == "Поиск":
                user = User.update_user(user, data=dict(menu="SEARCH_MENU"))
                bot.send_message(message.chat.id, strings.CHOOSE_MENU, reply_markup=search_keyboard(user))
            elif message.text == "≡ Настройки":
                user = User.update_user(user, data=dict(menu="SETTINGS"))
                bot.send_message(message.chat.id, strings.WHAT_TO_SET,
                                 reply_markup=settings_keyboard(user))
        else:
            if user.role is None:
                bot.send_message(message.chat.id, strings.WELCOME,
                                 reply_markup=choice_role_keyboard())
            else:
                bot.send_message(message.chat.id, "Не удалось получить расписание", reply_markup=main_keyboard(user))
    if user.menu == "CHOICE_GROUP" or user.menu == "SEARCH_GROUP":
        group = get_group(message.text)
        if group.has_error is False and group.data:
            if user.menu == "SEARCH_GROUP":
                User.update_user(user=user, data=dict(search_additional=group.data[1],
                                                      menu="SEARCH_GROUP_DAY"))
                bot.send_message(message.chat.id, f"Найдена группа «{group.data[0]}»",
                                 reply_markup=choice_day_keyboard())
            else:
                user = User.update_user(user=user, data=dict(search_id=group.data[1],
                                                             search_display=group.data[0],
                                                             menu="MAIN_MENU"))
                bot.send_message(message.chat.id, strings.GROUP_CHANGED_FOR.format(group.data[0]),
                                 reply_markup=main_keyboard(user))
        else:
            bot.send_message(message.chat.id, f"Не удалось найти вашу группу. Введите вашу группу еще раз",
                             reply_markup=ReplyKeyboardRemove())
    elif user.menu == "SEARCH_GROUP_DAY" or user.menu == "SEARCH_TEACHER_DAY":
        if message.text == "Текущий день":
            if user.menu == "SEARCH_TEACHER_DAY":
                bot.send_message(message.chat.id,
                                 format_schedule(user, days=1, teacher_id=int(user.search_additional)),
                                 parse_mode="Markdown")
            elif user.menu == "SEARCH_GROUP_DAY":
                bot.send_message(message.chat.id,
                                 format_schedule(user, days=1, group_id=int(user.search_additional)),
                                 parse_mode="Markdown")
        elif message.text == "Следующий день":
            if user.menu == "SEARCH_TEACHER_DAY":
                bot.send_message(message.chat.id,
                                 format_schedule(user, start_day=1, days=1, teacher_id=int(user.search_additional)),
                                 parse_mode="Markdown")
            elif user.menu == "SEARCH_GROUP_DAY":
                bot.send_message(message.chat.id,
                                 format_schedule(user, start_day=1, days=1, group_id=int(user.search_additional)),
                                 parse_mode="Markdown")
        elif message.text == "Текущий и следующий день":
            if user.menu == "SEARCH_TEACHER_DAY":
                bot.send_message(message.chat.id,
                                 format_schedule(user, days=2, teacher_id=int(user.search_additional)),
                                 parse_mode="Markdown")
            elif user.menu == "SEARCH_GROUP_DAY":
                bot.send_message(message.chat.id,
                                 format_schedule(user, days=2, group_id=int(user.search_additional)),
                                 parse_mode="Markdown")
        elif message.text == "Эта неделя":
            if user.menu == "SEARCH_TEACHER_DAY":
                bot.send_message(message.chat.id,
                                 format_schedule(user, start_day=-datetime.datetime.now().isoweekday() + 1,
                                                 days=7, teacher_id=int(user.search_additional)),
                                 parse_mode="Markdown")
            elif user.menu == "SEARCH_GROUP_DAY":
                bot.send_message(message.chat.id,
                                 format_schedule(user, start_day=-datetime.datetime.now().isoweekday() + 1,
                                                 days=7, group_id=int(user.search_additional)),
                                 parse_mode="Markdown")
        elif message.text == "Следующая неделя":
            if user.menu == "SEARCH_TEACHER_DAY":
                bot.send_message(message.chat.id,
                                 format_schedule(user, start_day=7 - datetime.datetime.now().isoweekday() + 1,
                                                 days=7, teacher_id=int(user.search_additional)),
                                 parse_mode="Markdown")
            elif user.menu == "SEARCH_GROUP_DAY":
                bot.send_message(message.chat.id,
                                 format_schedule(user, start_day=7 - datetime.datetime.now().isoweekday() + 1,
                                                 days=7, group_id=int(user.search_additional)),
                                 parse_mode="Markdown")
        bot.send_message(message.chat.id, strings.CHOOSE_MENU, reply_markup=main_keyboard(user))
        User.update_user(user, data=dict(menu="MAIN_MENU", search_additional=None))
    elif user.menu == "CHOICE_NAME" or user.menu == "SEARCH_TEACHER":
        teachers = get_teacher(message.text)
        if teachers.has_error is False and teachers.data:
            if user.menu == "SEARCH_TEACHER":
                User.update_user(user=user, data=dict(search_additional=teachers.data[0][0],
                                                      menu="SEARCH_TEACHER_DAY"))
                bot.send_message(message.chat.id, strings.FOUND_TEACHER.format(teachers.data[0][1]),
                                 reply_markup=choice_day_keyboard())
            else:
                User.update_user(user=user, data=dict(search_id=teachers.data[0][0],
                                                      search_display=teachers.data[0][1],
                                                      menu="MAIN_MENU"))
                bot.send_message(message.chat.id, f"Пользователь изменен на «{teachers.data[0][1]}»",
                                 reply_markup=main_keyboard(user))
        else:
            bot.send_message(message.chat.id, f"Не удалось найти, введите ФИО еще раз",
                             reply_markup=ReplyKeyboardRemove())
    elif user.menu == "SEARCH_DAY" and user.search_additional == "CHANGES":
        user = User.update_user(user, data=dict(menu="MAIN_MENU", search_additional=None))
        bot.send_message(message.chat.id, strings.CHOOSE_MENU, reply_markup=main_keyboard(user))
    elif user.menu == "SETTINGS":
        if message.text == "← Назад":
            user = User.update_user(user, data=dict(menu="MAIN_MENU"))
            bot.send_message(message.chat.id, strings.CHOOSE_MENU, reply_markup=main_keyboard(user))
        elif message.text == "Отображение расписания":
            bot.send_message(message.chat.id, "Тут вы можете выбрать строки которые нужно показывать в расписании, "
                                              "или выключить их показ",
                             reply_markup=display_in_schedule_keyboard(user))
        elif message.text == "Подписаться на расписание" or message.text == "Изменить подписку на расписание":
            User.update_user(user, data=dict(menu="SUBSCRIBE_CHOICE_TIME",
                                             subscription_id=user.search_id,
                                             subscription_time=None,
                                             subscription_days=None))
            bot.send_message(message.chat.id,
                             "Напишите или выбери время в которое хотите получать раписание\n\nНапример: «12:35»",
                             reply_markup=subscribe_choice_time_keyboard())
        elif message.text == "Отписаться от подписки на расписание":
            user = User.update_user(user, data=dict(menu="MAIN_MENU",
                                                    subscription_id=user.search_id,
                                                    subscription_time=None,
                                                    subscription_days=None))
            bot.send_message(message.chat.id, "Подписка на раписание отменена", reply_markup=main_keyboard(user))
    elif user.menu == "SEARCH_MENU":
        if message.text == "← Назад":
            user = User.update_user(user, data=dict(menu="MAIN_MENU"))
            bot.send_message(message.chat.id, strings.CHOOSE_MENU, reply_markup=main_keyboard(user))
        elif message.text == "Расписание на определенный день":
            User.update_user(user, data=dict(menu="SEARCH_DAY", search_additional="CHANGES"))
            now = datetime.datetime.now()
            users_calendar_dates[message.chat.id] = (now.year, now.month)
            bot.send_message(message.chat.id, "Выберите дату в календаре",
                             reply_markup=telebot_calendar.create_calendar(now.year, now.month))
        elif message.text == "Расписание группы":
            User.update_user(user, data=dict(menu="SEARCH_GROUP", search_additional="CHANGES"))
            bot.send_message(message.chat.id, "Напиши группу, которую требуется найти\n\nНапример «ПИ18-1»",
                             reply_markup=ReplyKeyboardRemove())
        elif message.text == "Расписание преподавателя":
            User.update_user(user, data=dict(menu="SEARCH_TEACHER", search_additional="CHANGES"))
            bot.send_message(message.chat.id,
                             "Напиши ФИО преподавателя, которого необходимо найти\n\nНапример «Коротеев Михаил "
                             "Викторович»",
                             reply_markup=ReplyKeyboardRemove())
    elif user.menu == "SUBSCRIBE_CHOICE_TIME":
        subscribe_time = message.text
        try:
            subscribe_time = datetime.datetime.strptime(subscribe_time, "%H:%M").strftime("%H:%M")
        except ValueError:
            user = User.update_user(user=user, data=dict(menu="MAIN_MENU",
                                                         subscription_id=None,
                                                         subscription_time=None,
                                                         subscription_days=None))
        if user.subscription_id is None:
            if message.text == "Отмена":
                text = strings.CHOOSE_MENU
            else:
                text = strings.INCORRECT_DATE_FORMAT
            bot.send_message(message.chat.id, text, reply_markup=main_keyboard(user))
        else:
            user = User.update_user(user, data=dict(menu="SUBSCRIBE_CHOICE_DAY", subscription_time=subscribe_time))
            bot.send_message(message.chat.id,
                             f"Формируем подписку в {user.subscription_time}\nВыбери период, в "
                             f"который ты хочешь получать расписание",
                             reply_markup=choice_day_keyboard())
    elif user.menu == "SUBSCRIBE_CHOICE_DAY":
        day = message.text
        if day in ("Текущий день", "Следующий день", "Текущий и следующий день", "Эта неделя", "Следующая неделя"):
            user = User.update_user(user=user, data=dict(menu="MAIN_MENU",
                                                         subscription_days=day))
            if day == "Эта неделя":
                day = "эту неделю"
            elif day == "Следующая неделя":
                day = "следующую неделю"
            else:
                day = day.lower()
            bot.send_message(message.chat.id,
                             f"Подписка на рассылку успешно сформирована\n\n"
                             f"Теперь каждый день в {user.subscription_time} ты будешь получать расписание на {day}",
                             reply_markup=main_keyboard(user))
        else:
            user = User.update_user(user=user, data=dict(menu="MAIN_MENU",
                                                         subscription_id=None,
                                                         subscription_time=None,
                                                         subscription_days=None))
            if message.text == "Отмена":
                text = strings.CHOOSE_MENU
            else:
                text = "Не удалось добавить в рассылку расписания\nНеправильный день"
            bot.send_message(message.chat.id, text, reply_markup=main_keyboard(user))
    elif message.text.lower() == "меню":
        user = User.update_user(user, data=dict(menu="MAIN_MENU"))
        bot.send_message(message.chat.id, "Перевели вас в главное меню", reply_markup=main_keyboard(user))


def schedule_subscription():
    """
    Рассылает расписание пользователям

    :return:
    """

    global bot

    for user in User.filter_by_time(time.strftime("%H:%M", time.localtime())):
        if user.subscription_days == "Текущий день":
            bot.send_message(user.id,
                             "Твое расписание на сегодня\n\n" + format_schedule(user, days=1),
                             parse_mode="Markdown")
        elif user.subscription_days == "Следующий день":
            bot.send_message(user.id,
                             "Твое расписание на следующий день\n\n" + format_schedule(user, start_day=1, days=1),
                             parse_mode="Markdown")
        elif user.subscription_days == "Текущий и следующий день":
            bot.send_message(user.id,
                             "Твое расписание на сегодня и завтра\n\n" + format_schedule(user, days=2),
                             parse_mode="Markdown")
        elif user.subscription_days == "Эта неделя":
            bot.send_message(user.id,
                             "Твое расписание на эту неделю\n\n" +
                             format_schedule(user, start_day=-datetime.datetime.now().isoweekday() + 1, days=7),
                             parse_mode="Markdown")
        elif user.subscription_days == "Следующая неделя":
            bot.send_message(user.id,
                             "Твое расписание на следующую\n\n" +
                             format_schedule(user, start_day=7 - datetime.datetime.now().isoweekday() + 1, days=7),
                             parse_mode="Markdown")


def start_workers():
    """
    Запускает работников

    :return:
    """

    print(" * CRON started")
    schedule.every().minute.at(":00").do(schedule_subscription)
    while True:
        schedule.run_pending()
        time.sleep(1)


