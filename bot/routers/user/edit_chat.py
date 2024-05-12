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

@router.callback_query(AnswerCallbackData.filter(F.action == 'edit_chat'))
async def edit_chat_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    await bot.edit_message_text(
        text="<b>Редакция групп</b>\n\nВыберите действия:",
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=markups.edit_chat_markup
    )

@router.callback_query(UserChatCallbackData.filter(F.action == 'edit_chat_select_action'))
async def edit_chat_select_action_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    select_action = (
        InlineKeyboardBuilder()
        .button(text="Редактировать из списка", callback_data=UserChatPaginationCallbackData(action='select_edit_chat', data=callback_data.data, id=0, page=1).pack())
        .button(text="Подробнее", callback_data=UserChatCallbackData(action='edit_chat_instruction', data=callback_data.data, id=0).pack())
        .button(text="Назад", callback_data=AnswerCallbackData(action='edit_chat').pack())
        .adjust(1, repeat=True)
        .as_markup()
    )

    await bot.edit_message_text(
        text="Выберите действия:",
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=select_action
    )
    
@router.callback_query(UserChatPaginationCallbackData.filter(F.action == 'select_edit_chat'))
async def set_type_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    user_chats = await UserChat.filter(bot_user=bot_user, type=ChatRole[callback_data.data]).prefetch_related("bot_user").all()
    if len(user_chats) == 0:
        return await callback.answer("🚫 Список пуст", True)

    await bot.edit_message_text(
        text="Выберите чат:",
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=await create_edit_chats_markup(user_chats, callback_data.data, callback_data.page)
    )

@router.callback_query(UserChatCallbackData.filter(F.action == 'select_edit_action'))
async def select_edit_action_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    user_chat = await UserChat.filter(id=callback_data.id).first()
    
    if ChatRole[callback_data.data] == ChatRole.cc:
        type_text = "Нальщики"
        move_type = "writer"
    elif ChatRole[callback_data.data] == ChatRole.writer:
        type_text = "КЦ/ЛейкиЦ"
        move_type = "cc"
    
    markup = (
        InlineKeyboardBuilder()
        .button(text="Изменить данные", callback_data=UserChatCallbackData(action='edit_chat_data', data=callback_data.data, id=callback_data.id).pack())
        .button(text="Переместить в {type_text}".format(type_text=type_text), callback_data=UserChatCallbackData(action='move_chat_type', data=move_type, id=callback_data.id).pack())
        .button(text="Удалить", callback_data=UserChatCallbackData(action='remove_user_chat', data="confirmation-{data}".format(data=callback_data.data), id=callback_data.id).pack())
        .button(text="Назад", callback_data=UserChatPaginationCallbackData(action='select_edit_chat', data=callback_data.data, id=0, page=1))
        .adjust(1, repeat=True)
        .as_markup()
    )

    await bot.edit_message_text(
            text="Выбран чат <b>{user_chat.name}</b>\n\nВыберите тип редактирования:".format(user_chat=user_chat),
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            reply_markup=markup
        )

@router.callback_query(UserChatCallbackData.filter(F.action == 'move_chat_type'))
async def move_chat_type_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
   user_chat = await UserChat.filter(id=callback_data.id).first()
   user_chat.type = ChatRole[callback_data.data]
   await user_chat.save()
   await callback.answer("✅ Чат {user_chat.name}  успешно перемешен".format(user_chat=user_chat), True)
   await edit_chat_handler(callback, callback_data, state, bot_user)

@router.callback_query(UserChatCallbackData.filter(F.action == 'remove_user_chat'))
async def remove_user_chat_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
   user_chat = await UserChat.filter(id=callback_data.id).first()
   if callback_data.data.find("confirmation") != -1:
       explode = callback_data.data.split("-")
       markup = (
            InlineKeyboardBuilder()
            .button(text="Подтвердить", callback_data=UserChatCallbackData(action='remove_user_chat', data="confirm", id=callback_data.id).pack())
            .button(text="Отменить", callback_data=UserChatCallbackData(action='select_edit_action', data=explode[1], id=callback_data.id))
            .adjust(1, repeat=True)
            .as_markup()
        )
       text = "<b>Подтвердите действие</b>\n\n❗️ Группа <b>{user_chat.name}</b> будет удалена со всеми его заявками/данными".format(user_chat=user_chat)
       return await callback.message.edit_text(text=text,reply_markup=markup)
   await user_chat.delete()
   await callback.answer("✅ Чат {user_chat.name}  успешно удален".format(user_chat=user_chat), True)
   await edit_chat_handler(callback, callback_data, state, bot_user)

@router.callback_query(UserChatCallbackData.filter(F.action == 'edit_chat_data'))
async def edit_chat_data_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    await state.clear()
    if ChatRole[callback_data.data] == ChatRole.cc:
        text="Введите данные для группы в формате: Процент чата|Комментарий для себя» \n\nПример: <code>10%|альфа кеш вкусный проц</code>"
    elif ChatRole[callback_data.data] == ChatRole.writer:
        text="Введите данные для группы в формате: Депозит увед.|Процент чата|Комментарий для себя\n\nПример: <code>100к|10%|альфа кеш вкусный проц</code>"
    await state.set_state(Action.wait_chat_data)
    await state.set_data({"message_id": callback.message.message_id, "chat_id": callback_data.id, "type": callback_data.data})
    await bot.edit_message_text(
            text=text,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            reply_markup=markups.cancel_markup
        )

