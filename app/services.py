import logging

from aiogram import Bot
from aiogram.dispatcher import Dispatcher
from aiomisc.service.base import Service
from aiogram.contrib.middlewares.logging import LoggingMiddleware

from app.dispatcher import BotDispatcher
from app.dependency import Connection

log = logging.getLogger(__name__)


class BotService(Service):
    __dependencies__ = ("db", "bot")
    bot: Bot
    db: Connection
    dispatcher: Dispatcher

    async def start(self):
        """
        Запускает сервис

        :return:
        """

        self.dispatcher = BotDispatcher(bot=self.bot, db=self.db)
        self.dispatcher.middleware.setup(LoggingMiddleware())
        self.loop.create_task(self.dispatcher.start_polling())

    async def stop(self, exception=None):
        """
        Останавливает сервис

        :param exception:
        :return:
        """

        await self.dispatcher.stop_polling()
