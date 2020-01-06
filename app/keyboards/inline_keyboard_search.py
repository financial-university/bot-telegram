from typing import List

from aiogram import types
from aiogram.utils.callback_data import CallbackData

from app.ruz.server import Group, Teacher
from app.model import User


menu_callback = CallbackData("sm", "menu")
groups_list_callback = CallbackData("g", "id", "name")
teachers_list_callback = CallbackData("t", "id", "name")


async def search_keyboard(user: User) -> types.InlineKeyboardMarkup:
    """
    Возвращает меню поиска

    :param user:
    :return:
    """

    keyboard_markup = types.InlineKeyboardMarkup(row_width=1)

    if user.search_id:
        keyboard_markup.row(
            types.InlineKeyboardButton(
                "Расписание на определенный день",
                callback_data=menu_callback.new(menu="Расписание на определенный день"),
            ),
        )

    keyboard_markup.row(
        types.InlineKeyboardButton(
            "Расписание преподавателя",
            callback_data=menu_callback.new(menu="Расписание преподавателя"),
        ),
    )
    keyboard_markup.row(
        types.InlineKeyboardButton(
            "Расписание группы",
            callback_data=menu_callback.new(menu="Расписание группы"),
        ),
    )

    return keyboard_markup


async def list_groups(groups: List[Group]) -> types.InlineKeyboardMarkup:
    """
    Возвращает inline клавиатуру списка групп

    :param groups:
    :return:
    """

    keyboard_markup = types.InlineKeyboardMarkup(row_width=3)

    for i in range(0, len(groups), 3):
        keyboard_markup.row(
            *(
                types.InlineKeyboardButton(
                    group.name,
                    callback_data=groups_list_callback.new(
                        id=group.id, name=group.name.replace(":", "")
                    ),
                )
                for group in groups[i : i + 3]
            )
        )

    keyboard_markup.add(
        types.InlineKeyboardButton(
            "Не нашли? Проверьте на RUZ", url="http://ruz.fa.ru/ruz"
        ),
    )

    return keyboard_markup


async def list_teacher(teachers: List[Teacher]) -> types.InlineKeyboardMarkup:
    """
    Возвращает inline клавиатуру списка преподавателей

    :param teachers:
    :return:
    """

    keyboard_markup = types.InlineKeyboardMarkup(row_width=1)

    for teacher in teachers:
        keyboard_markup.row(
            types.InlineKeyboardButton(
                teacher.name,
                callback_data=teachers_list_callback.new(
                    id=teacher.id, name=teacher.name
                ),
            )
        )

    keyboard_markup.add(
        types.InlineKeyboardButton(
            "Не нашли? Проверьте на RUZ", url="http://ruz.fa.ru/ruz"
        ),
    )
    return keyboard_markup
