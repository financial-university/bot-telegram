from dataclasses import dataclass
from typing import AsyncContextManager, Callable

from aiomysql.sa import create_engine, SAConnection

# from aiopg.sa import create_engine, SAConnection
from aiogram import Bot
from aiomisc_dependency import dependency

Connection = Callable[[], AsyncContextManager[SAConnection]]


def config_dependency(config: dataclass):
    @dependency
    async def db() -> Connection:
        engine = await create_engine(
            host=config.db_host,
            port=config.db_port,
            db=config.db_database,
            user=config.db_user,
            password=config.db_password,
            echo=True if config.debug else False,
            autocommit=True,
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
