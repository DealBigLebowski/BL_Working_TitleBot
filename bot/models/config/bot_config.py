from typing import Union

from pydantic import Field

from ..config_model import ConfigModel


class BotConfig(ConfigModel):
    __filenames__ = ("_config_dev.json", "config.json")

    bot_token: str = Field("API токен из @BotFather")
    admin_user_id: Union[int, str] = Field(
        "User ID администратора бота (можно получить в https://t.me/userinfobot)"
    )
    database_uri: str = Field("sqlite://database.sqlite3")
    timezone: str = Field("Europe/Moscow")

