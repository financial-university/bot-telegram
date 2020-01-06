from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData

from app.model import User
from app.utils import strings

settings_callback = CallbackData("sett", "menu")
subscribe_time_callback = CallbackData("sub_t", "time", sep="|")
subscribe_day_callback = CallbackData("sub_d", "day", sep="|")


async def settings(user: User) -> InlineKeyboardMarkup:
    """
    Возвращает inline клавиатуру настроек

    :param user:
    :return:
    """

    keyboard_markup = InlineKeyboardMarkup(row_width=1)

    if user.role and user.search_id:
        if user.role == "teacher":
            role = "lecturer"
        else:
            role = "group"
        url = f"{strings.SUBSCRIBE_URL}?name={user.search_display}&type={role}&id={user.search_id}".replace(
            " ", "+"
        )
        keyboard_markup.row(InlineKeyboardButton("Добавить в календарь 📲", url=url,))

    keyboard_markup.row(
        InlineKeyboardButton(
            "Отображение расписания",
            callback_data=settings_callback.new(menu="Показываемые поля"),
        )
    )

    if (
        user.role
        and user.search_id
        and (
            user.subscription_time is None
            or user.subscription_id is None
            or user.subscription_time is None
        )
    ):
        keyboard_markup.row(
            InlineKeyboardButton(
                "Подписаться на расписание",
                callback_data=settings_callback.new(menu="Подписка на время"),
            )
        )
    else:
        if user.subscription_days is not None and user.subscription_days != "CHANGES":
            if user.role and user.search_id:
                keyboard_markup.row(
                    InlineKeyboardButton(
                        "Изменить подписку на расписание",
                        callback_data=settings_callback.new(menu="Подписка на время"),
                    )
                )
            keyboard_markup.row(
                InlineKeyboardButton(
                    "Отписаться от подписки на расписание",
                    callback_data=settings_callback.new(menu="Отписаться"),
                )
            )

    return keyboard_markup


async def display_in_schedule(
    show_groups: bool, show_location: bool
) -> InlineKeyboardMarkup:
    """
    Возвращает inline клавиатуру показа полей в расписании

    :param show_location:
    :param show_groups:
    :return:
    """

    keyboard_markup = InlineKeyboardMarkup(row_width=1)

    keyboard_markup.row(
        InlineKeyboardButton(
            f"Группы в расписании {'✅' if show_groups is True else '❌'}",
            callback_data=settings_callback.new(menu="Группы в расписании"),
        )
    )
    keyboard_markup.row(
        InlineKeyboardButton(
            f"Корпус в расписании {'✅' if show_location is True else '❌'}",
            callback_data=settings_callback.new(menu="Место в расписании"),
        )
    )
    keyboard_markup.row(
        InlineKeyboardButton(
            f"Назад", callback_data=settings_callback.new(menu="Настройки"),
        )
    )

    return keyboard_markup


async def subscribe_choice_time_keyboard() -> InlineKeyboardMarkup:
    """
    Возвращает клавиатуру выбора времени подписки

    :return:
    """

    keyboard_markup = InlineKeyboardMarkup(row_width=3)

    keyboard_markup.row(
        InlineKeyboardButton(
            "7:00", callback_data=subscribe_time_callback.new(time="7:00"),
        ),
        InlineKeyboardButton(
            "7:30", callback_data=subscribe_time_callback.new(time="7:30"),
        ),
        InlineKeyboardButton(
            "8:00", callback_data=subscribe_time_callback.new(time="8:00"),
        ),
    )
    keyboard_markup.row(
        InlineKeyboardButton(
            "9:00", callback_data=subscribe_time_callback.new(time="9:00"),
        ),
        InlineKeyboardButton(
            "10:40", callback_data=subscribe_time_callback.new(time="10:40"),
        ),
        InlineKeyboardButton(
            "12:05", callback_data=subscribe_time_callback.new(time="12:05"),
        ),
    )
    keyboard_markup.row(
        InlineKeyboardButton(
            "20:00", callback_data=subscribe_time_callback.new(time="20:00"),
        ),
        InlineKeyboardButton(
            "21:30", callback_data=subscribe_time_callback.new(time="21:30"),
        ),
        InlineKeyboardButton(
            "22:00", callback_data=subscribe_time_callback.new(time="22:00"),
        ),
    )
    keyboard_markup.row(
        InlineKeyboardButton(
            "Отмена", callback_data=subscribe_day_callback.new(day="Отмена"),
        )
    )

    return keyboard_markup


async def choice_day_keyboard() -> InlineKeyboardMarkup:
    """
    Возвращает клавиатуру выбора дня подписки

    :return:
    """

    keyboard_markup = InlineKeyboardMarkup(row_width=2)

    keyboard_markup.row(
        InlineKeyboardButton(
            "Текущий день",
            callback_data=subscribe_day_callback.new(day="Текущий день"),
        ),
        InlineKeyboardButton(
            "Следующий день",
            callback_data=subscribe_day_callback.new(day="Следующий день"),
        ),
    )
    keyboard_markup.row(
        InlineKeyboardButton(
            "Текущий и следующий день",
            callback_data=subscribe_day_callback.new(day="Текущий и следующий день"),
        ),
    )
    keyboard_markup.row(
        InlineKeyboardButton(
            "Эта неделя", callback_data=subscribe_day_callback.new(day="Эта неделя"),
        ),
    )
    keyboard_markup.row(
        InlineKeyboardButton(
            "Следующая неделя",
            callback_data=subscribe_day_callback.new(day="Следующая неделя"),
        ),
    )
    keyboard_markup.row(
        InlineKeyboardButton(
            "Отмена", callback_data=subscribe_day_callback.new(day="Отмена"),
        )
    )

    return keyboard_markup
