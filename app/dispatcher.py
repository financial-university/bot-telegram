import logging
import datetime
import asyncio

from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode
from aiogram.utils import exceptions
from aiogram.types.reply_keyboard import ReplyKeyboardRemove
from aiogram.utils.exceptions import MessageToDeleteNotFound
from aiogram.utils.parts import safe_split_text

from app.ruz.server import Group, Teacher, get_group, get_teacher, format_schedule
from app.dependency import Connection
from app.model import Model, User, UserFilteredByTime
from app.keyboards import (
    standard_keyboard,
    inline_keyboard_search,
    inline_keyboard_settings,
    inline_keyboard_calendar,
)
from app.utils import strings

log = logging.getLogger(__name__)


class BotHelper:
    bot: Bot

    @staticmethod
    async def get_schedule(
        user: User or UserFilteredByTime,
        start_day: int = 0,
        days: int = 1,
        text: str = "",
        search_id: int = None,
        search_type: str = None,
        show_groups: bool = None,
        show_location: bool = None,
    ) -> list:
        """
        Отсылает пользователю расписание

        :param user:
        :param start_day: -1 - начало этой недели, -2 - начало следующей
        :param days:
        :param text: начальная строка, к которой прибавляется расписание
        :param search_id:
        :param search_type:
        :param show_groups:
        :param show_location:
        :return:
        """

        if start_day == -1:
            start_day = -datetime.datetime.now().isoweekday() + 1
        elif start_day == -2:
            start_day = 7 - datetime.datetime.now().isoweekday() + 1

        if search_type is None or search_id is None:
            search_id = user.search_id
            search_type = user.role
            show_groups = user.show_groups
            show_location = user.show_location

        schedule = await format_schedule(
            id=search_id,
            type=search_type,
            start_day=start_day,
            days=days,
            show_groups=show_groups,
            show_location=show_location,
        )
        if schedule is None:
            log.warning("Target [CHAT_ID:%s]: error getting schedule", user.id)
            return [strings.CANT_GET_SCHEDULE]
        return safe_split_text(text + schedule)

    async def send_message(
        self,
        chat_id: int,
        text: str or list,
        parse_mode: str = None,
        disable_web_page_preview: bool = None,
        disable_notification: bool = None,
        reply_to_message_id: int = None,
        reply_markup=None,
    ) -> True or False:
        """
        Отправка сообщенея

        :param chat_id:
        :param text:
        :param parse_mode:
        :param disable_web_page_preview:
        :param disable_notification:
        :param reply_to_message_id:
        :param reply_markup:
        :return:
        """

        if isinstance(text, str):
            parts = safe_split_text(text)
        elif isinstance(text, list):
            parts = text
        else:
            raise TypeError

        try:
            for text in parts:
                await self.bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    parse_mode=parse_mode,
                    disable_web_page_preview=disable_web_page_preview,
                    disable_notification=disable_notification,
                    reply_to_message_id=reply_to_message_id,
                    reply_markup=reply_markup,
                )
        except exceptions.BotBlocked:
            log.error("Target [CHAT_ID:%s]: blocked by user", chat_id)
        except exceptions.ChatNotFound:
            log.error("Target [CHAT_ID:%s]: invalid user ID", chat_id)
        except exceptions.RetryAfter as e:
            log.error(
                "Target [CHAT_ID:%s]: Flood limit is exceeded. Sleep %s seconds.",
                chat_id,
                e.timeout,
            )
            await asyncio.sleep(e.timeout)
        except exceptions.UserDeactivated:
            log.error("Target [CHAT_ID:%s]: user is deactivated", chat_id)
        except exceptions.TelegramAPIError:
            log.exception(f"Target [CHAT_ID:%s]: failed", chat_id)
        else:
            log.info("Target [CHAT_ID:%s]: success", chat_id)
            return True
        return False