@router.message(Action.wait_chat_data)
async def wait_chat_data_handler(message: types.Message, state: FSMContext, bot_user: BotUser):
    state_date = await state.get_data()
    user_chat = await UserChat.filter(id=state_date['chat_id']).first()
    if user_chat is None:
        await message.answer("Ошибка, попробуйте еще раз", reply_markup=markups.cancel_markup)
    else:
        array_data = message.text.split("|")
        if ChatRole[state_date['type']] == ChatRole.cc:
            check_len = 2
        elif ChatRole[state_date['type']] == ChatRole.writer:
            check_len = 3
        if len(array_data) == check_len:
            for i in range(len(array_data)):
                if array_data[i] == '':
                    return await message.answer("Все поля должны бять заполнены", reply_markup=markups.cancel_markup)
            user_chat.commission = array_data[check_len - 2].replace("%", "")
            user_chat.comment = array_data[check_len - 1]
            if check_len == 3:
                upper_data = array_data[0].upper()
                if upper_data.find("К"):
                    limit = int(upper_data.replace("К", "")) * 1000
                else:
                    limit = array_data[0].replace(".", "")
                user_chat.notify_limit = limit
            await user_chat.save()

            await message.answer("✅ Данные успешно обновлены")
        else:
            return await message.answer("Введите правильные данные", reply_markup=markups.cancel_markup)
    await state.clear()
    text = "Добро пожаловать <b>" + message.from_user.first_name + "</b>!\n\nВыберите действия 👇" 
    await message.answer( text, reply_markup=markups.main_menu_markup )   

    await bot.delete_message(
        bot_user.id,
        state_date["message_id"]
    )

@router.callback_query(UserChatCallbackData.filter(F.action == 'edit_chat_instruction'))
async def edit_chat_instruction_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    if ChatRole[callback_data.data] == ChatRole.writer:
        return await callback.answer("❕ Данная функция позволит вам различать группы Команд Нальщиков, для более удобного и точного создания статистики по работе с ними", True)
    await callback.answer("❕ Данная функция позволит вам различать группы КЦ/Лейки, для более удобного и точного создания статистики по работе с ними", True)

async def create_edit_chats_markup(chats, callback_data, page=1):
    # markup = (
    #     InlineKeyboardBuilder()
    #     .add(*(types.InlineKeyboardButton(
    #         text=create_chat_name(chat, callback_data),
    #         callback_data=UserChatCallbackData(action='select_edit_action', data=callback_data, id=chat.id).pack(),
    #     ) for chat in chats))
    #     .button(text="Назад", callback_data=UserChatCallbackData(action='edit_chat_select_action', data=callback_data, id=0).pack())
    #     .adjust(1, repeat=True)
    #     .as_markup()
    # )
    limit = 10
    initial_page = (page - 1) * limit
    total_rows = len(chats)
    total_pages = math.ceil (total_rows / limit); 
    user_chats = await UserChat.filter(bot_user=chats[0].bot_user, type=ChatRole[callback_data]).limit(limit).offset(initial_page).all()
    
    buttons = []
    for chat in user_chats:
        buttons.append([types.InlineKeyboardButton(
            text=create_chat_name(chat, callback_data),
            callback_data=UserChatCallbackData(action='select_edit_action', data=callback_data, id=chat.id).pack(),
        )])
    if page == 1 and total_pages > page:
        buttons.append( [
            types.InlineKeyboardButton(text="🔜", callback_data=UserChatPaginationCallbackData(action='select_edit_chat', data=callback_data, id=0, page=(page + 1)).pack())
        ])
    elif total_pages > page:
        buttons.append( [
            types.InlineKeyboardButton(text="🔙", callback_data=UserChatPaginationCallbackData(action='select_edit_chat', data=callback_data, id=0, page=(page - 1)).pack()),
            types.InlineKeyboardButton(text="🔜", callback_data=UserChatPaginationCallbackData(action='select_edit_chat', data=callback_data, id=0, page=(page + 1)).pack())
        ])
    elif page > 1 and total_pages == page:
         buttons.append( [
            types.InlineKeyboardButton(text="🔙", callback_data=UserChatPaginationCallbackData(action='select_edit_chat', data=callback_data, id=0, page=(page - 1)).pack()),
        ])
    buttons.append([types.InlineKeyboardButton(text="Назад", callback_data=UserChatCallbackData(action='edit_chat_select_action', data=callback_data, id=0).pack())])
    return types.InlineKeyboardMarkup(inline_keyboard=buttons)


    return markup

def create_chat_name(chat, callback_data):
    if ChatRole[callback_data] == ChatRole.writer:
        return "{chat.name}|{chat.commission}%|{chat.notify_limit}|{chat.comment}".format(chat=chat)
    else:
        return "{chat.name}|{chat.commission}%|{chat.comment}".format(chat=chat)