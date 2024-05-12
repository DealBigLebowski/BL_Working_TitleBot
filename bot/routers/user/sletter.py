import uuid

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
from ...services.database.models import BotUser, UserChat, SupportUserChat
from ...enums import ChatRole


router.message.filter(F.chat.type == "private")


acd = AnswerCallbackData(action='demo')

@router.callback_query(AnswerCallbackData.filter(F.action == 'sletter_select_chat_type'))
async def select_chat_type_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    select_start_chat_type = (
            InlineKeyboardBuilder()
            .button(text="КЦ/Лейки", callback_data=UserChatCallbackData(action='send_sletter', data='cc', id=0).pack())
            .button(text="Нальщики", callback_data=UserChatCallbackData(action='send_sletter', data='writer', id=0).pack())
            .button(text="Назад", callback_data=AnswerCallbackData(action='main').pack())
            .adjust(1, repeat=True)
            .as_markup()
        )

    await callback.message.edit_text(
        text="Выберите тип гуррпы, для рассылки сообщения 👇",
        reply_markup=select_start_chat_type
    )

@router.callback_query(UserChatCallbackData.filter(F.action == 'send_sletter'))
async def select_chat_type_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    chat_type_name = "КЦ/Лейки" if ChatRole[callback_data.data] == ChatRole.cc else "Нальщики"
    await state.set_data({"user_chat_type": callback_data.data})
    await state.set_state(Action.wait_sletter_text)
    await callback.message.edit_text("Отправьте желаемый текст для рассылку, сообщение будет отправлена вашим группам <b>{chat_type_name}</b> 👇".format(chat_type_name=chat_type_name), reply_markup=markups.cancel_markup)

@router.message(Action.wait_sletter_text, F.text != '/start')
async def advertising_text_handler(message: types.Message, state: FSMContext, bot_user: BotUser):
    state_data = await state.get_data()
    user_chats = await UserChat.filter(bot_user=bot_user, type=ChatRole[state_data['user_chat_type']]).all()
    await bot.send_message(chat_id=bot_user.id, text="Идет расслыка сообщений, пожалуйста подождите")
    sender_count = 0
    for user_chat in user_chats:
        try:
            if message.document:
                await bot.send_document(chat_id=user_chat.id, document=message.document.file_id, caption=message.caption)
            elif message.photo:
                await bot.send_photo(chat_id=user_chat.id, photo=message.photo[-1].file_id, caption=message.caption)
            elif message.video:
                await bot.send_video(chat_id=user_chat.id, video=message.video.file_id, caption=message.caption)
            elif message.text:
                await bot.send_message(chat_id=user_chat.id, text=message.text)
            sender_count += 1
        except:
            pass

    await state.clear()
    await message.answer("✅ Собщение успешно отправлено {count} чатам.".format(count=sender_count))
    await message.answer("Выберите действия 👇 ", reply_markup=markups.main_menu_markup)