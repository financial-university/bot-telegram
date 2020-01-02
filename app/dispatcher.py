import logging
import datetime
import asyncio

from aiogram.types.reply_keyboard import ReplyKeyboardRemove
from aiogram import Bot, Dispatcher, types
from aiogram.utils import exceptions

from app.ruz.server import Group, Teacher, get_group, get_teacher, format_schedule
from app.dependency import Connection
from app.model import Model, User
from app.keyboards import keyboards, inline_keyboards, inline_calendar
from app.utils import strings

log = logging.getLogger(__name__)


class BotDispatcher(Dispatcher):
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
        self.register_callback_query_handler(
            self._list_groups_or_teachers_handler,
            inline_keyboards.groups_callback.filter(),
        )
        self.register_callback_query_handler(
            self._list_groups_or_teachers_handler,
            inline_keyboards.teachers_callback.filter(),
        )

        # SEARCH
        self.register_callback_query_handler(
            self._search_handler, inline_keyboards.search_callback.filter(),
        )

        # CALENDAR
        self.register_callback_query_handler(
            self._calendar_handler, inline_calendar.calendar_callback.filter(),
        )

        # SETTINGS
        self.register_callback_query_handler(
            self._settings_handler, inline_keyboards.settings_callback.filter(),
        )

        # SUBSCRIBE
        self.register_callback_query_handler(
            self._subscribe_to_schedule,
            inline_keyboards.subscribe_time_callback.filter(),
        )
        self.register_callback_query_handler(
            self._subscribe_to_schedule,
            inline_keyboards.subscribe_day_callback.filter(),
        )

        # OTHER MESSAGES
        self.register_message_handler(self.check_other_messages, content_types=["text"])

    async def send_message(
        self,
        chat_id: int,
        text: str,
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

        if len(text) > 4096:
            parts = list()
            while len(text) > 0:
                if len(text) > 4096:
                    part = text[:4096]
                    r = part.rfind("\n")
                    if r != -1:
                        parts.append(part[:r])
                        text = text[(r + 1) :]
                    else:
                        parts.append(part)
                        text = text[4096:]
                else:
                    parts.append(text)
                    break
        else:
            parts = [text]
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

    async def send_schedule(
        self,
        user: User,
        start_day: int = 0,
        days: int = 1,
        text: str = "",
        search_id: int = None,
        search_type: str = None,
        show_groups: bool = None,
        show_location: bool = None,
    ) -> True or False:
        """
        Отсылает пользователю расписание

        :param user:
        :param start_day: -1 - начало этой недели, -2 - начало следующей
        :param days:
        :param text:
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
            text=text,
            show_groups=show_groups,
            show_location=show_location,
        )
        if schedule is None:
            log.warning("Target [CHAT_ID:%s]: error getting schedule", user.id)
            await self.send_message(user.id, text="Не удалось получить расписание")
            return False
        await self.send_message(user.id, text=schedule)
        return True

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
        # TODO Решить что с этим делать
        # self.users.update(
        #     {user.id: dict(time=datetime.datetime.today(), warnings=0, ban=False)}
        # )
        await self.send_message(
            user.id,
            text=strings.WELCOME,
            reply_markup=await keyboards.choice_role_keyboard(),
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
        elif user.menu == "SEARCH_GROUP_DAY" or user.menu == "SEARCH_TEACHER_DAY":
            pass
        elif user.menu == "SEARCH_DAY" and user.search_additional == "CHANGES":
            pass
        elif user.menu == "SEARCH_MENU":
            pass
        else:
            print("Не относится никуда")

    async def _main_menu(self, user: User, message: types.Message) -> None:
        """
        Обрабатывает главное меню

        :param user:
        :param message:
        :return:
        """

        if message.text == "Сегодня":
            self.loop.create_task(self.send_schedule(user=user, start_day=0, days=1))
        elif message.text == "Завтра":
            self.loop.create_task(self.send_schedule(user=user, start_day=1, days=1))
        elif message.text == "Эта неделя":
            self.loop.create_task(self.send_schedule(user=user, start_day=-1, days=7))
        elif message.text == "Следующая неделя":
            self.loop.create_task(self.send_schedule(user=user, start_day=-2, days=7))
        elif message.text == "Поиск":
            keyboard = await inline_keyboards.search_keyboard(user=user)
            await self.send_message(
                chat_id=user.id, text=strings.WHAT_TO_FIND, reply_markup=keyboard
            )
        elif message.text == "Настройки":
            keyboard = await inline_keyboards.settings(user=user)
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
                if user.menu == "SEARCH_GROUP":  # TODO проверить работу
                    await self.model.update_user(
                        id=user.id,
                        data=dict(
                            search_additional=groups.data[0].id, menu="SEARCH_GROUP_DAY"
                        ),
                    )
                    await self.send_message(
                        chat_id=user.id,
                        text=strings.GROUP.format(groups.data[0].name),
                        reply_markup=await inline_keyboards.choice_day_keyboard(),
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
                        reply_markup=await keyboards.main_keyboard(user),
                    )
            else:
                keyboard = await inline_keyboards.list_groups(groups=groups.data)
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
                if user.menu == "SEARCH_TEACHER":  # TODO проверить работу
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
                        reply_markup=await inline_keyboards.choice_day_keyboard(),
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
                        reply_markup=await keyboards.main_keyboard(user),
                    )
            else:
                keyboard = await inline_keyboards.list_teacher(teachers=teachers.data)
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
            text = strings.GROUP.format(data.name)
            edit_text = strings.GROUP_CHANGED_FOR.format(data.name)
        elif callback_data["@"] == "t":
            data = Teacher(id=callback_data["id"], name=callback_data["name"])
            search_day = "SEARCH_TEACHER_DAY"
            text = strings.FOUND_TEACHER.format(data.name)
            edit_text = strings.TEACHER_CHANGED_FOR.format(data.name)
        else:
            raise TypeError

        if (
            user.menu == "SEARCH_GROUP" or user.menu == "SEARCH_TEACHER"
        ):  # TODO Проверить работу
            await self.model.update_user(
                id=user.id, data=dict(search_additional=data.id, menu=search_day),
            )
            await self.send_message(
                chat_id=user.id,
                text=text,
                reply_markup=await inline_keyboards.choice_day_keyboard(),
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
                reply_markup=await keyboards.main_keyboard(user),
            )

    async def _settings_handler(
        self, query: types.CallbackQuery, callback_data: dict
    ) -> None:
        """
        Обрабатывает настройки

        :param query:
        :param callback_data:
        :return:
        """

        user = await self.model.get_user(query.from_user.id)

        if callback_data["menu"] == "SUBSCRIBE_CHOICE_TIME":

            keyboard = await inline_keyboards.subscribe_choice_time_keyboard()
            await query.message.edit_text(
                strings.SUBSCRIBE_CHOICE_TIME, reply_markup=keyboard
            )

        elif callback_data["menu"] == "SUBSCRIBE_CHOICE_DAY":
            pass  # TODO Дописать
        elif callback_data["menu"] == "UNSUBSCRIBE":
            await self._unsubscribe_to_schedule(user)
            await query.message.edit_text(strings.UNSUBSCRIBE_SCHEDULE)
        elif callback_data["menu"] == "DISPLAY_SCHEDULE":
            keyboard = await inline_keyboards.display_in_schedule(
                show_groups=user.show_groups, show_location=user.show_location
            )
            await query.message.edit_text(
                strings.DISPLAY_SCHEDULE, reply_markup=keyboard
            )
        elif (
            callback_data["menu"] == "LOCATION_IN_SCHEDULE"
            or callback_data["menu"] == "GROUPS_IN_SCHEDULE"
        ):
            show_groups = user.show_groups
            show_location = user.show_location
            if callback_data["menu"] == "LOCATION_IN_SCHEDULE":
                show_location = False if show_location is True else True
                await self.model.update_user(
                    user.id, data=dict(show_location=show_location)
                )
            elif callback_data["menu"] == "GROUPS_IN_SCHEDULE":
                show_groups = False if show_groups is True else True
                await self.model.update_user(
                    user.id, data=dict(show_groups=show_groups)
                )
            keyboard = await inline_keyboards.display_in_schedule(
                show_groups=show_groups, show_location=show_location
            )
            await query.message.edit_text(
                strings.DISPLAY_SCHEDULE, reply_markup=keyboard
            )
        elif callback_data["menu"] == "CANCEL":
            keyboard = await inline_keyboards.settings(user=user)
            await query.message.edit_text(strings.WHAT_TO_SET, reply_markup=keyboard)

    async def _subscribe_to_schedule(
        self, query: types.CallbackQuery, callback_data: dict
    ) -> None:
        """
        Обрабатывает подписки

        :param query:
        :param callback_data:
        :return:
        """

        user = await self.model.get_user(query.from_user.id)
        if callback_data["@"] == "s_t":
            time = callback_data["time"]
            if time == "Отмена":
                await self.loop.create_task(self._unsubscribe_to_schedule(user))
                await query.message.edit_text(strings.UNSUBSCRIBE_SCHEDULE)
            else:
                await self.model.update_user(
                    user.id,
                    data=dict(subscription_id=user.search_id, subscription_time=time,),
                )
                keyboard = await inline_keyboards.choice_day_keyboard()
                await query.message.edit_text(
                    strings.WHAT_TO_SET, reply_markup=keyboard
                )
        elif callback_data["@"] == "s_d":
            day = callback_data["day"]
            if day == "Отмена":
                self.loop.create_task(self._unsubscribe_to_schedule(user))
                await query.message.edit_text(strings.UNSUBSCRIBE_SCHEDULE)
            else:
                self.loop.create_task(
                    self.model.update_user(user.id, data=dict(subscription_days=day,),)
                )
                if day == "Эта неделя":
                    day = "эту неделю"
                elif day == "Следующая неделя":
                    day = "следующую неделю"
                else:
                    day = day.lower()
                await query.message.edit_text(
                    f"Подписка на рассылку успешно сформирована\n\n"
                    f"Теперь каждый день в {user.subscription_time} вы будете получать расписание на {day}"
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

    async def _calendar_handler(
        self, query: types.CallbackQuery, callback_data: dict
    ) -> None:
        """
        Обрабатывает действия с календарем

        :param query:
        :param callback_data:
        :return:
        """

        print(callback_data)
        print(query)
        user = await self.model.get_user(query.from_user.id)

        action, day, month, year = (
            callback_data["action"],
            callback_data["day"],
            callback_data["month"],
            callback_data["year"],
        )

        current = datetime.datetime(int(year), int(month), 1)

        if action == "NEXT-MONTH":
            next_month = current + datetime.timedelta(days=31)
            keyboard = await inline_calendar.create_calendar(
                int(next_month.year), int(next_month.month)
            )
            await query.message.edit_text(
                text=query.message.text, reply_markup=keyboard
            )
        elif action == "PREVIOUS-MONTH":
            preview_month = current - datetime.timedelta(days=1)
            keyboard = await inline_calendar.create_calendar(
                year=int(preview_month.year), month=int(preview_month.month)
            )
            await query.message.edit_text(
                text=query.message.text, reply_markup=keyboard
            )
        elif action == "CANCEL":
            await query.message.delete()
        elif action == "MONTH":
            keyboard = await inline_calendar.create_calendar(
                year=int(year), month=int(month)
            )
            await query.message.edit_text(
                text=query.message.text, reply_markup=keyboard
            )
        elif action == "MONTHS":
            keyboard = await inline_calendar.create_months_calendar(year=current.year)
            await query.message.edit_text(
                text=query.message.text, reply_markup=keyboard
            )
        elif action == "DAY":
            date = datetime.datetime.strptime(f"{day}.{month}.{year}", f"%d.%m.%Y")
            start_day = (
                date - datetime.datetime.today() + datetime.timedelta(days=1)
            ).days
            # TODO Сделать фикс
            await query.message.delete()
            self.loop.create_task(
                self.send_schedule(user=user, start_day=start_day, days=1)
            )

    async def _search_handler(
        self, query: types.CallbackQuery, callback_data: dict
    ) -> None:
        """
        Обрабатывает поиск

        :param query:
        :param callback_data:
        :return:
        """

        print(callback_data)
        print(query)

        menu = callback_data["menu"]
        if menu == "Расписание на определенный день":
            now = datetime.datetime.now()
            await query.message.edit_text(
                strings.SELECT_DAY_IN_CALENDAR,
                reply_markup=await inline_calendar.create_calendar(
                    year=now.year, month=now.month
                ),
            )
        elif menu == "Расписание преподавателя":
            pass
        elif menu == "Расписание группы":
            pass
