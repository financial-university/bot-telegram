from dataclasses import dataclass
from typing import AsyncContextManager, Callable

from aiogram import Bot
from aiopg.sa import create_engine, SAConnection

# from aiomysql.sa import create_engine, SAConnection
from aiomisc_dependency import dependency

Connection = Callable[[], AsyncContextManager[SAConnection]]


def config_dependency(config: dataclass):
    @dependency
    async def db() -> Connection:
        engine = await create_engine(
            host=config.db_host,
            port=config.db_port,
            database=config.db_database,
            user=config.db_user,
            password=config.db_password,
            echo=True if config.debug else False,
        )
        yield engine.acquire
        engine.close()
        await engine.wait_closed()

    @dependency
    async def bot() -> Bot:
        """
        Создает экзепляр бота

        :return:
        """

        bot = Bot(config.token)
        yield bot
        await bot.delete_webhook()
