import datetime
import calendar

from aiogram import types
from aiogram.utils.callback_data import CallbackData

from app.utils.strings import MONTHS, DAYS

calendar_callback = CallbackData("sr", "action", "year", "month", "day")


async def create_calendar(
    year: int = None, month: int = None
) -> types.InlineKeyboardMarkup:
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

    keyboard_markup = types.InlineKeyboardMarkup(row_width=7)

    keyboard_markup.row(
        types.InlineKeyboardButton(
            MONTHS[month - 1] + " " + str(year),
            callback_data=calendar_callback.new(
                action="MONTHS", year=year, month=month, day="!"
            ),
        )
    )

    keyboard_markup.row(
        *[
            types.InlineKeyboardButton(
                day,
                callback_data=calendar_callback.new(
                    action="IGNORE", year=year, month=month, day="!"
                ),
            )
            for day in DAYS
        ]
    )

    for week in calendar.monthcalendar(year, month):
        row = list()
        for day in week:
            if day == 0:
                row.append(
                    types.InlineKeyboardButton(
                        " ",
                        callback_data=calendar_callback.new(
                            action="IGNORE", year=year, month=month, day="!"
                        ),
                    )
                )
            elif (
                f"{now_day.day}.{now_day.month}.{now_day.year}"
                == f"{day}.{month}.{year}"
            ):
                row.append(
                    types.InlineKeyboardButton(
                        f"({day})",
                        callback_data=calendar_callback.new(
                            action="DAY", year=year, month=month, day=day
                        ),
                    )
                )
            else:
                row.append(
                    types.InlineKeyboardButton(
                        f" {day} ",
                        callback_data=calendar_callback.new(
                            action="DAY", year=year, month=month, day=day
                        ),
                    )
                )
        keyboard_markup.row(*row)

    keyboard_markup.row(
        types.InlineKeyboardButton(
            "<",
            callback_data=calendar_callback.new(
                action="PREVIOUS-MONTH", year=year, month=month, day="!"
            ),
        ),
        types.InlineKeyboardButton(
            "Отмена",
            callback_data=calendar_callback.new(
                action="CANCEL", year=year, month=month, day="!"
            ),
        ),
        types.InlineKeyboardButton(
            ">",
            callback_data=calendar_callback.new(
                action="NEXT-MONTH", year=year, month=month, day="!"
            ),
        ),
    )

    return keyboard_markup


async def create_months_calendar(year: int = None) -> types.InlineKeyboardMarkup:
    """
    Создает календарь с выбором месяца

    :param year: Год
    :return:
    """

    if year is None:
        year = datetime.datetime.now().year

    keyboard_markup = types.InlineKeyboardMarkup()

    for i, month in enumerate(zip(MONTHS[0::2], MONTHS[1::2])):
        keyboard_markup.row(
            types.InlineKeyboardButton(
                month[0],
                callback_data=calendar_callback.new(
                    action="MONTH", year=year, month=i + 1, day="!"
                ),
            ),
            types.InlineKeyboardButton(
                month[1],
                callback_data=calendar_callback.new(
                    action="MONTH", year=year, month=(i + 1) * 2, day="!"
                ),
            ),
        )

    return keyboard_markup
