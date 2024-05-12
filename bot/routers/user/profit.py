import uuid

from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram import F, types
from aiogram.filters.command import CommandStart
from aiogram.fsm.context import FSMContext
from ...filters.registered import SupportFilter
from tortoise.functions import Count, Sum 
from tortoise import expressions
from datetime import datetime
from pytz import timezone

from ... import markups
from ...bot import bot
from ...state import Action
from . import router
from ...callback_data import AnswerCallbackData, UserChatCallbackData
from ...services.database.models import BotUser, UserChat, ProfitUserChat, ProfitUser, Order
from ...enums import ChatRole, OrderStatus

router.message.filter(F.chat.type == "private")


acd = AnswerCallbackData(action='demo')



@router.callback_query(AnswerCallbackData.filter(F.action == 'profit'))
async def profit_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    await bot.edit_message_text(
        text="<b>Резак капусты</b>\n\nВыберите действия:",
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=markups.profit_markup
    )

@router.callback_query(AnswerCallbackData.filter(F.action == 'profit_collect'))
async def profit_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    user_profit = await ProfitUser.filter(bot_user=bot_user).first()
    if user_profit is None:
        user_profit = await ProfitUser.create(
            bot_user=bot_user,
            uuid=str(uuid.uuid4())[:8]
        )
    start_date = user_profit.last_action
    end_date = datetime.now(timezone(bot.config.timezone))
    text = await get_stats_text(bot_user, start_date, end_date, olny_one=False)
    await bot.edit_message_text(
        text=text,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=await markups.create_back_markup(AnswerCallbackData(action='profit').pack())
    )
    user_profit.last_action = end_date
    await user_profit.save()

@router.callback_query(AnswerCallbackData.filter(F.action == 'profit_add_commission'))
async def instruction_profit_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    profit_user_chat = await ProfitUserChat.filter(user_chat__bot_user_id=bot_user.id).prefetch_related("bot_user", "user_chat").all()
    await bot.edit_message_text(
        text="<b>Установить комиссию</b>\n\nВыберите чат:",
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=await create_profit_user_chat_list(profit_user_chat, "data")
    )


@router.callback_query(AnswerCallbackData.filter(F.action == 'profit_instruction'))
async def instruction_profit_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    await callback.answer("❕ Привяжите все ваши КЦ к данному ЛК для получения подробная информация о доходах ваших КЦ/Лейки и получения подсчета вашей доли с реферальной программы, всё это собрано и доступно прямо здесь", True)

@router.callback_query(AnswerCallbackData.filter(F.action == 'profit_stats'))
async def instruction_profit_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    await callback.answer("❕ В разработке", True)


@router.callback_query(AnswerCallbackData.filter(F.action == 'profit_add_chat'))
async def profit_add_chat_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    user_profit = await ProfitUser.filter(bot_user=bot_user).first()
    if user_profit is None:
        user_profit = await ProfitUser.create(
            bot_user=bot_user,
            uuid=str(uuid.uuid4())[:8]
        )
    text = "Ваша реферальная команда для добавления группы: <code>/set_profit {user_profit.uuid}</code>\n\n❕ Обратите внимание, код нужно ввести в ту группу (КЦ/Лейки) которую хотите добавить".format(user_profit=user_profit)
    back_markup = ( InlineKeyboardBuilder().button(text="Назад", callback_data=AnswerCallbackData(action='profit').pack()).as_markup())
    await bot.edit_message_text(
        text=text,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=back_markup
    )

@router.callback_query(UserChatCallbackData.filter(F.action == 'profit_add_commission'))
async def edit_chat_select_action_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    await state.set_data({"profit_user_chat_id": callback_data.id})
    await state.set_state(Action.wait_user_profite_commission)
    await bot.edit_message_text(
        text="Отправьте комиссию вознограждения:",
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=markups.cancel_markup
    )

@router.message(Action.wait_user_profite_commission, F.text)
async def wait_support_username_handler(message: types.Message, state: FSMContext, bot_user: BotUser):
    if not message.text.replace('.','',1).isdigit():
        return await message.answer("Введите число")
    amount = float(message.text)
    if amount > 0 and amount <= 100:
        current_data = await state.get_data()
        profit_user_chat = await ProfitUserChat.filter(id=current_data["profit_user_chat_id"]).prefetch_related("bot_user", "user_chat").first()
        profit_user_chat.commission = message.text
        await profit_user_chat.save()
        text="✅ Комиссия вознограждения для чата <b>{chat_name}</b> -> @{username} успешно изменена на {amount}%".format(amount=message.text, chat_name=profit_user_chat.user_chat.name,username=profit_user_chat.bot_user.username)
        await message.answer(text,reply_markup=markups.back_markup)

