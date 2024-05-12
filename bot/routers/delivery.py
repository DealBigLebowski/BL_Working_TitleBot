from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram import F, types
from aiogram.filters.command import CommandStart
from aiogram.fsm.context import FSMContext
from ..filters.registered import SupportFilter


from .. import markups
from ..bot import bot
from ..state import Action
from ..utils.router import Router
from . import root_handlers_router

from ..callback_data import AnswerCallbackData, UserChatCallbackData, DeliveryCallbackData
from ..services.database.models import BotUser, UserChat, Delivery
from ..enums import ChatRole

router = Router()
root_handlers_router.include_router(router)

@router.message(F.chat.type != "private", F.text.find("/add") == 0, SupportFilter(support=True))
async def create_delivery_handler(message: types.Message, state: FSMContext, bot_user: BotUser):
    user_chat = await UserChat.filter(id=message.chat.id).prefetch_related("bot_user").first()
    if user_chat.type == ChatRole.rek:    
        delivery = await Delivery.filter(bot_user=bot_user).all()
        await message.answer(
            text="Выберите пустой слот для добавление, или выберите реквизит для редактирования:",
            reply_markup= await create_add_delivery_markup(delivery, bot_user)
        )

@router.callback_query(DeliveryCallbackData.filter(F.action == 'add_delivery'))
async def other_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    await state.set_data({"message_id": callback.message.message_id})
    await state.set_state(Action.wait_add_rek_fio)
    await bot.send_message(
        text="Введите фио дропа в формате: фамилия имя отчество",
        chat_id=callback.message.chat.id,
        reply_markup=markups.cancel_rek_markup
    )

@router.message(Action.wait_add_rek_fio, F.text)
async def wait_add_rek_fio_handler(message: types.Message, state: FSMContext, bot_user: BotUser):
    current_data = await state.get_data()
    await state.set_state(Action.wait_add_rek_bank)
    await state.set_data({
        "message_id": current_data['message_id'],
        "fio": message.text
        })
    await bot.send_message(
        text="Введите название банка и виды пополнения:",
        chat_id=message.chat.id,
        reply_markup=markups.cancel_rek_markup
        )

@router.message(Action.wait_add_rek_bank)
async def wait_add_rek_bank_handler(message: types.Message, state: FSMContext, bot_user: BotUser):
    current_data = await state.get_data()
    if message.text:
        await state.set_state(Action.wait_add_rek_limit)
        await state.set_data({
            "message_id": current_data['message_id'],
            "fio": current_data['fio'],
            'bank': message.text
            })
        await bot.send_message(
            text="Введите максимальный лимит",
            chat_id=message.chat.id,
            reply_markup=markups.cancel_rek_markup
        )

@router.message(Action.wait_add_rek_limit)
async def wait_add_rek_fio_handler(message: types.Message, state: FSMContext, bot_user: BotUser):
    current_data = await state.get_data()
    if message.text:
        await state.set_state(Action.wait_add_rek_other_information)
        upper_data = message.text.upper()
        if upper_data.find("КК") != -1:
            limit = int(float(upper_data.replace("КК", "")) * 1000000)
        else:
            limit = message.text.replace(".", "")
        if not str(limit).isnumeric():
            return await message.answer("Введите число!", reply_markup=markups.cancel_rek_markup)
        await state.set_data({
            "message_id": current_data['message_id'],
            "fio": current_data['fio'],
            "bank": current_data['bank'],
            "limit": limit
            })
        await bot.send_message(
            text="Введите полный реквизиты в формате:\n\nФИО\nСчёт получателя платежа ХХХХХХХХХХХХХХХХХХХХ\nНазначение платежа Перевод средств по договору № ХХХХХХХХХХ\nБИК ХХХХХХХХХ\nБанк получатель ХХХХХХХХХХХ\nКорр. счёт ХХХХХХХХХХХХХХХХХХХХ\nИНН  ХХХХХХХХХХ\nКПП ХХХХХХХХХ\n\nНомер карты: ХХХХ ХХХХ ХХХХ ХХХХ\nСрок карты: ХХ/ХХ               CVV: ХХХ\nТелефон СБП ХХХХХХХХХХХ\n\nДата рождения: ДД.ММ.ГГГГ\nПрописка: Город/область; Улица и номер дома; Квартира.",
            chat_id=message.chat.id,
            reply_markup=markups.cancel_rek_markup
        )

@router.message(Action.wait_add_rek_other_information)
async def wait_add_rek_fio_handler(message: types.Message, state: FSMContext, bot_user: BotUser):
    current_data = await state.get_data()
    if message.text:
        await state.clear()
        await Delivery.create(
            bot_user=bot_user,
            fio=current_data['fio'],
            bank_name=current_data['bank'],
            limit=current_data['limit'],
            other_information=message.text
        )
        await bot.send_message(
            text="✅ Данные успешно добавлены",
            chat_id=message.chat.id,
        )

async def create_add_delivery_markup(delivery, bot_user):
    markup = (
        InlineKeyboardBuilder()
        .add(*(types.InlineKeyboardButton(
            text="{deliv.bank_name} - {deliv.limit}".format(deliv=deliv),
            callback_data=DeliveryCallbackData(action='edit_delivery', id=deliv.id).pack(),
        ) for deliv in delivery))
        .add(*(types.InlineKeyboardButton(
            text="[             ]",
            callback_data=DeliveryCallbackData(action='add_delivery', id=bot_user.id).pack(),
        ) for deliv in range(10 - len(delivery))))
        .adjust(2, repeat=True)
        .as_markup()
    )
    return markup