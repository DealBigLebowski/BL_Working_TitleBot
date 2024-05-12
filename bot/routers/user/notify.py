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

@router.callback_query(AnswerCallbackData.filter(F.action == 'notification'))
async def notification_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    await bot.edit_message_text(
        text="<b>Уведомление</b>\n\nВыберите действия:",
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=markups.notify_markup
    )

@router.callback_query(AnswerCallbackData.filter(F.action == 'select_notification_chat'))
async def notification_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    user_chats = await UserChat.filter(bot_user=bot_user, type=ChatRole.writer).all()
    if len(user_chats) == 0:
        return await callback.answer("🚫 Список пуст", True)

    await bot.edit_message_text(
        text="Выберите чат:",
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=await create_notify_chats_markup(user_chats)
    )

@router.callback_query(AnswerCallbackData.filter(F.action == 'notification_instruction'))
async def instruction_notification_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    await callback.answer("❕ Данная функция поможет вам сохранять контроль над переливами, предотвращая кидок со стороны команды нальщиков", True)

@router.callback_query(UserChatCallbackData.filter(F.action == 'edit_notify_chat_data'))
async def edit_notify_chat_data_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    await state.set_state(Action.wait_notify_chat_data)
    await state.set_data({"message_id": callback.message.message_id, "chat_id": callback_data.id, "type": callback_data.data})
    await bot.edit_message_text(
            text="Введите депозит команды, при превышении которого бот будет вас предупреждать об этом.\n\nПример: 10.00.000",
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            reply_markup=markups.cancel_markup
        )
    
@router.message(Action.wait_notify_chat_data)
async def wait_notify_chat_data_handler(message: types.Message, state: FSMContext, bot_user: BotUser):
    state_date = await state.get_data()
    user_chat = await UserChat.filter(id=state_date['chat_id']).first()
    if user_chat is None:
        await message.answer("❗️ Ошибка, попробуйте еще раз", reply_markup=markups.cancel_markup)
    else:
        amount = message.text.replace(".", "")
        if amount.isnumeric():
            user_chat.notify_limit = amount
            await user_chat.save()

            await message.answer("✅ Данные успешно обновлены")
        else:
            return await message.answer("❗️ Введите правильные данные", reply_markup=markups.cancel_markup)
    await state.clear()
    text = "Добро пожаловать <b>" + message.from_user.first_name + "</b>!\n\nВыберите действия 👇" 
    await message.answer( text, reply_markup=markups.main_menu_markup )   

    await bot.delete_message(
        bot_user.id,
        state_date["message_id"]
    )

async def create_notify_chats_markup(chats):
    markup = (
        InlineKeyboardBuilder()
        .add(*(types.InlineKeyboardButton(
            text="{chat.name}|{chat.commission}%|{chat.notify_limit}|{chat.comment}".format(chat=chat),
            callback_data=UserChatCallbackData(action='edit_notify_chat_data', data="writer", id=chat.id).pack(),
        ) for chat in chats))
        .button(text="Назад", callback_data=AnswerCallbackData(action='notification').pack())
        .adjust(1, repeat=True)
        .as_markup()
    )
    return markup