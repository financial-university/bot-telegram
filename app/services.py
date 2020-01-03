import asyncio
import logging
import time
from asyncio import Event, sleep

import schedule
import aiohttp.web
from aiogram import Bot
from aiogram.types import ParseMode
from aiomisc.service.base import Service
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiomisc.service.aiohttp import AIOHTTPService
from aiohttp.web_request import Request

from app.dispatcher import BotDispatcher
from app.dependency import Connection
from app.model import Model, User, UserFilteredByTime

log = logging.getLogger(__name__)


class BotService(Service):
    __dependencies__ = ("db", "bot")
    bot: Bot
    db: Connection
    dispatcher: BotDispatcher

    async def start(self):
        """
        Запускает сервис

        :return:
        """

        self.dispatcher = BotDispatcher(bot=self.bot, db=self.db)
        self.dispatcher.middleware.setup(LoggingMiddleware())

        asyncio.run_coroutine_threadsafe(self.dispatcher.start_polling(), self.loop)

        log.info("Bot started")

    async def stop(self, exception=None):
        """
        Останавливает сервис

        :param exception:
        :return:
        """

        await self.dispatcher.stop_polling()


class BotSubscriptionService(Service):
    __dependencies__ = ("db", "bot")
    bot: Bot
    db: Connection
    dispatcher: BotDispatcher
    exit_event: Event

    async def start(self):
        """
        Запускает сервис

        :return:
        """

        self.dispatcher = BotDispatcher(bot=self.bot, db=self.db)
        self.dispatcher.middleware.setup(LoggingMiddleware())
        self.exit_event = Event()

        logging.getLogger("schedule").setLevel(logging.DEBUG)

        def distribution():
            asyncio.run_coroutine_threadsafe(self.schedule_distribution(), self.loop)

        schedule.every().minute.at(":00").do(distribution)

        log.info("Bot subscription started")

        while not self.exit_event.is_set():
            schedule.run_pending()
            await sleep(1)

    async def stop(self, exception=None):
        """
        Останавливает сервис

        :param exception:
        :return:
        """

        self.exit_event.set()

    async def schedule_distribution(self):
        """
        Рассылает расписание пользователям

        :return:
        """

        async with self.db() as conn:
            for user in (
                UserFilteredByTime(*user.as_tuple())
                for user in await (
                    (
                        await conn.execute(
                            User.filter_by_time(
                                time.strftime("%H:%M", time.localtime())
                            )
                        )
                    ).fetchall()
                )
            ):
                if all(
                    item is not None
                    for item in (user.subscription_days, user.subscription_id,)
                ):
                    if user.subscription_days == "Текущий день":
                        self.loop.create_task(
                            self.dispatcher.send_message(
                                chat_id=user.id,
                                text=await self.dispatcher.get_schedule(
                                    user=user,
                                    start_day=0,
                                    days=1,
                                    search_id=int(user.subscription_id),
                                    search_type=user.role,
                                    show_location=user.show_location,
                                    show_groups=user.show_groups,
                                    text="Ваше расписание на сегодня\n\n",
                                ),
                                parse_mode=ParseMode.MARKDOWN,
                            )
                        )
                    elif user.subscription_days == "Следующий день":
                        self.loop.create_task(
                            self.dispatcher.send_message(
                                chat_id=user.id,
                                text=await self.dispatcher.get_schedule(
                                    user=user,
                                    start_day=1,
                                    days=1,
                                    search_id=int(user.subscription_id),
                                    search_type=user.role,
                                    show_location=user.show_location,
                                    show_groups=user.show_groups,
                                    text="Ваше расписание на завтра\n\n",
                                ),
                                parse_mode=ParseMode.MARKDOWN,
                            )
                        )
                    elif user.subscription_days == "Текущий и следующий день":
                        self.loop.create_task(
                            self.dispatcher.send_message(
                                chat_id=user.id,
                                text=await self.dispatcher.get_schedule(
                                    user=user,
                                    days=2,
                                    search_id=int(user.subscription_id),
                                    search_type=user.role,
                                    show_location=user.show_location,
                                    show_groups=user.show_groups,
                                    text="Ваше расписание на сегодня и завтра\n\n",
                                ),
                                parse_mode=ParseMode.MARKDOWN,
                            )
                        )
                    elif user.subscription_days == "Эта неделя":
                        self.loop.create_task(
                            self.dispatcher.send_message(
                                chat_id=user.id,
                                text=await self.dispatcher.get_schedule(
                                    user=user,
                                    days=6,
                                    search_id=int(user.subscription_id),
                                    search_type=user.role,
                                    show_location=user.show_location,
                                    show_groups=user.show_groups,
                                    text="Ваше расписание на 7 дней\n\n",
                                ),
                                parse_mode=ParseMode.MARKDOWN,
                            )
                        )
                    elif user.subscription_days == "Следующая неделя":
                        self.loop.create_task(
                            self.dispatcher.send_message(
                                chat_id=user.id,
                                text=await self.dispatcher.get_schedule(
                                    user=user,
                                    start_day=7,
                                    days=7,
                                    search_id=int(user.subscription_id),
                                    search_type=user.role,
                                    show_location=user.show_location,
                                    show_groups=user.show_groups,
                                    text="Ваше расписание на следующую неделю\n\n",
                                ),
                                parse_mode=ParseMode.MARKDOWN,
                            )
                        )


class RESTfulService(AIOHTTPService):
    __dependencies__ = ("db",)
    db: Connection
    model: Model

    async def create_application(self):
        """
        Создает RESTful API сервис

        :return:
        """

        self.model = Model(self.db)
        app = aiohttp.web.Application()
        app.add_routes(
            [aiohttp.web.get("/api/users_count", self.handler_user_count),]
        )

        log.info("RESTful API started")

        return app

    async def handler_user_count(self, request: Request) -> "Response":
        """
        Обрабатывает запрос кол-ва человек в базе /api/users_count

        :return:
        """

        count = await self.model.get_count_users()

        return aiohttp.web.json_response(dict(count=count))
