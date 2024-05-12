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
from ...callback_data import AnswerCallbackData, CloverBountyCallbackData, UserChatCallbackData
from ...services.database.models import BotUser, UserChat, CloverBounty, Clover
from ...enums import CloverBountyType, ChatRole

router.message.filter(F.chat.type == "private")


acd = AnswerCallbackData(action='demo')

@router.callback_query(AnswerCallbackData.filter(F.action == 'interactives'))
async def interactives_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    await bot.edit_message_text(
        text="<b>Интерактивы для клиентов</b>\n\nВыберите действия:",
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=markups.interactives_markup
    )

@router.callback_query(AnswerCallbackData.filter(F.action == 'interactives_instruciton'))
async def instruction_interactives_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    await callback.answer("❕ Данная функция предназначена для оживления чата путем розыгрышей призов. Призы вы размещаете сами, или заменяете старые. Претендовать на призы могут группы в которых есть хоть 1 «Билет Удачи»", True)

@router.callback_query(AnswerCallbackData.filter(F.action == 'setting_get_status'))
async def setting_get_status_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    await callback.answer("❕ None", True)

@router.callback_query(AnswerCallbackData.filter(F.action == 'interactives_add_clover_bounty'))
async def setting_set_support_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    clover_bounty = await CloverBounty.filter(bot_user=bot_user).all()
    await bot.edit_message_text(
        text="Выберите слот для добавления/редактирования призов:",
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=await create_clover_bounty_markup(clover_bounty)
    )

@router.callback_query(AnswerCallbackData.filter(F.action == 'interactives_set_clover_amount'))
async def add_support_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    await state.clear()
    text="Введите сумму. Далее все КЦ/Лейки пролившие больше данной суммы за сутки получат «Билет Удачи» и с его помощью смогут разыграть с вами приз.\n\nПример: 1.000.000"
    await state.set_state(Action.wait_clover_limit_amount)
    await state.set_data({"message_id": callback.message.message_id})
    await bot.edit_message_text(
            text=text,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            reply_markup=markups.cancel_markup
        )

@router.message(Action.wait_clover_limit_amount)
async def wait_support_username_handler(message: types.Message, state: FSMContext, bot_user: BotUser):
    
    amount = message.text.replace(".", "")
    if amount.isnumeric():
        bot_user.clover_limit = amount
        await bot_user.save()
        await message.answer("✅ Условия для билета успешно обновлен")
    else:
        return await message.answer("❗️ Ошибка, Введите правильные данные" , reply_markup=markups.cancel_markup)
        
            
    await state.clear()
    text = "Добро пожаловать <b>" + message.from_user.first_name + "</b>!\n\nВыберите действия 👇" 
    await message.answer( text, reply_markup=markups.main_menu_markup )   
    state_date = await state.get_data()

    await bot.delete_message(
        bot_user.id,
        state_date["message_id"]
    )

@router.callback_query(CloverBountyCallbackData.filter(F.action == 'edit_clover_bounty'))
async def edit_clover_bounty_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    await state.clear()
    await state.set_data({"message_id": callback.message.message_id, "clover_bounty_id": callback_data.id})
    text = "Выберите количество билетов для данного приза:"
    await bot.edit_message_text(
            text=text,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            reply_markup=markups.bounty_clover_count
        )
    # text="Введите краткое описание приза.\n\nПример: «1000 строк базы»; «50$ на пополнение телефонии»"
    # await state.set_state(Action.wait_clover_bounty_data)
    # await bot.edit_message_text(
    #         text=text,
    #         chat_id=callback.message.chat.id,
    #         message_id=callback.message.message_id,
    #         reply_markup=markups.cancel_markup
    #     )

@router.callback_query(CloverBountyCallbackData.filter(F.action == 'bounty_clover_count'))
async def bounty_clover_count_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    state_date = await state.get_data()
    state_date["clover_count"] = callback_data.id
    await state.set_data(state_date)
    text="Введите краткое описание приза.\n\nПример: «1000 строк базы»; «50$ на пополнение телефонии»"
    await state.set_state(Action.wait_clover_bounty_data)
    await bot.edit_message_text(
            text=text,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            reply_markup=markups.cancel_markup
        )

