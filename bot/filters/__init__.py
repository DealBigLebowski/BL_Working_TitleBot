from aiogram import types

from ..services.database.models import BotUser


def make_username_from_mention(mention: str) -> str:
    return mention.lstrip("@")


async def bot_user_filter(message: types.Message):
    bot_user = None

    if message.forward_from:
        bot_user = await BotUser.filter(id=message.forward_from.id).first()

    if message.text:
        if message.text.isdigit():
            bot_user = await BotUser.filter(id=int(message.text)).first()
        elif username := make_username_from_mention(message.text):
            bot_user = await BotUser.filter(username=username).first()

    if bot_user is None:
        return False

    return dict(target_bot_user=bot_user)
