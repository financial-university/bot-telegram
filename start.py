from os import getenv
from dataclasses import dataclass

from app import start_app


@dataclass(frozen=True)
class Config:
    token: str = getenv("TOKEN") or None
    host: str = getenv("HOST") or "tg.uname.su"
    listen: str = getenv("LISTEN") or "0.0.0.0"
    db_host: str = getenv("DB_HOST") or "localhost"
    db_port: int = int(getenv("DB_PORT") or 5432)
    db_user: str = getenv("DB_USER") or "root"
    db_password: str = getenv("DB_PASSWORD") or "password"
    db_database: str = getenv("DB_DATABASE") or "bot"
    db_connect_timeout: int = 18000
    debug: bool = getenv("DEBUG") != "False"

    @property
    def url(self):
        return f"https://{self.host}/telegram/api"


if __name__ == "__main__":

    config = Config(
        token="993105879:AAGlZtLWyNyAbPxlXDbc3p8A2ebWk9jg12U",
        debug=True,
        db_port=5432,
        db_database="bot",
        db_user="postgres",
        db_password="postgres",
    )

    start_app(config)
