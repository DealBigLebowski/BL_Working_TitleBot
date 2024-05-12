from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram import F, types
from aiogram.filters.command import CommandStart
from aiogram.fsm.context import FSMContext


from ... import markups
from ...bot import bot
from ...state import Action
from . import router
from ...callback_data import AnswerCallbackData, UserChatCallbackData
from ...services.database.models import BotUser, UserChat, UserChatAdvertising
from ...enums import ChatRole

router.message.filter(F.chat.type == "private")


acd = AnswerCallbackData(action='demo')

@router.callback_query(AnswerCallbackData.filter(F.action == 'check_rek'))
async def add_chat_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    await bot.edit_message_text(
        text="<b>Проверить рек</b>\n\nВыберите действия:",
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=markups.check_rek_markup
    )

@router.callback_query(AnswerCallbackData.filter(F.action == 'check_rek_instruciton'))
async def instruction_advertising_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    await callback.answer("❕ Чем больше пользователей подключают нашего бота, тем точнее будет поиск выданного вам реквизита в истории запросов/выдачи. Бот не всесильный, поиск проводится лишь по нашей внутренней базе", True)
