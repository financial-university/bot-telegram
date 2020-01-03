import logging
from dataclasses import dataclass

from aiomisc import entrypoint

from app.dependency import config_dependency
from app.services import (
    BotService,
    BotSubscriptionService,
    RESTfulService,
)


log = logging.getLogger(__name__)


def start_app(config: dataclass):
    """
    Запускает сервисы

    :param config: конфиг
    :return:
    """

    config_dependency(config)
    with entrypoint(
        BotService(token=config.token),
        BotSubscriptionService(),
        RESTfulService(port=config.port),
        log_level=logging.DEBUG if config.debug else logging.INFO,
    ) as loop:
        loop.run_forever()
