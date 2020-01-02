from typing import List

from aiogram import types
from aiogram.utils.callback_data import CallbackData

from app.ruz.server import Group, Teacher
from app.model import User
from app.utils import strings


search_callback = CallbackData("sr", "menu")
groups_callback = CallbackData("g", "id", "name")
teachers_callback = CallbackData("t", "id", "name")
settings_callback = CallbackData("st", "menu")
subscribe_time_callback = CallbackData("s_t", "time", sep="|")
subscribe_day_callback = CallbackData("s_d", "day", sep="|")


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
                callback_data=search_callback.new(
                    menu="Расписание на определенный день"
                ),
            ),
        )

    keyboard_markup.row(
        types.InlineKeyboardButton(
            "Расписание преподавателя",
            callback_data=search_callback.new(menu="Расписание преподавателя"),
        ),
    )
    keyboard_markup.row(
        types.InlineKeyboardButton(
            "Расписание группы",
            callback_data=search_callback.new(menu="Расписание группы"),
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
                    callback_data=groups_callback.new(
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
                callback_data=teachers_callback.new(id=teacher.id, name=teacher.name),
            )
        )

    keyboard_markup.add(
        types.InlineKeyboardButton(
            "Не нашли? Проверьте на RUZ", url="http://ruz.fa.ru/ruz"
        ),
    )
    print(keyboard_markup)
    return keyboard_markup


async def settings(user: User) -> types.InlineKeyboardMarkup:
    """
    Возвращает inline клавиатуру настроек

    :param user:
    :return:
    """

    keyboard_markup = types.InlineKeyboardMarkup(row_width=1)

    if user.role and user.search_id:
        if user.role == "teacher":
            role = "lecturer"
        else:
            role = "group"
        url = f"{strings.SUBSCRIBE_URL}?name={user.search_display}&type={role}&id={user.search_id}".replace(
            " ", "+"
        )
        keyboard_markup.row(
            types.InlineKeyboardButton("Добавить в календарь 📲", url=url,)
        )

    keyboard_markup.row(
        types.InlineKeyboardButton(
            "Отображение расписания",
            callback_data=settings_callback.new(menu="DISPLAY_SCHEDULE"),
        )
    )

    if (
        user.role
        and user.search_id
        and user.subscription_time is None
        or user.subscription_time == "CHANGES"
    ):
        keyboard_markup.row(
            types.InlineKeyboardButton(
                "Подписаться на расписание",
                callback_data=settings_callback.new(menu="SUBSCRIBE_CHOICE_TIME"),
            )
        )
    else:
        if user.subscription_days is not None and user.subscription_days != "CHANGES":
            if user.role and user.search_id:
                keyboard_markup.row(
                    types.InlineKeyboardButton(
                        "Изменить подписку на расписание",
                        callback_data=settings_callback.new(
                            menu="SUBSCRIBE_CHOICE_TIME"
                        ),
                    )
                )
            keyboard_markup.row(
                types.InlineKeyboardButton(
                    "Отписаться от подписки на расписание",
                    callback_data=settings_callback.new(menu="UNSUBSCRIBE"),
                )
            )

    return keyboard_markup


async def display_in_schedule(
    show_groups: bool, show_location: bool
) -> types.InlineKeyboardMarkup:
    """
    Возвращает inline клавиатуру показа полей в расписании

    :param show_location:
    :param show_groups:
    :return:
    """

    keyboard_markup = types.InlineKeyboardMarkup(row_width=1)

    keyboard_markup.row(
        types.InlineKeyboardButton(
            f"Группы в расписании {'✅' if show_groups is True else '❌'}",
            callback_data=settings_callback.new(menu="GROUPS_IN_SCHEDULE"),
        )
    )
    keyboard_markup.row(
        types.InlineKeyboardButton(
            f"Корпус в расписании {'✅' if show_location is True else '❌'}",
            callback_data=settings_callback.new(menu="LOCATION_IN_SCHEDULE"),
        )
    )
    keyboard_markup.row(
        types.InlineKeyboardButton(
            f"Назад", callback_data=settings_callback.new(menu="CANCEL"),
        )
    )

    return keyboard_markup


async def subscribe_choice_time_keyboard() -> types.InlineKeyboardMarkup:
    """
    Возвращает клавиатуру выбора времени подписки

    :return:
    """

    keyboard_markup = types.InlineKeyboardMarkup(row_width=3)

    keyboard_markup.row(
        types.InlineKeyboardButton(
            "7:00", callback_data=subscribe_time_callback.new(time="7:00"),
        ),
        types.InlineKeyboardButton(
            "7:30", callback_data=subscribe_time_callback.new(time="7:30"),
        ),
        types.InlineKeyboardButton(
            "8:00", callback_data=subscribe_time_callback.new(time="8:00"),
        ),
    )
    keyboard_markup.row(
        types.InlineKeyboardButton(
            "9:00", callback_data=subscribe_time_callback.new(time="9:00"),
        ),
        types.InlineKeyboardButton(
            "10:40", callback_data=subscribe_time_callback.new(time="10:40"),
        ),
        types.InlineKeyboardButton(
            "12:05", callback_data=subscribe_time_callback.new(time="12:05"),
        ),
    )
    keyboard_markup.row(
        types.InlineKeyboardButton(
            "20:00", callback_data=subscribe_time_callback.new(time="20:00"),
        ),
        types.InlineKeyboardButton(
            "21:30", callback_data=subscribe_time_callback.new(time="21:30"),
        ),
        types.InlineKeyboardButton(
            "22:00", callback_data=subscribe_time_callback.new(time="22:00"),
        ),
    )
    keyboard_markup.row(
        types.InlineKeyboardButton(
            "Отмена", callback_data=subscribe_day_callback.new(day="Отмена"),
        )
    )

    return keyboard_markup


async def choice_day_keyboard() -> types.InlineKeyboardMarkup:
    """
    Возвращает клавиатуру выбора дня подписки

    :return:
    """

    keyboard_markup = types.InlineKeyboardMarkup(row_width=2)

    keyboard_markup.row(
        types.InlineKeyboardButton(
            "Текущий день",
            callback_data=subscribe_day_callback.new(day="Текущий день"),
        ),
        types.InlineKeyboardButton(
            "Следующий день",
            callback_data=subscribe_day_callback.new(day="Следующий день"),
        ),
    )
    keyboard_markup.row(
        types.InlineKeyboardButton(
            "Текущий и следующий день",
            callback_data=subscribe_day_callback.new(day="Текущий и следующий день"),
        ),
    )
    keyboard_markup.row(
        types.InlineKeyboardButton(
            "Эта неделя", callback_data=subscribe_day_callback.new(day="Эта неделя"),
        ),
    )
    keyboard_markup.row(
        types.InlineKeyboardButton(
            "Следующая неделяь",
            callback_data=subscribe_day_callback.new(day="Следующая неделя"),
        ),
    )
    keyboard_markup.row(
        types.InlineKeyboardButton(
            "Отмена", callback_data=subscribe_day_callback.new(day="Отмена"),
        )
    )

    return keyboard_markup
