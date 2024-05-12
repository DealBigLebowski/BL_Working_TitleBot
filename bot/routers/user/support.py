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
    
@router.callback_query(AnswerCallbackData.filter(F.action == 'support'))
async def add_chat_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    await bot.edit_message_text(
        text="<b>Поддержка</b>\n\nВыберите действия:",
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=markups.support_markup
    )

@router.callback_query(AnswerCallbackData.filter(F.action == 'about'))
async def instruction_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    text = "<b>О нас</b>\n\n👨‍💻 Команда «BigLebowski» создала бота, который поможет вам контролировать работу во всех ваших рабочих группах, анализировать ваши доходы, проводить розыграши среди ваших клиентов, оповещать о специальных предложениях, автоматизировать выдачу реквизито и многое другое. Описание функций прописано во вкладках «Подробнее»"
    await bot.edit_message_text(
            text=text,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            reply_markup=await markups.create_back_markup(AnswerCallbackData(action="support").pack())

        )

@router.callback_query(AnswerCallbackData.filter(F.action == 'support_contact'))
async def instruction_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    text = "<b>Тех. Поддержка</b>\n\nПо всем техническим и общим вопросам, касательно работы проекта, обращайтесь в техническую поддержку"
    await bot.edit_message_text(
            text=text,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            reply_markup=await markups.create_back_markup(AnswerCallbackData(action="support").pack())

        )


@router.callback_query(AnswerCallbackData.filter(F.action == 'support_faq'))
async def instruction_advertising_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    await callback.answer("❕ В разработке", True)
