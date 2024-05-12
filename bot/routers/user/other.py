from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram import F, types
from aiogram.filters.command import CommandStart
from aiogram.fsm.context import FSMContext


from ... import markups
from ...bot import bot
from ...state import Action
from . import router
from ...callback_data import AnswerCallbackData, UserPeopleCallbackData
from ...services.database.models import BotUser, UserChat, UserChatAdvertising, UserPeople
from ...enums import ChatRole

router.message.filter(F.chat.type == "private")


acd = AnswerCallbackData(action='demo')

@router.callback_query(AnswerCallbackData.filter(F.action == 'other'))
async def other_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    await bot.edit_message_text(
        text="<b>Крайняк</b>\n\nВыберите действия:",
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=markups.other_markup
    )

@router.callback_query(AnswerCallbackData.filter(F.action == 'other_send_request'))
async def other_send_request_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    await state.clear()
    text="Введите подробный запрос.\n\nПример: Нужен реквизит МТС для пополнения через салон связи МТС на 500к."
    await state.set_state(Action.wait_other_send_request)
    await state.set_data({"message_id": callback.message.message_id})
    await bot.edit_message_text(
            text=text,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            reply_markup=markups.cancel_markup
        )


@router.message(Action.wait_other_send_request)
async def wait_other_send_request_handler(message: types.Message, state: FSMContext, bot_user: BotUser):
    state_date = await state.get_data()
    
    user_people = await UserPeople.filter(bot_user=bot_user).prefetch_related("other_bot_user").all()
    if message.text:
        for user in user_people:
            await bot.send_message(user.other_bot_user.id,text=message.text)
        await message.answer("✅ Ваш запрос успешно отправлен")
    else:
        return await message.answer("Ошибка, введите текст для запроса", reply_markup=markups.cancel_markup)
            
    await state.clear()
    text = "Добро пожаловать <b>" + message.from_user.first_name + "</b>!\n\nВыберите действия 👇" 
    await message.answer( text, reply_markup=markups.main_menu_markup )   

    await bot.delete_message(
        bot_user.id,
        state_date["message_id"]
    )

@router.callback_query(AnswerCallbackData.filter(F.action == 'other_people'))
async def notification_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    user_people = await UserPeople.filter(bot_user=bot_user).prefetch_related("other_bot_user").all()
    await bot.edit_message_text(
        text="Выберите действия:",
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=await create_user_people_markup(user_people)
    )

@router.callback_query(AnswerCallbackData.filter(F.action == 'other_instruciton'))
async def other_instruciton_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    back_markup = (
        InlineKeyboardBuilder()
        .button(text="Назад", callback_data=AnswerCallbackData(action='other').pack())
        .adjust(1, repeat=True)
        .as_markup()
    )
    text = "Данная функция поможет вам по нажатию одной кнопки отправить срочный запрос всем вашим доверенным командам нальщиков из заранее заданного списка. Не забудьте перед внесением пользователя в список подтвердиться с ним на форуме об условиях данной функции."
    await bot.edit_message_text(
            text=text,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            reply_markup=back_markup
        )

@router.callback_query(AnswerCallbackData.filter(F.action == 'add_people'))
async def other_add_people_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    await state.clear()
    text="Введите логин доверенного пользователя."
    await state.set_state(Action.wait_user_people)
    await state.set_data({"message_id": callback.message.message_id})
    await bot.edit_message_text(
            text=text,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            reply_markup=markups.cancel_markup
        )

@router.callback_query(UserPeopleCallbackData.filter(F.action == 'edit_user_people'))
async def edit_user_people_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    other_user = await BotUser.filter(id=callback_data.other_id).first()
    text="ID: {other_user.id}\nИмя: {other_user.first_name}\nЛогин: @{other_user.username}\n\nВыберите действия для этого пользователя:".format(other_user=other_user)
    
    action_markup = (
        InlineKeyboardBuilder()
        .button(text="Удалить", callback_data=UserPeopleCallbackData(action='remove_user_people', id=callback_data.id, other_id=callback_data.other_id).pack())
        .button(text="Назад", callback_data=AnswerCallbackData(action='other_people').pack())
        .adjust(1, repeat=True)
        .as_markup()
    )

    await bot.edit_message_text(
            text=text,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            reply_markup=action_markup
        )

@router.callback_query(UserPeopleCallbackData.filter(F.action == 'remove_user_people'))
async def edit_user_people_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    user_people = await UserPeople.filter(id=callback_data.id).first()
    if user_people:
        await user_people.delete()

    action_markup = (
        InlineKeyboardBuilder()
        .button(text="Назад", callback_data=AnswerCallbackData(action='other_people').pack())
        .adjust(1, repeat=True)
        .as_markup()
    )

    await bot.edit_message_text(
            text="✅ Данные успешно удалены",
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            reply_markup=action_markup
        )

    
@router.message(Action.wait_user_people)
async def wait_user_people_handler(message: types.Message, state: FSMContext, bot_user: BotUser):
    state_date = await state.get_data()
    username = message.text.replace("@", "")
    other_user = await BotUser.filter(username=username).first()
    if other_user is None:
        return await message.answer("Ошибка, логин введен неправильно или пользователь не найден" , reply_markup=markups.cancel_markup)
    else:
        if other_user.id == bot_user.id:
            return await message.answer("Ошибка, Вы не можете добавить себя", reply_markup=markups.cancel_markup)
        user_people = await UserPeople.filter(bot_user=bot_user, other_bot_user=other_user).first()
        if user_people is None:
            user_people = await UserPeople.create(
                bot_user=bot_user,
                other_bot_user=other_user
            )
            await message.answer("✅ Данные успешно обновлены")
        else:
            return await message.answer("Ошибка, пользователь уже добавлен в список", reply_markup=markups.cancel_markup)   
            
    await state.clear()
    text = "Добро пожаловать <b>" + message.from_user.first_name + "</b>!\n\nВыберите действия 👇" 
    await message.answer( text, reply_markup=markups.main_menu_markup )   

    await bot.delete_message(
        bot_user.id,
        state_date["message_id"]
    )

async def create_user_people_markup(user_people):
    markup = (
        InlineKeyboardBuilder()
        .add(*(types.InlineKeyboardButton(
            text="{user.other_bot_user.id}|{user.other_bot_user.username}".format(user=user),
            callback_data=UserPeopleCallbackData(action='edit_user_people', id=user.id, other_id=user.other_bot_user.id).pack(),
        ) for user in user_people))
        .button(text="Добавить нового", callback_data=AnswerCallbackData(action='add_people').pack())
        .button(text="Назад", callback_data=AnswerCallbackData(action='other').pack())
        .adjust(1, repeat=True)
        .as_markup()
    )
    return markup