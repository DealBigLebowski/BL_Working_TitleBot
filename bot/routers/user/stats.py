from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder, InlineKeyboardButton
from aiogram import F, types
from aiogram.filters.command import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.filters.callback_data import CallbackData
from tortoise.functions import Count, Sum 
from tortoise import expressions


from datetime import datetime
from pytz import timezone


from ... import markups
from ...bot import bot
from ...state import Action
from . import router
from ...callback_data import AnswerCallbackData, UserChatCallbackData, SupportUserChatCallbackData
from ...services.database.models import BotUser, UserChat, UserChatAdvertising, Order, SupportUserChat
from ...enums import ChatRole, OrderStatus, UserRole
from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback, DialogCalendar, DialogCalendarCallback, \
    get_user_locale
from aiogram_calendar.schemas import SimpleCalAct

router.message.filter(F.chat.type == "private")


acd = AnswerCallbackData(action='demo')

@router.callback_query(AnswerCallbackData.filter(F.action == 'stats'))
async def stats_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    await bot.edit_message_text(
        text="<b>Статистика</b>\n\nВыберите действия:",
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        reply_markup=markups.stats_markup
    )

@router.callback_query(AnswerCallbackData.filter(F.action == 'get_stats'))
async def get_stats_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    await callback.message.edit_text(
        "Выберите тип группы:",
        reply_markup=markups.stats_select_chat_type
    )

@router.callback_query(UserChatCallbackData.filter(F.action == 'stats_select_chat_type'))
async def get_stats_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    await state.clear()
    chat_type = [ChatRole.cc, ChatRole.writer] if callback_data.data == 'all' else [ChatRole[callback_data.data]]
    await state.update_data({"chat_type": chat_type})

    current_data = await state.get_data()
    start_date = datetime.now(timezone(bot.config.timezone))
    start_date = start_date.replace(hour=0, minute=0, second=0)
    
    end_date = datetime.now(timezone(bot.config.timezone))
    end_date = end_date.replace(hour=23, minute=59, second=59)
    
    await callback.message.edit_text(
        text=await get_stats_text(bot_user, start_date, end_date, chat_roles=current_data['chat_type']), 
        reply_markup=markups.filter_stats_markup
        )

@router.callback_query(AnswerCallbackData.filter(F.action == 'get_stats_today'))
async def get_stats_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
   current_data = await state.get_data()
   start_date = datetime.now(timezone(bot.config.timezone))
   start_date = start_date.replace(hour=0, minute=0, second=0)
   
   end_date = datetime.now(timezone(bot.config.timezone))
   end_date = end_date.replace(hour=23, minute=59, second=59)
   
   await callback.message.edit_text(
       text=await get_stats_text(bot_user, start_date, end_date, chat_roles=current_data['chat_type']), 
       reply_markup= await markups.create_back_markup(AnswerCallbackData(action="get_stats").pack())
       )

@router.callback_query(AnswerCallbackData.filter(F.action == 'get_stats_support'))
async def get_stats_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
#    current_data = await state.get_data()
#    start_date = datetime.now(timezone(bot.config.timezone))
#    start_date = start_date.replace(hour=0, minute=0, second=0)
   
#    end_date = datetime.now(timezone(bot.config.timezone))
#    end_date = end_date.replace(hour=23, minute=59, second=59) SupportUserChatCallbackData
    support_user_chat = await SupportUserChat.filter(bot_user=bot_user, other_bot_user_id__not=bot_user.id).prefetch_related("other_bot_user").all()
   
    await callback.message.edit_text(
       text="Выберите действия:",
       reply_markup=await create_support_user_markup(support_user_chat)
       )

@router.callback_query(SupportUserChatCallbackData.filter(F.action == 'get_stats_select_support'))
async def get_stats_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    current_data = await state.get_data()
    other_bot_user = await BotUser.filter(id=callback_data.other_user).first()
    current_data['support_id'] = callback_data.other_user
    await state.update_data(current_data)
    user_chat_filter_stats_markup = (
        InlineKeyboardBuilder()
        .button(text="Выбранной дате", callback_data=AnswerCallbackData(action='get_stats_select_day').pack())
        .button(text="Выбранному промежутку дат", callback_data=AnswerCallbackData(action='get_stats_select_betwen').pack())
        .button(text="Назад", callback_data=AnswerCallbackData(action='get_stats_support').pack())
        .adjust(1, repeat=True)
        .as_markup()
    )
    await callback.message.edit_text(text="Выберите действиея для пользователя {bot_user.first_name} (@{bot_user.username})".format(bot_user=other_bot_user), reply_markup=user_chat_filter_stats_markup)

