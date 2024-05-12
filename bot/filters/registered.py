from aiogram.filters.base import Filter

from ..protocols.telegram_user_event import TelegramUserEvent, TelegramMessageEvent
from ..services.database.models import BotUser, UserChat, SupportUserChat
from ..models.phrases.bot_phrases import BotPhrases

from ..bot import bot
from tortoise.expressions import Q

class RegisteredFilter(Filter):
    def __init__(self, *, registered: bool):
        self.registered = registered

    async def __call__(self, event: TelegramUserEvent, **data):
        return True

class SupportFilter(Filter):
    def __init__(self, *, support: bool):
        self.support = support

    async def __call__(self, message: TelegramMessageEvent):
        is_support = True
        bot_user = await BotUser.filter(id=message.from_user.id).first()
        if bot_user:
            chat_id = message.chat.id if hasattr(message, 'chat') else message.message.chat.id
            user_chat = await UserChat.filter(id=chat_id, bot_user=bot_user).first()
            if user_chat:
                return is_support
            else:
                supports = await SupportUserChat.filter(
                    Q(Q(other_bot_user=bot_user), Q(username=bot_user.username), join_type="OR"),
                    ).prefetch_related("bot_user").all()
                if supports:
                    for support in supports:
                        if support.username:
                            support.other_bot_user = bot_user
                            support.username=""
                            await support.save()
                        user_chat = await UserChat.filter(id=chat_id, bot_user=support.bot_user).first()
                        if user_chat:
                            return is_support
        return not is_support