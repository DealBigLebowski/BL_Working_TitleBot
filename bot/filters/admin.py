from aiogram.filters.base import Filter

from ..bot import bot
from ..protocols.telegram_user_event import TelegramUserEvent


class AdminFilter(Filter):
    async def __call__(self, telegram_object: TelegramUserEvent):
        if not hasattr(telegram_object, 'from_user'):
            return False

        return telegram_object.from_user.id == bot.config.admin_user_id