@router.callback_query(AnswerCallbackData.filter(F.action == 'get_stats_select_day'))
async def get_stats_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    current_data = await state.get_data()
    current_data['get_stats_select_day'] = True
    await state.update_data(current_data)
    await callback.message.edit_text(
        "Выберите нужную дату:",
        reply_markup=await SimpleCalendar(
            today_btn="Сегодня",
            cancel_btn="Меню",
            locale=await get_user_locale(callback.from_user)
        ).start_calendar()
    )

@router.callback_query(AnswerCallbackData.filter(F.action == 'get_stats_select_betwen'))
async def get_stats_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    current_data = await state.get_data()
    current_data['get_stats_select_betwen'] = True
    await state.update_data(current_data)
    await callback.message.edit_text(
        "Выберите начальную дату:",
        reply_markup=await SimpleCalendar(
            today_btn="Сегодня",
            cancel_btn="Меню",
            locale=await get_user_locale(callback.from_user)
        ).start_calendar()
    )


@router.callback_query(SimpleCalendarCallback.filter())
async def process_dialog_calendar(callback: CallbackQuery, callback_data: CallbackData, state: FSMContext, bot_user: BotUser):
    if callback.message.chat.type != 'private':
        user_chat = await UserChat.filter(id=callback.message.chat.id).first()
        markup = None
    else:
        user_chat = None
        markup = await markups.create_back_markup(AnswerCallbackData(action="get_stats").pack())
    calendar = SimpleCalendar(
        today_btn="Сегодня",
        cancel_btn="Меню",
        locale=await get_user_locale(callback.from_user), show_alerts=True
    )
    calendar.set_dates_range(datetime(2023, 1, 1), datetime(2025, 12, 31))
    
    if callback_data.act == SimpleCalAct.cancel:
        return await stats_handler(callback, callback_data, state, bot_user)
    selected, date = await calendar.process_selection(callback, callback_data)

    if selected:
        current_data = await state.get_data()
        is_support = False
        if 'support_id' in current_data:
            bot_user = await BotUser.filter(id=current_data['support_id']).first()
            bot_user.role = UserRole.manager
            is_support = True
        if user_chat:
            current_data['chat_type'] = [user_chat.type]
        if 'get_stats_select_day' in current_data:
            start_date = date.replace(hour=0, minute=0, second=0)
            end_date = date.replace(hour=23, minute=59, second=59)
            await callback.message.edit_text(
                    text=await get_stats_text(bot_user, start_date, end_date, current_user_chat=user_chat, chat_roles=current_data['chat_type'], is_support=is_support), 
                    reply_markup= markup
                )
            await state.clear()
        elif 'get_stats_select_betwen' in current_data:
            if 'start_date' in current_data:
                start_date = current_data['start_date'].replace(hour=0, minute=0, second=0)
                end_date = date.replace(hour=23, minute=59, second=59)
                stats_text = await get_stats_text(bot_user, start_date, end_date, olny_one=False, current_user_chat=user_chat, chat_roles=current_data['chat_type'], is_support=is_support)
                if len(stats_text) > 4096:
                    await callback.message.edit_text(
                        text=stats_text[:4096],
                        reply_markup=markup
                    )
                    start_index = 4096
                    end_index = start_index * 2
                    for i in range(int(len(stats_text) / start_index)):
                        await callback.message.answer(
                            text=stats_text[start_index:end_index],
                            reply_markup=markup
                        )
                        start_index = end_index
                        end_index = start_index * 2
                else:
                    await callback.message.edit_text(
                        text=stats_text, 
                        reply_markup= markup
                    )
                await state.clear()
            else:
                current_data['get_stats_select_betwen'] = True
                current_data['start_date'] = date
                await state.update_data(current_data)
                await callback.message.edit_text(
                    "Начальная дата: {start_date}\nКонечная дата: -\n\nВыберите конечную дату:".format(start_date=date.strftime("%Y-%m-%d")),
                    reply_markup=await SimpleCalendar(
                        today_btn="Сегодня",
                        cancel_btn="Меню",
                        locale=await get_user_locale(callback.from_user)
                    ).start_calendar()
                )
        

