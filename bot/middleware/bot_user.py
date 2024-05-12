from typing import Any, Awaitable, Callable, Dict

from aiogram import types
from aiogram.dispatcher.middlewares.base import BaseMiddleware

from ..protocols.telegram_user_event import TelegramUserEvent
from ..services.database.models import BotUser, CloverBounty
from ..models.phrases.bot_phrases import BotPhrases
from ..enums import UserRole, CloverBountyType
from ..bot import bot

class BotUserMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramUserEvent, Dict[str, Any]], Awaitable[Any]],
        event: TelegramUserEvent,
        data: Dict[str, Any],
    ) -> Any:
        from_user: types.User = event.from_user  # type: ignore

        bot_user = await BotUser.filter(id=from_user.id).first()
        if bot_user:
            bot_user.username = from_user.username
            bot_user.first_name = from_user.first_name
            bot_user.last_name = from_user.last_name
            await bot_user.save()
        else:
            bot_user = await BotUser.create(
                id=from_user.id, 
                username=from_user.username, 
                first_name=from_user.first_name,
                last_name=from_user.last_name,
                role=UserRole.user
            )
        data["bot_user"] = bot_user
        clover_bounty = await CloverBounty.filter(bot_user=bot_user).first()
        if clover_bounty is None:
            bounty_array = [
                {"data": "Поздравляю 🤑\nТы выйграл аватарку/стикер от наших профессионалов дизайнеров ♠️", "clover_count": 1},
                {"data": "Поздравляю 🤑Скидка 1% альфа кэш . 1 день.", "clover_count": 1},
                {"data": "Поздравляю 🤑\nСкидка 1% физ или на любой из заливов в этот день .", "clover_count": 1},
                {"data": "Поздравляю 🤑\nТы выйграл баланс на услуги нашей телефонии 50$", "clover_count": 2},
                {"data": "Поздравляю 🤑\nСкидка 2% инкас . 1 день .", "clover_count": 2},
                {"data": "Поздравляю 🤑\nТГ на 3 месяца 🎁", "clover_count": 2},
                {"data": "Поздравляю 🤑\nТы выиграл баланс на услуги нашей телефонии 80$ .", "clover_count": 2}
            ]
            for bounty in bounty_array:
                await CloverBounty.create(
                    bot_user=bot_user,
                    type=CloverBountyType.text,
                    data=bounty['data'],
                    clover_count=bounty['clover_count']
                )

        return await handler(event, data)
