import datetime
import calendar

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData

from app.utils.strings import CALENDAR_MONTHS, CALENDAR_DAYS

calendar_callback = CallbackData("ca", "action", "year", "month", "day")


async def create_calendar(year: int = None, month: int = None) -> InlineKeyboardMarkup:
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

    keyboard_markup = InlineKeyboardMarkup(row_width=7)

    keyboard_markup.row(
        InlineKeyboardButton(
            CALENDAR_MONTHS[month - 1] + " " + str(year),
            callback_data=calendar_callback.new(
                action="Месяца", year=year, month=month, day="!"
            ),
        )
    )

    keyboard_markup.row(
        *[
            InlineKeyboardButton(
                day,
                callback_data=calendar_callback.new(
                    action="Исключение", year=year, month=month, day="!"
                ),
            )
            for day in CALENDAR_DAYS
        ]
    )

    for week in calendar.monthcalendar(year, month):
        row = list()
        for day in week:
            if day == 0:
                row.append(
                    InlineKeyboardButton(
                        " ",
                        callback_data=calendar_callback.new(
                            action="Исключение", year=year, month=month, day="!"
                        ),
                    )
                )
            elif (
                f"{now_day.day}.{now_day.month}.{now_day.year}"
                == f"{day}.{month}.{year}"
            ):
                row.append(
                    InlineKeyboardButton(
                        f"({day})",
                        callback_data=calendar_callback.new(
                            action="DAY", year=year, month=month, day=day
                        ),
                    )
                )
            else:
                row.append(
                    InlineKeyboardButton(
                        f" {day} ",
                        callback_data=calendar_callback.new(
                            action="День", year=year, month=month, day=day
                        ),
                    )
                )
        keyboard_markup.row(*row)

    keyboard_markup.row(
        InlineKeyboardButton(
            "<",
            callback_data=calendar_callback.new(
                action="Предыдущий месяц", year=year, month=month, day="!"
            ),
        ),
        InlineKeyboardButton(
            "Отмена",
            callback_data=calendar_callback.new(
                action="Отмена", year=year, month=month, day="!"
            ),
        ),
        InlineKeyboardButton(
            ">",
            callback_data=calendar_callback.new(
                action="Следующий месяц", year=year, month=month, day="!"
            ),
        ),
    )

    return keyboard_markup


async def create_months_calendar(year: int = None) -> InlineKeyboardMarkup:
    """
    Создает календарь с выбором месяца

    :param year: Год
    :return:
    """

    if year is None:
        year = datetime.datetime.now().year

    keyboard_markup = InlineKeyboardMarkup()

    for i, month in enumerate(zip(CALENDAR_MONTHS[0::2], CALENDAR_MONTHS[1::2])):
        keyboard_markup.row(
            InlineKeyboardButton(
                month[0],
                callback_data=calendar_callback.new(
                    action="Месяц", year=year, month=i + 1, day="!"
                ),
            ),
            InlineKeyboardButton(
                month[1],
                callback_data=calendar_callback.new(
                    action="Месяц", year=year, month=(i + 1) * 2, day="!"
                ),
            ),
        )

    return keyboard_markup