async def get_stats_text(bot_user, start_date, end_date, olny_one=True):
    count = 0
    # paid_and_confirm_orders_amount = 0
    # cancel_orders_amount = 0
    # pending_orders_amount = 0
    # all_orders_amount = 0
    if start_date:
        if not olny_one:
            date_text = "{start_date} - {end_date}".format(start_date=start_date.strftime("%Y-%m-%d"), end_date=end_date.strftime("%Y-%m-%d"))
        else:
            date_text = "{start_date}".format(start_date=start_date.strftime("%Y-%m-%d"))
        user_chats = await ProfitUserChat.filter(bot_user=bot_user).prefetch_related("bot_user", "user_chat").all()
        total_count = 0
        total_paid_and_confirm_orders_amount = 0
        total_proft_orders_amount = 0
        total_pending_orders_amount = 0
        total_all_orders_amount = 0
        for profit_user_chat in user_chats:
            user_chat = profit_user_chat.user_chat
            count = await Order.filter(
                user_chat=user_chat,
                created_date__gte=start_date,
                created_date__lte=end_date
            ).all().annotate(total=Count("amount")).first().values("total")
            paid_and_confirm_orders_amount = await Order.filter(
                user_chat=user_chat,
                created_date__gte=start_date,
                created_date__lte=end_date,
                status__in=[OrderStatus.confirm, OrderStatus.paid],
            ).all().annotate(total=Sum("amount")).first().values("total")
            proft_orders_amount = await Order.filter(
                user_chat=user_chat,
                created_date__gte=start_date,
                created_date__lte=end_date,
                status=OrderStatus.paid,
            ).all().annotate(total=Sum(((expressions.F("profit_amount") - expressions.F("other_profit_amount")) / expressions.F("rates")))).first().values("total")
            pending_orders_amount = await Order.filter(
                user_chat=user_chat,
                created_date__gte=start_date,
                created_date__lte=end_date,
                status=OrderStatus.pending,
            ).all().annotate(total=Sum("amount")).first().values("total")
            all_orders_amount = await Order.filter(
                user_chat=user_chat,
                created_date__gte=start_date,
                created_date__lte=end_date,
            ).all().annotate(total=Sum("amount")).first().values("total")
            total_count += none_to_zero(count['total'])
            total_paid_and_confirm_orders_amount += none_to_zero(paid_and_confirm_orders_amount['total'])
            total_proft_orders_amount += int((abs(none_to_zero(proft_orders_amount['total'])) / 100) * profit_user_chat.commission)
            total_pending_orders_amount += none_to_zero(pending_orders_amount['total'])
            total_all_orders_amount += none_to_zero(all_orders_amount['total'])

    text = "По дате: {date_text}\n\nНайдено {total_count} платежей\n\n".format(date_text=date_text, total_count=amount_fm(total_count))
    if total_count:
        return (
            "{text}В ожидании: <b>{pending}₽</b>\nВыплачено: <b>{paid_and_confirm}₽</b>\nОбщая сумма: <b>{total}₽</b>\n\nТотал: <b>{profit}$</b>"
                .format(
                text=text,
                pending=amount_fm(total_pending_orders_amount),
                paid_and_confirm=amount_fm(total_paid_and_confirm_orders_amount),
                total=amount_fm(total_all_orders_amount),
                profit=amount_fm(total_proft_orders_amount)
            )
        )
    return text

def amount_fm(amount):
    return "{:,}".format(0 if amount is None else amount)

def none_to_zero(amount):
    return 0 if amount is None else int(amount)

async def create_profit_user_chat_list(chats, callback_data):
    markup = (
        InlineKeyboardBuilder()
        .add(*(types.InlineKeyboardButton(
            text="{chat.user_chat.name} -> @{chat.bot_user.username}".format(chat=chat),
            callback_data=UserChatCallbackData(action='profit_add_commission', data=callback_data, id=chat.id).pack(),
        ) for chat in chats))
        .button(text="Назад", callback_data=AnswerCallbackData(action='profit').pack())
        .adjust(1, repeat=True)
        .as_markup()
    )
    return markup