from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram import F, types
from aiogram.filters.command import CommandStart
from aiogram.fsm.context import FSMContext
import math


from ... import markups
from ...bot import bot
from ...state import Action
from . import router
from ...callback_data import AnswerCallbackData, UserChatCallbackData, UserChatPaginationCallbackData
from ...services.database.models import BotUser, UserChat
from ...enums import ChatRole

router.message.filter(F.chat.type == "private")

acd = AnswerCallbackData(action='demo')

@router.callback_query(AnswerCallbackData.filter(F.action == 'skip_text'))
async def main_handaler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    await bot.delete_message(callback.message.chat.id, callback.message.message_id)

@router.callback_query(AnswerCallbackData.filter(F.action == 'main'))
async def main_handaler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    await state.clear()
    text = "Добро пожаловать <b>" + callback.from_user.first_name + "</b>!\n\nВыберите действия 👇" 
    await bot.edit_message_text(
        text=text,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=markups.main_menu_markup
    )

@router.callback_query(AnswerCallbackData.filter(F.action == 'add_chat'))
async def add_chat_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    await bot.edit_message_text(
        text="<b>Добавить в группу</b>\n\nВыберите действия:",
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=markups.add_chat_markup
    )

@router.callback_query(UserChatCallbackData.filter(F.action == 'select_action'))
async def set_type_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    select_action = (
        InlineKeyboardBuilder()
        .button(text="Добавить новую", callback_data=UserChatPaginationCallbackData(action='select_chat', data=callback_data.data, id=0, page=1).pack())
        .button(text="Инструкция", callback_data=AnswerCallbackData(action='instruction').pack())
        .button(text="Назад", callback_data=AnswerCallbackData(action='add_chat').pack())
        .adjust(1, repeat=True)
        .as_markup()
    )

    await bot.edit_message_text(
        text="Выберите действия:",
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=select_action
    )
    
@router.callback_query(UserChatPaginationCallbackData.filter(F.action == 'select_chat'))
async def set_type_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    user_chats = await UserChat.filter(bot_user=bot_user, type=ChatRole.none).prefetch_related("bot_user").all()
    if len(user_chats) == 0:
        return await callback.answer("🚫 Список пуст, добавьте бота в группу с правами администратора", True)

    await bot.edit_message_text(
        text="Выберите чат:",
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=await create_chats_markup(user_chats, callback_data.data, callback_data.page)
    )

@router.callback_query(UserChatCallbackData.filter(F.action == 'set_type'))
async def set_type_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    
    user_chat = await UserChat.filter(id=callback_data.id).first()
    user_chat.type = ChatRole[callback_data.data]
    await user_chat.save()
    await callback.answer("✅ Данные успешно обновлены")
    await state.clear()

    await main_handaler(callback, callback_data, state, bot_user)


@router.callback_query(AnswerCallbackData.filter(F.action == 'instruction'))
async def instruction_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    await callback.answer("❕ Необходимо задать класификацию группы, для этого выбирите группу подкласа «КЦ»(«Команды нальщиков») из списка не распределенных групп", True)

async def create_chats_markup(chats, callback_data, page=1):
    limit = 10
    initial_page = (page - 1) * limit
    total_rows = len(chats)
    total_pages = math.ceil (total_rows / limit); 
    user_chats = await UserChat.filter(bot_user=chats[0].bot_user, type=ChatRole.none).limit(limit).offset(initial_page).all()
    
    buttons = []
    for chat in user_chats:
        buttons.append([types.InlineKeyboardButton(
            text=chat.name,
            callback_data=UserChatCallbackData(action='set_type', data=callback_data, id=chat.id).pack(),
        )])
    if page == 1 and total_pages > page:
        buttons.append( [
            types.InlineKeyboardButton(text="🔜", callback_data=UserChatPaginationCallbackData(action='select_chat', data=callback_data, id=0, page=(page + 1)).pack())
        ])
    elif total_pages > page:
        buttons.append( [
            types.InlineKeyboardButton(text="🔙", callback_data=UserChatPaginationCallbackData(action='select_chat', data=callback_data, id=0, page=(page - 1)).pack()),
            types.InlineKeyboardButton(text="🔜", callback_data=UserChatPaginationCallbackData(action='select_chat', data=callback_data, id=0, page=(page + 1)).pack())
        ])
    elif page > 1 and total_pages == page:
         buttons.append( [
            types.InlineKeyboardButton(text="🔙", callback_data=UserChatPaginationCallbackData(action='select_chat', data=callback_data, id=0, page=(page - 1)).pack()),
        ])
    buttons.append([types.InlineKeyboardButton(text="Назад", callback_data=UserChatCallbackData(action='select_action', data=callback_data, id=0).pack())])
    return types.InlineKeyboardMarkup(inline_keyboard=buttons)