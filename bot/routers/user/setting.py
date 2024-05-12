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
from ...callback_data import AnswerCallbackData, SupportUserChatCallbackData
from ...services.database.models import BotUser, UserChat, SupportUserChat
from ...enums import ChatRole

router.message.filter(F.chat.type == "private")


acd = AnswerCallbackData(action='demo')

@router.callback_query(AnswerCallbackData.filter(F.action == 'settings'))
async def setting_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    await bot.edit_message_text(
        text="<b>Настройки кабинета</b>\n\nВыберите действия:",
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=markups.settings_markup
    )

@router.callback_query(AnswerCallbackData.filter(F.action == 'setting_instruciton'))
async def instruction_setting_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    await callback.answer("❕ None", True)

@router.callback_query(AnswerCallbackData.filter(F.action == 'setting_get_status'))
async def setting_get_status_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    await callback.answer("❕ None", True)

@router.callback_query(AnswerCallbackData.filter(F.action == 'setting_set_support'))
async def setting_set_support_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    support_user_chat = await SupportUserChat.filter(bot_user=bot_user, other_bot_user_id__not=bot_user.id).prefetch_related("other_bot_user").all()
    await bot.edit_message_text(
        text="Выберите действия:",
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=await create_support_user_markup(support_user_chat)
    )

@router.callback_query(AnswerCallbackData.filter(F.action == 'add_support'))
async def add_support_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    await state.clear()
    text="Введите логин саппорта.\n\n"
    await state.set_state(Action.wait_support_username)
    await state.set_data({"message_id": callback.message.message_id})
    await bot.edit_message_text(
            text=text,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            reply_markup=markups.cancel_markup
        )


@router.callback_query(AnswerCallbackData.filter(F.action == 'setting_set_company_name'))
async def add_support_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    company_name = bot_user.company_name if bot_user.company_name else "Не указан"
    text = "Название вашей компании - <b>{company_name}</b>\n\nВведите новое название:".format(company_name=company_name)
    await state.set_state(Action.wait_company_name)
    await state.set_data({"message_id": callback.message.message_id})

    await bot.edit_message_text(
            text=text,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            reply_markup=markups.cancel_markup
        )
    

@router.message(Action.wait_company_name, F.text)
async def wait_support_username_handler(message: types.Message, state: FSMContext, bot_user: BotUser):
    state_date = await state.get_data()
    bot_user.company_name = message.text
    await bot_user.save()
    await message.answer("✅ Название компании изменено на <b>{message.text}</b> он будет отображен в закрепленных сообщениях.".format(message=message))
            
    await state.clear()
    text = "Добро пожаловать <b>" + message.from_user.first_name + "</b>!\n\nВыберите действия 👇" 
    await message.answer( text, reply_markup=markups.main_menu_markup )   

    await bot.delete_message(
        bot_user.id,
        state_date["message_id"]
    )

@router.message(Action.wait_support_username)
async def wait_support_username_handler(message: types.Message, state: FSMContext, bot_user: BotUser):
    state_date = await state.get_data()
    username = message.text.replace("@", "")
    other_user = await BotUser.filter(username=username).first()
    if username == message.from_user.username:
        return await message.answer("❗️ Ошибка, Вы не можете добавить себя", reply_markup=markups.cancel_markup)
    if other_user is None:
        support_user_chat = await SupportUserChat.filter(bot_user=bot_user, username=username).first()
        if support_user_chat:
            await message.answer("❗️ Ошибка, пользователь уже добавлен в список для @{username}".format(username=username))
        else:
            support_user_chat = await SupportUserChat.create(
                    bot_user=bot_user, 
                    other_bot_user=bot_user,
                    username=username
                )
            await message.answer("✅ Саппорт <b>@{username}</b> успешно добавлен в список".format(username=username))
    else:
        support_user_chat = await SupportUserChat.filter(bot_user=bot_user, other_bot_user=other_user).first()

        if support_user_chat:
            return await message.answer("❗️ Ошибка, пользователь уже добавлен в список" , reply_markup=markups.cancel_markup)
        else:
            support_user_chat = await SupportUserChat.create(
                    bot_user=bot_user, 
                    other_bot_user=other_user
                )
            await message.answer("✅ Саппорт <b>{other_user.first_name}</b> успешно добавлен в список".format(other_user=other_user))
            
    await state.clear()
    text = "Добро пожаловать <b>" + message.from_user.first_name + "</b>!\n\nВыберите действия 👇" 
    await message.answer( text, reply_markup=markups.main_menu_markup )   

    await bot.delete_message(
        bot_user.id,
        state_date["message_id"]
    )

@router.callback_query(SupportUserChatCallbackData.filter(F.action == 'edit_support_user'))
async def edit_support_user_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    support_user_chat = await SupportUserChat.filter(id=callback_data.id).prefetch_related("other_bot_user").first()
    text="ID: {other_user.id}\nИмя: {other_user.first_name}\nЛогин: @{other_user.username}\n\nВыберите действия для этого пользователя:".format(other_user=support_user_chat.other_bot_user)
        
    action_markup = (
        InlineKeyboardBuilder()
        .button(text="Удалить", callback_data=SupportUserChatCallbackData(action='remove_support_user_chat', id=callback_data.id, other_user=support_user_chat.other_bot_user.id).pack())
        .button(text="Назад", callback_data=AnswerCallbackData(action='setting_set_support').pack())
        .adjust(1, repeat=True)
        .as_markup()
    )

    await bot.edit_message_text(
            text=text,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            reply_markup=action_markup
        )

@router.callback_query(SupportUserChatCallbackData.filter(F.action == 'remove_support_user_chat'))
async def remove_support_user_chat_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    support_user_chat = await SupportUserChat.filter(id=callback_data.id).first()
    if support_user_chat:
        await support_user_chat.delete()

    action_markup = (
        InlineKeyboardBuilder()
        .button(text="Назад", callback_data=AnswerCallbackData(action='setting_set_support').pack())
        .adjust(1, repeat=True)
        .as_markup()
    )

    await bot.edit_message_text(
            text="✅ Данные успешно удалены",
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            reply_markup=action_markup
        )

async def create_support_user_markup(support_user_chat):
    markup = (
        InlineKeyboardBuilder()
        .add(*(types.InlineKeyboardButton(
            text="{user.username}".format(user=user.other_bot_user),
            callback_data=SupportUserChatCallbackData(action='edit_support_user', id=user.id, other_user=user.other_bot_user.id).pack(),
        ) for user in support_user_chat))
        .button(text="Добавить саппорта", callback_data=AnswerCallbackData(action='add_support').pack())
        .button(text="Назад", callback_data=AnswerCallbackData(action='settings').pack())
        .adjust(1, repeat=True)
        .as_markup()
    )
    return markup