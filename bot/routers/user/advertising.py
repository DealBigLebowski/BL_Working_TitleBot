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

@router.callback_query(AnswerCallbackData.filter(F.action == 'advertising'))
async def advertising_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    await bot.edit_message_text(
        text="<b>Реклама в закрепе</b>\n\nВыберите действия:",
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=markups.advertising_markup
    )

@router.callback_query(AnswerCallbackData.filter(F.action == 'advertising_instruciton'))
async def instruction_advertising_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    await callback.answer("❕ Данная функция позволяет вам разместить любое рекламное предложение в закрепленной стате у всех ваших рабочих групп с подкласа «КЦ».", True)


@router.callback_query(AnswerCallbackData.filter(F.action == 'advertising_chat_type'))
async def advertising_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    await bot.edit_message_text(
        text="<b>Ввести текст</b>\n\nВыберите тип группы:",
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=markups.advertising_chat_type_markup
    )

@router.callback_query(UserChatCallbackData.filter(F.action == 'enter_advertising_text'))
async def advertising_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    await state.clear()
    await state.set_state(Action.wait_advertising_text)
    await state.set_data({"message_id": callback.message.message_id, "user_chat_type": callback_data.data})
    await bot.edit_message_text(
        text="Введите текст для рекламы:",
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=markups.cancel_markup
    )

@router.message(Action.wait_advertising_text)
async def advertising_text_handler(message: types.Message, state: FSMContext, bot_user: BotUser):
    state_date = await state.get_data()
    advertising = await UserChatAdvertising.filter(bot_user=bot_user, user_chat_type=ChatRole[state_date['user_chat_type']]).first()
    if advertising is None:
        await UserChatAdvertising.create(
            bot_user=bot_user,
            text=message.text,
            user_chat_type=ChatRole[state_date['user_chat_type']]
        )
    else:
        advertising.text = message.text
        await advertising.save()
    
    

    await message.answer("✅ Данные успешно обновлены")
    await state.clear()
    text = "Добро пожаловать <b>" + message.from_user.first_name + "</b>!\n\nВыберите действия 👇" 
    await message.answer( text, reply_markup=markups.main_menu_markup )   

    await bot.delete_message(
        bot_user.id,
        state_date["message_id"]
    )