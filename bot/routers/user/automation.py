from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram import F, types
from aiogram.filters.command import CommandStart
from aiogram.fsm.context import FSMContext


from ... import markups
from ...bot import bot
from ...state import Action
from . import router
from ...callback_data import AnswerCallbackData, UserChatCallbackData, DeliveryCallbackData
from ...services.database.models import BotUser, UserChat, Delivery
from ...enums import ChatRole

acd = AnswerCallbackData(action='demo')


@router.callback_query(AnswerCallbackData.filter(F.action == 'automation'))
async def automation_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    await bot.edit_message_text(
        text="<b>Автоматизация работы</b>\n\nВыберите действия:",
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=markups.automation_markup
    )

@router.callback_query(UserChatCallbackData.filter(F.action == 'automation_selected_chat'))
async def other_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    await state.clear()
    user_chat = await UserChat.filter(id=callback_data.id).first()
    if user_chat.type == ChatRole.rek:
        return await callback.answer("❕ Данная группа уже добавлена, пожалуйста выберите другой", True)
    user_chat.type = ChatRole.rek
    await user_chat.save()
    await callback.answer("✅ Группа {chat.name} успешно добавлен в список реквизитов, отправьте команду /add в группе чтобы добавить реквизиты".format(chat=user_chat), True)
    await automation_handler(callback, callback_data, state, bot_user)
    # delivery = await Delivery.filter(user_chat=user_chat).all()
    # await bot.edit_message_text(
    #     text="Выберите пустой слот для добавление, или выберите реквизит для редактирования:",
    #     chat_id=callback.message.chat.id,
    #     message_id=callback.message.message_id,
    #     reply_markup= await create_delivery_markup(delivery, user_chat)
    # )

@router.callback_query(AnswerCallbackData.filter(F.action == 'automation_add_rek'))
async def automation_inclode_bot_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    await bot.edit_message_text(
        text="<b>Добавить реквизит</b>\n\nВыберите действия:",
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=markups.automation_include_bot_markup
    )


@router.callback_query(AnswerCallbackData.filter(F.action == 'automation_select_add_rek'))
async def automation_inclode_bot_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    user_chat = await UserChat.filter(bot_user=bot_user, type__in=[ChatRole.none, ChatRole.rek]).all()
    await bot.edit_message_text(
        text="Выберите группу:",
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=await create_user_chat_markup(user_chat)
    )

@router.callback_query(AnswerCallbackData.filter(F.action == 'instruction_function_rek'))
async def instruction_function_rek_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    await callback.answer("❕ Данная функция позволит вам выдавать реквизиты в автоматическом режиме. Для этого добавьте бота в специальную группу для загрузки реквизитов и следуйте дальнейшим инструкциям", True)

@router.callback_query(AnswerCallbackData.filter(F.action == 'instruction_function_day'))
async def instruction_function_day_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    await callback.message.edit_text(
            text="❕ Чтобы поднять к себе интерес и доказать свой профессионализм, можете включить данную функцию.\n\nУсловия следующие:\nФункция работает по хештегу- «#дай». Для примера «#дай нфс 1кк», начинается отсчёт времени 3 минуты , если саппорт не успевает выдать, вам начисляется скидка в 0.5%.  Саппорт в праве запросить доп время (+3мин),  . В случае если сапп не успеет выдать рек за доп. время  - % удваиваются и скидка на выдачу река будет 1%",
            reply_markup=await markups.create_back_markup(AnswerCallbackData(action="automation_function_day").pack())
        )

@router.callback_query(AnswerCallbackData.filter(F.action == 'automation_function_rek'))
async def automation_function_rek_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    text="<b>Функция Рек</b>\n\nСтатус: {status}".format(status="✅ Включен" if bot_user.function_rek else "🚫 Выключен")
    await bot.edit_message_text(
        text=text,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=await create_function_keyboard("on_function_rek", "off_function_rek", "instruction_function_rek")
    )

@router.callback_query(AnswerCallbackData.filter(F.action == 'on_function_rek'))
async def on_function_rek_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    bot_user.function_rek = True
    await bot_user.save()
    await callback.answer("✅ Функция Рек успешно включена")
    await automation_function_rek_handler(callback, callback_data, state, bot_user)

@router.callback_query(AnswerCallbackData.filter(F.action == 'off_function_rek'))
async def off_function_rek_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    bot_user.function_rek = False
    await bot_user.save()
    await callback.answer("🚫 Функция Рек успешно выключена")
    await automation_function_rek_handler(callback, callback_data, state, bot_user)

@router.callback_query(AnswerCallbackData.filter(F.action == 'automation_function_day'))
async def automation_function_day_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    text="<b>Функция Дай</b>\n\nСтатус: {status}".format(status="✅ Включен" if bot_user.function_day else "🚫 Выключен")
    await bot.edit_message_text(
        text=text,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=await create_function_keyboard("on_function_day", "off_function_day", "instruction_function_day")
    )


@router.callback_query(AnswerCallbackData.filter(F.action == 'on_function_day'))
async def on_function_day_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    bot_user.function_day = True
    await bot_user.save()
    await callback.answer("✅ Функция Дай успешно включена")
    await automation_function_day_handler(callback, callback_data, state, bot_user)

@router.callback_query(AnswerCallbackData.filter(F.action == 'off_function_day'))
async def off_function_day_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    bot_user.function_day = False
    await bot_user.save()
    await callback.answer("🚫 Функция Дай успешно выключена")
    await automation_function_day_handler(callback, callback_data, state, bot_user)

async def create_function_keyboard(active_data, deactive_data, instruction_data):
    markup = (
        InlineKeyboardBuilder()
        .button(text="Активировать", callback_data=AnswerCallbackData(action=active_data).pack())
        .button(text="Деактивировать", callback_data=AnswerCallbackData(action=deactive_data).pack())
        .button(text="Подробнее", callback_data=AnswerCallbackData(action=instruction_data).pack())
        .button(text="Назад", callback_data=AnswerCallbackData(action="automation").pack())
        .adjust(1, repeat=True)
        .as_markup()
    )
    return markup

async def create_user_chat_markup(chats):
    markup = (
        InlineKeyboardBuilder()
        .add(*(types.InlineKeyboardButton(
            text="{chat_name}".format(chat_name=chat.name if chat.type == ChatRole.none else "✅ {name}".format(name=chat.name)),
            callback_data=UserChatCallbackData(action='automation_selected_chat', data="", id=chat.id).pack(),
        ) for chat in chats))
        .button(text="Назад", callback_data=AnswerCallbackData(action='automation_add_rek').pack())
        .adjust(1, repeat=True)
        .as_markup()
    )
    return markup