class BotDispatcher(Dispatcher, BotHelper):
    bot: Bot
    model: Model

    def __init__(self, bot: Bot, db: Connection):
        super().__init__(bot)
        self.model = Model(db)

        # START/RESTART BOT
        self.register_message_handler(
            self.start_message, commands=["start", "restart", "старт"]
        )

        # CHANGE ROLE
        self.register_message_handler(self.role_message, regexp="студент|преподаватель")

        # SEARCH GROUP/TEACHERS
        self.register_callback_query_handler(
            self._list_groups_or_teachers_handler,
            inline_keyboard_search.groups_list_callback.filter(),
        )

        self.register_callback_query_handler(
            self._list_groups_or_teachers_handler,
            inline_keyboard_search.teachers_list_callback.filter(),
        )

        # SEARCH IN MENU

        self.register_callback_query_handler(
            self._schedule_specific_day,
            inline_keyboard_search.menu_callback.filter(
                menu="Расписание на определенный день"
            ),
        )

        self.register_callback_query_handler(
            self._schedule_specific_teacher,
            inline_keyboard_search.menu_callback.filter(
                menu="Расписание преподавателя"
            ),
        )

        self.register_callback_query_handler(
            self._schedule_specific_group,
            inline_keyboard_search.menu_callback.filter(menu="Расписание группы"),
        )

        # CALENDAR

        self.register_callback_query_handler(
            self._calendar_next_month,
            inline_keyboard_calendar.calendar_callback.filter(action="Следующий месяц"),
        )

        self.register_callback_query_handler(
            self._calendar_previous_month,
            inline_keyboard_calendar.calendar_callback.filter(
                action="Предыдущий месяц"
            ),
        )

        self.register_callback_query_handler(
            self._calendar_cancel,
            inline_keyboard_calendar.calendar_callback.filter(action="Отмена"),
        )

        self.register_callback_query_handler(
            self._calendar_exception,
            inline_keyboard_calendar.calendar_callback.filter(action="Исключение"),
        )

        self.register_callback_query_handler(
            self._calendar_months,
            inline_keyboard_calendar.calendar_callback.filter(action="Месяца"),
        )

        self.register_callback_query_handler(
            self._calendar_month,
            inline_keyboard_calendar.calendar_callback.filter(action="Месяц"),
        )

        self.register_callback_query_handler(
            self._calendar_day,
            inline_keyboard_calendar.calendar_callback.filter(action="День"),
        )

        # SETTINGS

        self.register_callback_query_handler(
            self._settings_subscribe_to_time,
            inline_keyboard_settings.settings_callback.filter(menu="Подписка на время"),
        )

        self.register_callback_query_handler(
            self._settings_unsubscribe,
            inline_keyboard_settings.settings_callback.filter(menu="Отписаться"),
        )

        self.register_callback_query_handler(
            self._settings_displayed_fields,
            inline_keyboard_settings.settings_callback.filter(menu="Показываемые поля"),
        )

        self.register_callback_query_handler(
            self._settings_back,
            inline_keyboard_settings.settings_callback.filter(menu="Настройки"),
        )

        self.register_callback_query_handler(
            self._settings_displayed_fields_menu,
            inline_keyboard_settings.settings_callback.filter(
                menu=["Группы в расписании", "Место в расписании"]
            ),
        )

        # SUBSCRIBE
        self.register_callback_query_handler(
            self._choice_day_schedule,
            inline_keyboard_settings.subscribe_time_callback.filter(),
        )
        self.register_callback_query_handler(
            self._choice_day_schedule,
            inline_keyboard_settings.subscribe_day_callback.filter(),
        )

        # OTHER MESSAGES
        self.register_message_handler(self.check_other_messages, content_types=["text"])

    async def start_message(self, message: types.Message) -> None:
        """
        Отправляет начальные настройки пользователя и сбрасывает данные пользователя по умолчанию

        :param message:
        :return:
        """

        user = await self.model.get_user(message.from_user.id)
        await self.model.update_user(
            message.from_user.id,
            data=dict(
                id=message.from_user.id,
                role=None,
                menu="START",
                search_id=None,
                search_display=None,
                subscription_time=None,
                subscription_days=None,
                subscription_id=None,
                show_location=False,
                show_groups=False,
                login=message.from_user.username,
            ),
        )
        await self.send_message(
            user.id,
            text=strings.WELCOME,
            reply_markup=await standard_keyboard.choice_role_keyboard(),
        )

    async def role_message(self, message: types.Message) -> None:
        """
        Обработка предложения о смене группы

        :param message:
        :return:
        """

        user = await self.model.get_user(message.from_user.id)

        if message.text == "Студент":
            await self.model.update_user(
                user.id, data=dict(id=user.id, role="student", menu="CHOICE_GROUP"),
            )
            await self.send_message(
                user.id, text=strings.GROUP_EXAMPLE, reply_markup=ReplyKeyboardRemove(),
            )
        elif message.text == "Преподаватель":
            await self.model.update_user(
                user.id,
                data=dict(
                    id=user.id,
                    role="teacher",
                    menu="CHOICE_NAME",
                    show_location=True,
                    show_groups=True,
                ),
            )
            await self.send_message(
                user.id,
                text=strings.TEACHER_EXAMPLE,
                reply_markup=ReplyKeyboardRemove(),
            )

    async def check_other_messages(self, message: types.Message) -> None:
        """
        Обрабатывает сообщения, которые не может обработать handler

        :param message:
        :return:
        """

        user = await self.model.get_user(message.from_user.id)

        if user.menu == "MAIN_MENU":
            await self._main_menu(user=user, message=message)
        elif user.menu == "CHOICE_GROUP" or user.menu == "SEARCH_GROUP":
            await self._search_group(user=user, message=message)
        elif user.menu == "CHOICE_NAME" or user.menu == "SEARCH_TEACHER":
            await self._search_teacher(user=user, message=message)
        elif user.menu == "SUBSCRIBE_CHOICE_TIME":
            data = dict(menu="MAIN_MENU", subscription_id=user.search_id,)
            try:
                subscribe_time = datetime.datetime.strptime(
                    message.text, "%H:%M"
                ).strftime("%H:%M")
                data["subscription_time"] = subscribe_time
                await self.model.update_user(user.id, data=data)
                keyboard = await inline_keyboard_settings.choice_day_keyboard()
                await self.send_message(
                    chat_id=user.id,
                    text=strings.DISPLAY_SCHEDULE,
                    reply_markup=keyboard,
                )
            except ValueError:
                await self.send_message(
                    chat_id=user.id, text="Выберите другое время",
                )
        else:
            log.warning("Target [CHAT_ID:%s]: not found menu", user.id)

    async def _main_menu(self, user: User, message: types.Message) -> None:
        """
        Обрабатывает главное меню

        :param user:
        :param message:
        :return:
        """

        select = message.text
        if select == "Сегодня":
            self.loop.create_task(
                self.send_message(
                    chat_id=user.id,
                    text=await self.get_schedule(user=user, start_day=0, days=1),
                    parse_mode=ParseMode.MARKDOWN,
                )
            )
        elif select == "Завтра":
            self.loop.create_task(
                self.send_message(
                    chat_id=user.id,
                    text=await self.get_schedule(user=user, start_day=1, days=1),
                    parse_mode=ParseMode.MARKDOWN,
                )
            )
        elif select == "Эта неделя":
            self.loop.create_task(
                self.send_message(
                    user.id,
                    text=await self.get_schedule(user=user, start_day=-1, days=7),
                    parse_mode=ParseMode.MARKDOWN,
                )
            )
        elif select == "Следующая неделя":
            self.loop.create_task(
                self.send_message(
                    user.id,
                    text=await self.get_schedule(user=user, start_day=-2, days=7),
                    parse_mode=ParseMode.MARKDOWN,
                )
            )
        elif select == "Поиск":
            keyboard = await inline_keyboard_search.search_keyboard(user=user)
            await self.send_message(
                chat_id=user.id, text=strings.WHAT_TO_FIND, reply_markup=keyboard
            )
        elif select == "Настройки":
            keyboard = await inline_keyboard_settings.settings(user=user)
            await self.send_message(
                chat_id=user.id, text=strings.WHAT_TO_SET, reply_markup=keyboard,
            )
        else:
            keyboard = await standard_keyboard.main_keyboard()
            await self.send_message(
                chat_id=user.id, text=strings.WHAT_TO_SET, reply_markup=keyboard,
            )

    async def _search_group(self, user: User, message: types.Message) -> None:
        """
        Ищет группу
        Использует во время поиска группы из главного меню и во время первой настройки

        :param user:
        :param message:
        :return:
        """

        groups = await get_group(group_name=message.text)

        if isinstance(groups.data, list) and groups.has_error is False and groups.data:
            if len(groups.data) == 1:
                if user.menu == "SEARCH_GROUP":
                    await self.model.update_user(
                        id=user.id,
                        data=dict(
                            search_additional=groups.data[0].id,
                            menu="SEARCH_GROUP_DAY",
                        ),
                    )
                    await self.send_message(
                        chat_id=user.id,
                        text=strings.GROUP.format(groups.data[0].name),
                        reply_markup=await inline_keyboard_settings.choice_day_keyboard(),
                    )
                else:
                    await self.model.update_user(
                        id=user.id,
                        data=dict(
                            search_id=groups.data[0].id,
                            search_display=groups.data[0].name,
                            menu="MAIN_MENU",
                        ),
                    )
                    await self.send_message(
                        chat_id=user.id,
                        text=strings.GROUP_CHANGED_FOR.format(groups.data[0].name)
                        + "\n"
                        + strings.CHOOSE_MENU,
                        reply_markup=await standard_keyboard.main_keyboard(),
                    )
            else:
                keyboard = await inline_keyboard_search.list_groups(groups=groups.data)
                await message.reply(strings.CHOOSE_GROUP, reply_markup=keyboard)

        else:
            await self.send_message(
                chat_id=user.id,
                text=strings.GROUP_NOT_FOUND.format(message.text),
                reply_markup=ReplyKeyboardRemove(),
            )

    async def _search_teacher(self, user: User, message: types.Message) -> None:
        """
        Ищет преподавателя
        Использует во время поиска группы из главного меню и во время первой настройки

        :param user:
        :param message:
        :return:
        """

        teachers = await get_teacher(message.text)

        if (
            isinstance(teachers.data, list)
            and teachers.has_error is False
            and teachers.data
        ):
            if len(teachers.data) == 1:
                if user.menu == "SEARCH_TEACHER":
                    await self.model.update_user(
                        id=user.id,
                        data=dict(
                            search_additional=teachers.data[0].id,
                            menu="SEARCH_TEACHER_DAY",
                        ),
                    )
                    await self.send_message(
                        chat_id=user.id,
                        text=strings.GROUP.format(teachers.data[0].name),
                        reply_markup=await inline_keyboard_settings.choice_day_keyboard(),
                    )
                else:
                    await self.model.update_user(
                        id=user.id,
                        data=dict(
                            search_id=teachers.data[0].id,
                            search_display=teachers.data[0].name,
                            menu="MAIN_MENU",
                        ),
                    )
                    await self.send_message(
                        chat_id=user.id,
                        text=strings.FOUND_TEACHER.format(teachers.data[0].name)
                        + "\n"
                        + strings.CHOOSE_MENU,
                        reply_markup=await standard_keyboard.main_keyboard(),
                    )
            else:
                keyboard = await inline_keyboard_search.list_teacher(
                    teachers=teachers.data
                )
                await message.reply(
                    strings.CHOOSE_CURRENT_TEACHER, reply_markup=keyboard
                )
        else:
            await self.send_message(
                chat_id=user.id,
                text=strings.TEACHER_NOT_FOUND.format(message.text),
                reply_markup=ReplyKeyboardRemove(),
            )

    async def _list_groups_or_teachers_handler(
        self, query: types.CallbackQuery, callback_data: dict
    ) -> None:
        """
        Обрабатывает списки групп и преподавателей

        :param query:
        :param callback_data:
        :return:
        """

        user = await self.model.get_user(query.from_user.id)
        if callback_data["@"] == "g":
            data = Group(id=callback_data["id"], name=callback_data["name"])
            search_day = "SEARCH_GROUP_DAY"
            edit_text = strings.GROUP_CHANGED_FOR.format(data.name)
        elif callback_data["@"] == "t":
            data = Teacher(id=callback_data["id"], name=callback_data["name"])
            search_day = "SEARCH_TEACHER_DAY"
            edit_text = strings.TEACHER_CHANGED_FOR.format(data.name)
        else:
            raise TypeError

        if user.menu == "SEARCH_GROUP" or user.menu == "SEARCH_TEACHER":
            await self.model.update_user(
                id=user.id, data=dict(search_additional=data.id, menu=search_day),
            )
            await query.message.edit_text(
                text=edit_text,
                reply_markup=await inline_keyboard_settings.choice_day_keyboard(),
            )
        else:
            await self.model.update_user(
                id=user.id,
                data=dict(
                    search_id=data.id, search_display=data.name, menu="MAIN_MENU",
                ),
            )
            await query.message.edit_text(edit_text)
            await self.send_message(
                chat_id=user.id,
                text=strings.CHOOSE_MENU,
                reply_markup=await standard_keyboard.main_keyboard(),
            )

    async def _settings_subscribe_to_time(self, query: types.CallbackQuery) -> None:
        """
        Обрабатывает подписку. Выбор времени

        :param query:
        :return:
        """

        user_id = query.from_user.id
        await self.model.update_user(
            user_id, data=dict(menu="SUBSCRIBE_CHOICE_TIME"),
        )
        await query.message.delete()
        await self.send_message(
            chat_id=user_id,
            text=strings.SUBSCRIBE_CHOICE_TIME_ONE,
            reply_markup=ReplyKeyboardRemove(),
        )
        keyboard = await inline_keyboard_settings.subscribe_choice_time_keyboard()
        await self.send_message(
            chat_id=user_id,
            text=strings.SUBSCRIBE_CHOICE_TIME_TWO,
            reply_markup=keyboard,
        )

    async def _settings_unsubscribe(self, query: types.CallbackQuery) -> None:
        """
        Обрабатывает отписку

        :param query:
        :return:
        """

        user = await self.model.get_user(query.from_user.id)

        await self._unsubscribe_to_schedule(user)
        await query.message.edit_text(strings.UNSUBSCRIBE_SCHEDULE)

    async def _settings_displayed_fields(self, query: types.CallbackQuery) -> None:
        """
        Обрабатывает позываемые поля

        :param query:
        :return:
        """

        user = await self.model.get_user(query.from_user.id)

        keyboard = await inline_keyboard_settings.display_in_schedule(
            show_groups=user.show_groups, show_location=user.show_location
        )
        await query.message.edit_text(strings.DISPLAY_SCHEDULE, reply_markup=keyboard)

    async def _settings_back(self, query: types.CallbackQuery) -> None:
        """
        Обрабатывает кнопку назад

        :param query:
        :return:
        """

        user = await self.model.get_user(query.from_user.id)

        keyboard = await inline_keyboard_settings.settings(user=user)
        await query.message.edit_text(strings.WHAT_TO_SET, reply_markup=keyboard)

    async def _settings_displayed_fields_menu(
        self, query: types.CallbackQuery, callback_data: dict
    ) -> None:
        """
        Обрабатывает настройки

        :param query:
        :param callback_data:
        :return:
        """

        user = await self.model.get_user(query.from_user.id)
        menu = callback_data["menu"]
        if any(item == menu for item in ("Место в расписании", "Группы в расписании")):
            show_groups = user.show_groups
            show_location = user.show_location
            if menu == "Место в расписании":
                show_location = False if show_location is True else True
                await self.model.update_user(
                    user.id, data=dict(show_location=show_location)
                )
            elif menu == "Группы в расписании":
                show_groups = False if show_groups is True else True
                await self.model.update_user(
                    user.id, data=dict(show_groups=show_groups)
                )
            keyboard = await inline_keyboard_settings.display_in_schedule(
                show_groups=show_groups, show_location=show_location
            )
            await query.message.edit_text(
                strings.DISPLAY_SCHEDULE, reply_markup=keyboard
            )

    async def _choice_day_schedule(
        self, query: types.CallbackQuery, callback_data: dict
    ) -> None:
        """
        Обрабатывает выбор дня

        :param query:
        :param callback_data:
        :return:
        """

        user = await self.model.get_user(query.from_user.id)
        if callback_data["@"] == "sub_t":
            time = callback_data["time"]
            if time == "Отмена":
                await self.loop.create_task(self._unsubscribe_to_schedule(user))
                await query.message.edit_text(strings.UNSUBSCRIBE_SCHEDULE)
            else:
                await self.model.update_user(
                    user.id,
                    data=dict(subscription_id=user.search_id, subscription_time=time,),
                )
                keyboard = await inline_keyboard_settings.choice_day_keyboard()
                await query.message.edit_text(
                    strings.DISPLAY_SCHEDULE, reply_markup=keyboard
                )
                # FIXME Каким то чудом придумать как скрывать клавиатуру :/
        elif callback_data["@"] == "sub_d":
            day = callback_data["day"]

            if user.menu == "SEARCH_GROUP_DAY" or user.menu == "SEARCH_TEACHER_DAY":
                if day == "Отмена":
                    await query.message.edit_text(strings.CANCEL)
                    await self.model.update_user(
                        user.id, data=dict(menu="MAIN_MENU", search_additional=None,),
                    )
                    await self.send_message(
                        chat_id=user.id,
                        text=strings.CHOOSE_MENU,
                        reply_markup=await standard_keyboard.main_keyboard(),
                    )
                else:

                    if day == "Эта неделя":
                        start_day = -1
                        days = 7
                        day = "эту неделю"
                    elif day == "Следующая неделя":
                        start_day = -2
                        days = 7
                        day = "следующую неделю"
                    elif day == "Текущий и следующий день":
                        day = "этот и следующий день"
                        start_day = 0
                        days = 2
                    elif day == "Текущий день":
                        start_day = 0
                        days = 1
                        day = "этот день"
                    elif day == "Следующий день":
                        start_day = 1
                        days = 1
                        day = "следующий день"
                    else:
                        log.error(
                            "Target [CHAT_ID:%s]: error name schedule on search other group/teacher",
                            user.id,
                        )
                        raise NameError
                    await self.model.update_user(
                        user.id, data=dict(menu="MAIN_MENU", search_additional=None,),
                    )

                    if user.menu == "SEARCH_GROUP_DAY":
                        search_type = "student"
                    else:
                        search_type = "teacher"
                    await query.answer(f"Загружаем расписание")
                    await query.message.delete()
                    schedule = await self.get_schedule(
                        user=user,
                        start_day=start_day,
                        days=days,
                        search_id=int(user.search_additional),
                        search_type=search_type,
                        text=f"Расписание на {day}\n\n",
                    )
                    await self.send_message(
                        chat_id=user.id,
                        text=schedule + [strings.CHOOSE_MENU],
                        reply_markup=await standard_keyboard.main_keyboard(),
                        parse_mode=ParseMode.MARKDOWN,
                    )
            else:  # Подписки
                if day == "Отмена":
                    self.loop.create_task(self._unsubscribe_to_schedule(user))
                    await query.message.edit_text(strings.UNSUBSCRIBE_SCHEDULE)
                    await self.send_message(
                        chat_id=user.id,
                        text=strings.CHOOSE_MENU,
                        reply_markup=await standard_keyboard.main_keyboard(),
                    )
                else:
                    self.loop.create_task(
                        self.model.update_user(
                            user.id, data=dict(subscription_days=day, menu="MAIN_MENU"),
                        )
                    )
                    if day == "Эта неделя":
                        day = "эту неделю"
                    elif day == "Следующая неделя":
                        day = "следующую неделю"
                    else:
                        day = day.lower()

                    await query.message.delete()
                    keyboard = await standard_keyboard.main_keyboard()
                    await self.send_message(
                        chat_id=user.id,
                        text=f"Подписка на рассылку успешно сформирована\n\n"
                        f"Теперь каждый день в {user.subscription_time} вы будете получать расписание на {day}\n\n"
                        + strings.WHAT_TO_SET,
                        reply_markup=keyboard,
                    )

    async def _unsubscribe_to_schedule(self, user: User) -> None:
        """
        Сбрасывает подписку пользователя

        :param user:
        :return:
        """

        await self.model.update_user(
            user.id,
            data=dict(
                menu="MAIN_MENU",
                subscription_id=None,
                subscription_time=None,
                subscription_days=None,
            ),
        )

    async def _calendar_day(
        self, query: types.CallbackQuery, callback_data: dict
    ) -> None:
        """
        Обрабатывает действие календаря "расписание на определенный день"

        :param query:
        :param callback_data:
        :return:
        """

        user = await self.model.get_user(query.from_user.id)
        self.loop.create_task(query.answer(strings.LOAD_SCHEDULE))
        action, day, month, year = (
            callback_data["action"],
            callback_data["day"],
            callback_data["month"],
            callback_data["year"],
        )
        date = datetime.datetime.strptime(f"{day}.{month}.{year}", f"%d.%m.%Y")
        start_day = (date - datetime.datetime.today() + datetime.timedelta(days=1)).days

        message = await self.get_schedule(user=user, start_day=start_day, days=1)
        await query.message.edit_text(message[0], parse_mode=ParseMode.MARKDOWN)

    @staticmethod
    async def _calendar_next_month(
        query: types.CallbackQuery, callback_data: dict
    ) -> None:
        """
        Обрабатывает действие календаря "следующий месяц календаря"

        :param query:
        :param callback_data:
        :return:
        """

        action, day, month, year = (
            callback_data["action"],
            callback_data["day"],
            callback_data["month"],
            callback_data["year"],
        )

        current = datetime.datetime(int(year), int(month), 1)

        next_month = current + datetime.timedelta(days=31)
        keyboard = await inline_keyboard_calendar.create_calendar(
            int(next_month.year), int(next_month.month)
        )
        await query.message.edit_text(text=query.message.text, reply_markup=keyboard)

    @staticmethod
    async def _calendar_previous_month(
        query: types.CallbackQuery, callback_data: dict
    ) -> None:
        """
        Обрабатывает действие календаря "предыдущий месяц календаря"

        :param query:
        :param callback_data:
        :return:
        """

        action, day, month, year = (
            callback_data["action"],
            callback_data["day"],
            callback_data["month"],
            callback_data["year"],
        )

        current = datetime.datetime(int(year), int(month), 1)

        preview_month = current - datetime.timedelta(days=1)
        keyboard = await inline_keyboard_calendar.create_calendar(
            year=int(preview_month.year), month=int(preview_month.month)
        )
        await query.message.edit_text(text=query.message.text, reply_markup=keyboard)

    @staticmethod
    async def _calendar_month(query: types.CallbackQuery, callback_data: dict) -> None:
        """
        Обрабатывает действие календаря "выбор месяца"

        :param query:
        :param callback_data:
        :return:
        """

        action, day, month, year = (
            callback_data["action"],
            callback_data["day"],
            callback_data["month"],
            callback_data["year"],
        )

        keyboard = await inline_keyboard_calendar.create_calendar(
            year=int(year), month=int(month)
        )
        await query.message.edit_text(text=query.message.text, reply_markup=keyboard)

    @staticmethod
    async def _calendar_months(query: types.CallbackQuery, callback_data: dict) -> None:
        """
        Обрабатывает действие календаря "показать месяца"

        :param query:
        :param callback_data:
        :return:
        """

        action, day, month, year = (
            callback_data["action"],
            callback_data["day"],
            callback_data["month"],
            callback_data["year"],
        )

        current = datetime.datetime(int(year), int(month), 1)

        keyboard = await inline_keyboard_calendar.create_months_calendar(
            year=current.year
        )
        await query.message.edit_text(text=query.message.text, reply_markup=keyboard)

    @staticmethod
    async def _calendar_exception(query: types.CallbackQuery) -> None:
        """
        Обрабатывает действие календаря "исключение"

        :param query:
        :return:
        """

        await query.answer("Выберите другое действие")

    @staticmethod
    async def _calendar_cancel(query: types.CallbackQuery) -> None:
        """
        Обрабатывает действие календаря "отмена"

        :param query:
        :return:
        """

        try:
            await query.message.delete()
        except MessageToDeleteNotFound:
            await query.answer(strings.MESSAGE_DELETED)

    @staticmethod
    async def _schedule_specific_day(query: types.CallbackQuery) -> None:
        """
        Обрабатывает расписание на определенный день

        :param query:
        :return:
        """

        now = datetime.datetime.now()
        await query.message.edit_text(
            strings.SELECT_DAY_IN_CALENDAR,
            reply_markup=await inline_keyboard_calendar.create_calendar(
                year=now.year, month=now.month
            ),
        )

    async def _schedule_specific_group(self, query: types.CallbackQuery) -> None:
        """
        Обрабатывает расписание для опеределнной группы

        :param query:
        :return:
        """

        user_id = query.from_user.id
        await query.message.delete()
        await self.model.update_user(
            user_id, data=dict(menu="SEARCH_GROUP", search_additional="CHANGES",),
        )
        await self.send_message(
            chat_id=user_id,
            text=strings.WRITE_GROUP,
            reply_markup=ReplyKeyboardRemove(),
        )

    async def _schedule_specific_teacher(self, query: types.CallbackQuery) -> None:
        """
        Обрабатывает расписание для определенного преподавателя

        :param query:
        :return:
        """

        user_id = query.from_user.id
        await query.message.delete()
        await self.model.update_user(
            user_id, data=dict(menu="SEARCH_TEACHER", search_additional="CHANGES",),
        )
        await self.send_message(
            chat_id=user_id,
            text=strings.WRITE_TEACHER,
            reply_markup=ReplyKeyboardRemove(),
        )