@router.callback_query(AnswerCallbackData.filter(F.action == 'stats_instruciton'))
async def stats_instruciton_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    await callback.answer("❕ Данная функция позволяет вам разместить получить подробную статистику по чатам", True)


async def get_stats_text(bot_user, start_date, end_date, olny_one=True, current_user_chat=None, chat_roles=[ChatRole.cc, ChatRole.writer], is_support=False):
    is_only_cc = True if len(chat_roles) == 1 and chat_roles[0] == ChatRole.cc else False
    body_text = ""
    # paid_and_confirm_orders_amount = 0
    # cancel_orders_amount = 0
    # pending_orders_amount = 0
    # all_orders_amount = 0
    user_chat_text = ""
    total_count = 0
    total_paid_orders_amount = 0
    total_confirm_orders_amount = 0
    total_profit = 0
    total_pending_orders_amount = 0
    total_all_orders_amount = 0
    other_total = 0
    other_total_usd = 0
    support_profit_list = dict()
    if start_date:

        if not olny_one:
            date_text = "{start_date} - {end_date}".format(start_date=start_date.strftime("%Y-%m-%d"), end_date=end_date.strftime("%Y-%m-%d"))
        else:
            date_text = "{start_date}".format(start_date=start_date.strftime("%Y-%m-%d"))
        
        if bot_user.role == UserRole.manager and current_user_chat is None:
            orders = await Order.filter(
                expressions.Q(expressions.Q(bot_user=bot_user), expressions.Q(other_bot_user=bot_user), join_type="OR"), 
                created_date__gte=start_date,
                created_date__lte=end_date
            ).prefetch_related("other_bot_user").prefetch_related("user_chat").all()
            total_count += len(orders)
            for order in orders:
                profit = 0
                if order.status == OrderStatus.paid:
                    if order.other_profit_amount != 0 and order.profit_amount != 0:
                        profit = int(round(abs(order.other_profit_amount - order.profit_amount), 0)) 
                        total_profit += profit
                    total_paid_orders_amount += order.amount
                elif order.status == OrderStatus.confirm:
                    total_confirm_orders_amount += order.amount
                elif order.status == OrderStatus.pending:
                    total_pending_orders_amount += order.amount
                
                if order.user_chat.name in support_profit_list:
                    support_profit_list[order.user_chat.name]["amount"] += order.amount
                    support_profit_list[order.user_chat.name]['profit'] += profit
                else:
                    support_profit_list[order.user_chat.name] = {"amount": order.amount, "profit": profit}
                total_all_orders_amount += order.amount
        else:
            if current_user_chat is None:
                user_chats = await UserChat.filter(bot_user=bot_user, type__in=chat_roles).all()
            else:
                user_chats = []
                user_chats.append(current_user_chat)
            checked_orders = []
            for user_chat in user_chats:
                if current_user_chat:
                    orders = await Order.filter(
                        expressions.Q(expressions.Q(user_chat=user_chat), expressions.Q(other_user_chat=user_chat), join_type="OR"), 
                        created_date__gte=start_date,
                        created_date__lte=end_date
                    ).all()
                    total_count = len(orders)
                    bank_data = dict()
                    for order in orders:
                        if not order.bank in bank_data:
                            bank_data[order.bank] =  {"confirm": 0, "paid": 0, "pending": 0, "cancel": 0, "profit": 0}
                        if order.status == OrderStatus.confirm:
                            bank_data[order.bank]["confirm"] += order.amount
                        elif order.status == OrderStatus.pending:
                            bank_data[order.bank]["pending"] += order.amount
                        elif order.status == OrderStatus.paid:
                            bank_data[order.bank]["paid"] += order.amount
                            amount = order.profit_amount
                            if user_chat.type == ChatRole.writer:
                                amount = order.other_profit_amount
                            bank_data[order.bank]["profit"] += amount
                            other_total += order.amount
                            other_total_usd += amount
                        else:
                            bank_data[order.bank]["cancel"] += order.amount
                    
                    for bank in bank_data:
                        body_text += "<b>{bank}</b>\n├✅{paid}руб ({profit}$)\n".format(bank=bank, paid=amount_fm(int(bank_data[bank]['paid'])), profit=amount_fm(int(bank_data[bank]['profit'])))
                        body_text += "├☑️{confirm}руб\n".format(confirm=amount_fm(int(bank_data[bank]['confirm'])))
                        body_text += "├⌛️{pending}руб\n".format(pending=amount_fm(int(bank_data[bank]['pending'])))
                        body_text += "└🎯{cancel}руб\n".format(cancel=amount_fm(int(bank_data[bank]['cancel'])))
                        if len(body_text) > 3500:
                            text = "По выбранной дате: {date_text}\n\nНайдено {total_count} платежей\n\n{body_text}".format(date_text=date_text, total_count=len(orders), body_text=body_text)
                            await bot.send_message(user_chat.id, text)
                            body_text = ""
                    break
                orders = await Order.filter(
                    expressions.Q(expressions.Q(user_chat=user_chat), expressions.Q(other_user_chat=user_chat), join_type="OR"), 
                    created_date__gte=start_date,
                    created_date__lte=end_date
                ).prefetch_related("other_bot_user", "user_chat")
                total_count += len(orders)
                total_orders_user_chat = 0
                total_profit_user_chat = 0
                for order in orders:
                    if order.id in checked_orders:
                        continue
                    checked_orders.append(order.id)
                    if is_only_cc:
                        total_orders_user_chat += order.amount
                    if order.status == OrderStatus.paid:
                        if order.other_profit_amount != 0 and order.profit_amount != 0:
                            if is_only_cc:
                                total_profit_user_chat += int(round(abs(order.other_profit_amount - order.profit_amount), 0))
                            # if order.other_bot_user.role == UserRole.manager:
                            profit = int(round(abs(order.other_profit_amount - order.profit_amount), 0))
                            if order.other_bot_user.username is None:
                                order.other_bot_user.username = 'None'
                            if order.user_chat.name in support_profit_list:
                                support_profit_list[order.user_chat.name]["amount"] += order.amount
                                support_profit_list[order.user_chat.name]['profit'] += profit
                            else:
                                support_profit_list[order.user_chat.name] = {"amount": order.amount, "profit": profit}
                            total_profit += profit
                        total_paid_orders_amount += order.amount
                    elif order.status == OrderStatus.confirm:
                        total_confirm_orders_amount += order.amount
                    elif order.status == OrderStatus.pending:
                        total_pending_orders_amount += order.amount
                    total_all_orders_amount += order.amount

    if is_only_cc and current_user_chat is None:
        for i in support_profit_list:
            user_chat_text += "\n{name}\nОборот: {total_amount}₽\nПрофит: {total_profit}$\n".format(name=i, total_amount=amount_fm(support_profit_list[i]['amount']), total_profit=amount_fm(int(round(support_profit_list[i]['profit'], 0))))
    text = "По выбранной дате: {date_text}\n\n{user_chat_text}Найдено {total_count} платежей\n\n{body_text}".format(date_text=date_text, total_count=amount_fm(total_count), body_text=body_text, user_chat_text=user_chat_text)
    
    if total_count:
        if current_user_chat is None:
            return "{text}В ожидании: {pending}₽\nПодтверждено: {confirm}₽\nВыплачено: {paid}₽\nОбщая сумма: {total}₽\nВаш профит: {profit}$".format(
                text=text,
                pending=amount_fm(total_pending_orders_amount),
                paid=amount_fm(total_paid_orders_amount),
                confirm=amount_fm(total_confirm_orders_amount),
                profit=amount_fm(int(round(abs(total_profit), 0))), 
                total=amount_fm(total_all_orders_amount)
            )
        return "{text}\nОбщая сумма: <b>{total}₽ ({total_usd}$)</b>".format(
            text=text,
            total=amount_fm(other_total),
            total_usd=amount_fm(int(other_total_usd)),
        )
    return text

def amount_fm(amount):
    return "{:,}".format(0 if amount is None else amount)

def none_to_zero(amount):
    return 0 if amount is None else int(amount)


async def create_support_user_markup(support_user_chat):
    markup = (
        InlineKeyboardBuilder()
        .add(*(types.InlineKeyboardButton(
            text="{user.username}".format(user=user.other_bot_user),
            callback_data=SupportUserChatCallbackData(action='get_stats_select_support', id=user.id, other_user=user.other_bot_user.id).pack(),
        ) for user in support_user_chat))
        .button(text="Назад", callback_data=AnswerCallbackData(action='get_stats').pack())
        .adjust(1, repeat=True)
        .as_markup()
    )
    return markup