import datetime
import calendar

from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

months = [
    "Январь",
    "Февраль",
    "Март",
    "Апрель",
    "Май",
    "Июнь",
    "Июль",
    "Август",
    "Сентябрь",
    "Октябрь",
    "Ноябрь",
    "Декабрь",
]
days = [" Пн ", " Вт ", " Ср ", " Чт ", " Пт ", " Сб ", " Вс "]


def create_callback_data(action: str, year: int, month: int, day: str) -> str:
    """
    Создает данные обратного вызова

    :param action:
    :param year:
    :param month:
    :param day:
    :return:
    """

    return ";".join([action, str(year), str(month), str(day)])


def create_calendar(year: int = None, month: int = None) -> InlineKeyboardMarkup:
    """
    Создайт встроенную inline клавиатуру с календарем

    :param year: Год для использования в календаре, если не используется текущий год.
    :param month: Месяц для использования в календаре, если не используется текущий месяц.
    :return: Возвращает объект InlineKeyboardMarkup с календарем.
    """

    now_day = datetime.datetime.now()

    if year is None:
        year = now_day.year
    if month is None:
        month = now_day.month

    data_ignore = create_callback_data("IGNORE", year, month, "")
    data_months = create_callback_data("MONTHS", year, month, "")

    keyboard = InlineKeyboardMarkup(row_width=7)

    keyboard.add(
        InlineKeyboardButton(
            months[month - 1] + " " + str(year), callback_data=data_months
        )
    )

    keyboard.add(
        *[InlineKeyboardButton(day, callback_data=data_ignore) for day in days]
    )

    for week in calendar.monthcalendar(year, month):
        row = list()
        for day in week:
            if day == 0:
                row.append(InlineKeyboardButton(" ", callback_data=data_ignore))
            elif (
                f"{now_day.day}.{now_day.month}.{now_day.year}"
                == f"{day}.{month}.{year}"
            ):
                row.append(
                    InlineKeyboardButton(
                        f"({day})",
                        callback_data=create_callback_data("DAY", year, month, day),
                    )
                )
            else:
                row.append(
                    InlineKeyboardButton(
                        f" {day} ",
                        callback_data=create_callback_data("DAY", year, month, day),
                    )
                )
        keyboard.add(*row)

    keyboard.add(
        InlineKeyboardButton(
            "<", callback_data=create_callback_data("PREVIOUS-MONTH", year, month, "")
        ),
        InlineKeyboardButton(
            "Отмена", callback_data=create_callback_data("CANCEL", year, month, "")
        ),
        InlineKeyboardButton(
            ">", callback_data=create_callback_data("NEXT-MONTH", year, month, "")
        ),
    )

    return keyboard


def create_months_calendar(year: int = None) -> InlineKeyboardMarkup:
    """
    Создает календарь с выбором месяца

    :param year: Год
    :return:
    """

    if year is None:
        year = datetime.datetime.now().year

    keyboard = InlineKeyboardMarkup()

    for i, month in enumerate(zip(months[0::2], months[1::2])):
        keyboard.add(
            InlineKeyboardButton(
                month[0], callback_data=create_callback_data("MONTH", year, i + 1, "")
            ),
            InlineKeyboardButton(
                month[1],
                callback_data=create_callback_data("MONTH", year, (i + 1) * 2, ""),
            ),
        )

    return keyboard


def calendar_query_handler(bot: "bot", call: "callback") -> tuple:
    """
    Метод создает новый календарь если нажата кнопка вперед или назад
    Этот метод должен вызываться внутри CallbackQueryHandler.

    :param bot: Объект бота CallbackQueryHandler
    :param call: Новые данные CallbackQueryHandler
    :return: Возвращает кортеж
    """

    action, year, month, day = call.data.split(";")
    current = datetime.datetime(int(year), int(month), 1)
    if action == "IGNORE":
        bot.answer_callback_query(callback_query_id=call.id)
        return False, None
    elif action == "DAY":
        bot.delete_message(
            chat_id=call.message.chat.id, message_id=call.message.message_id
        )
        return "DAY", datetime.datetime(int(year), int(month), int(day))
    elif action == "PREVIOUS-MONTH":
        preview_month = current - datetime.timedelta(days=1)
        bot.edit_message_text(
            text=call.message.text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=create_calendar(
                int(preview_month.year), int(preview_month.month)
            ),
        )
        return None, None
    elif action == "NEXT-MONTH":
        next_month = current + datetime.timedelta(days=31)
        bot.edit_message_text(
            text=call.message.text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=create_calendar(int(next_month.year), int(next_month.month)),
        )
        return None, None
    elif action == "MONTHS":
        bot.edit_message_text(
            text=call.message.text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=create_months_calendar(current.year),
        )
        return "MONTH", None
    elif action == "MONTH":
        bot.edit_message_text(
            text=call.message.text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=create_calendar(int(year), int(month)),
        )
        return None, None
    elif action == "CANCEL":
        bot.delete_message(
            chat_id=call.message.chat.id, message_id=call.message.message_id
        )
        return "CANCEL", None
    else:
        bot.answer_callback_query(callback_query_id=call.id, text="ERROR!")
        return None, None