@router.message(Action.wait_clover_bounty_data)
async def wait_support_username_handler(message: types.Message, state: FSMContext, bot_user: BotUser):
    state_date = await state.get_data()
    clover_bounty = await CloverBounty.filter(id=state_date["clover_bounty_id"]).first()
    if clover_bounty is None:
        await CloverBounty.create(
            bot_user=bot_user,
            type=CloverBountyType.text,
            data=message.text,
            clover_count=state_date['clover_count']
        )
    else:
        clover_bounty.data = message.text
        clover_bounty.clover_count=state_date['clover_count']
        await clover_bounty.save()
    
    await message.answer("✅ Данные успешно обновлены")
        
    await state.clear()
    text = "Добро пожаловать <b>" + message.from_user.first_name + "</b>!\n\nВыберите действия 👇" 
    await message.answer( text, reply_markup=markups.main_menu_markup )   

    await bot.delete_message(
        bot_user.id,
        state_date["message_id"]
    )


@router.callback_query(AnswerCallbackData.filter(F.action == 'interactives_issue_clover'))
async def add_support_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    user_chats = await UserChat.filter(bot_user=bot_user, type=ChatRole.cc).all()
    if len(user_chats) == 0:
        return await callback.answer("🚫 Список групп КЦ/Лейки пуст", True)

    await bot.edit_message_text(
        text="Выберите какой группе вы хотите выдать внеочередной «Билет удачи»:",
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=await create_notify_chats_markup(user_chats)
    )

@router.callback_query(UserChatCallbackData.filter(F.action == 'issue_clover'))
async def add_support_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    user_chat = await UserChat.filter(id=callback_data.id).first()
    if user_chat is None:
        return await callback.answer("🚫 Чат не найден", True)
    
    clover = await Clover.filter(user_chat=user_chat).first()
    if clover is None:
        clover = await Clover.create(
            user_chat=user_chat,
            count=1
        )
    else:
        if clover.count >= 3:
            return await callback.answer("❗️ Ошибка, максимальное разрешенное количество билетов 3" , True)
        clover.count = clover.count + 1
        await clover.save()

    back_markup = (
        InlineKeyboardBuilder()
        .button(text="Назад", callback_data=AnswerCallbackData(action='interactives_issue_clover').pack())
        .adjust(1, repeat=True)
        .as_markup()
    )
    text = "🎟️ Начисление Билета\n\n💬 Чат:  {user_chat.name}\n🎟️ Билетов: {clover.count}".format(user_chat=user_chat, clover=clover)

    await bot.edit_message_text(
        text=text,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=back_markup
    ) 

async def create_clover_bounty_markup(clover_bounty):
    markup = (
        InlineKeyboardBuilder()
        .add(*(types.InlineKeyboardButton(
            text="🎟️ {clover_count} - ({text}...)".format(text=clover.data[:10],clover_count=clover.clover_count),
            callback_data=CloverBountyCallbackData(action='edit_clover_bounty', id=clover.id).pack(),
        ) for clover in clover_bounty))
        .add(*(types.InlineKeyboardButton(
            text="[             ]",
            callback_data=CloverBountyCallbackData(action='edit_clover_bounty', id=0).pack(),
        ) for clover in range(4 - len(clover_bounty))))
        .button(text="Назад", callback_data=AnswerCallbackData(action='interactives').pack())
        .adjust(1, repeat=True)
        .as_markup()
    )
    return markup

async def create_notify_chats_markup(chats):
    markup = (
        InlineKeyboardBuilder()
        .add(*(types.InlineKeyboardButton(
            text="{chat.name}".format(chat=chat),
            callback_data=UserChatCallbackData(action='issue_clover', data="cc", id=chat.id).pack(),
        ) for chat in chats))
        .button(text="Назад", callback_data=AnswerCallbackData(action='interactives').pack())
        .adjust(1, repeat=True)
        .as_markup()
    )
    return markup