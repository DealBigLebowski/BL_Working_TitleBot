from aiogram import F, types
from aiogram.filters.command import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.filters import IS_NOT_MEMBER, IS_MEMBER, ChatMemberUpdatedFilter, IS_ADMIN, LEFT, KICKED
from aiogram.types import CallbackQuery, ReactionTypeEmoji, ReactionType, ReactionTypeCustomEmoji
from aiogram.enums.reaction_type_type import ReactionTypeType
from operator import attrgetter
from contextlib import suppress
from typing import Literal
import time
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union
from tortoise.functions import Upper
from tortoise.expressions import Q
from tortoise import expressions 

import math

from .. import markups
from ..bot import bot
from ..filters.registered import SupportFilter
from ..services.database.models import BotUser, UserChat, Order, ProfitUserChat, TimerMessage, ProfitUser, GameAction, UserChatAdvertising, OrderStatic, Delivery, OrderFine, SupportUserChat, TaskQueue
from ..enums import ChatRole, OrderStatus, GameStatus, TaskQueueType, ChatDepositNotify
from ..utils.router import Router
from . import root_handlers_router
from ..state import Action
from ..callback_data import AnswerCallbackData, DeliveryCallbackData, TimerActionCallbackData, UserChatCallbackData
from tortoise.functions import Sum, Max
from datetime import datetime, timedelta
from pytz import timezone

router = Router()
root_handlers_router.include_router(router)

@router.my_chat_member(ChatMemberUpdatedFilter(IS_ADMIN))
async def group_handler(chat_member: types.ChatMemberUpdated):
    bot_user = await BotUser.filter(id=chat_member.from_user.id).first()
    user_chat = await UserChat.filter(id=chat_member.chat.id, bot_user=bot_user).first()
    if user_chat is None:
        user_chat = await UserChat.create(
            id=chat_member.chat.id,
            bot_user=bot_user,
            name=chat_member.chat.title,
            type=ChatRole.none
        )

        markup = (
        InlineKeyboardBuilder()
        .button(text="КЦ/Лейки", callback_data=UserChatCallbackData(action='set_type', data='cc', id=user_chat.id).pack())
        .button(text="Нальщики", callback_data=UserChatCallbackData(action='set_type', data='writer', id=user_chat.id).pack())
        .button(text="Скрыть", callback_data=AnswerCallbackData(action='skip_text').pack())
        .adjust(1, repeat=True)
        .as_markup()
    )
        await bot.send_message(
            chat_id=chat_member.from_user.id,
            text="Группа <b>" + chat_member.chat.title + "</b> успешно добавлен в список.",
            reply_markup=markup
        )
    #if(me.id == update)


@router.my_chat_member((ChatMemberUpdatedFilter(LEFT) or ChatMemberUpdatedFilter(KICKED)))
async def group_left_handler(chat_member: types.ChatMemberUpdated):
    user_chat = await UserChat.filter(id=chat_member.chat.id).prefetch_related("bot_user").first()
    if user_chat:
        await user_chat.delete()
        text = "Группа <b>" + chat_member.chat.title + "</b> удалена из списка"
        await bot.send_message(
            chat_id=user_chat.bot_user.id,
            text=text,
            reply_markup=markups.skip_markup
        )

@router.callback_query(TimerActionCallbackData.filter(F.action == 'done'), SupportFilter(support=True))
async def set_rates_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    timer = await TimerMessage.filter(id=callback_data.timer_id).first()
    if timer:
        user_chat = await UserChat.filter(id=callback.message.chat.id).prefetch_related("bot_user").first()    
        if timer.steep == 2:
            text = "Победили КЦ , к сожалению мы не успели обработать запрос в течении 6-ти минут . Мы сделаем все ,что бы последующие запросы обрабатывались как можно быстрее . В качестве компенсации даруется скидка в след залив в 1% 🍀"
            await OrderFine.create(
                user_chat=user_chat,
                fine=1
            )
        elif timer.status == 0:
            text = "Мы выдали реквизит позже установленного регламента, поэтому Вы получаете скидку на данный залив 0.5% 🤘"
            await OrderFine.create(
                user_chat=user_chat,
                fine=0.5
            )
        else:
            text = "✅ Реквизиты были выданы вовремя"
            timer.status = 3
            await timer.save()
        await callback.message.delete()
        await bot.send_message(callback.message.chat.id, text)

@router.callback_query(TimerActionCallbackData.filter(F.action == 'add_minutes'), SupportFilter(support=True))
async def set_rates_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    timer = await TimerMessage.filter(id=callback_data.timer_id).first()
    if timer:
        timer.steep = 2
        timer.end_time = timer.end_time + 180
        await timer.save()

@router.callback_query(TimerActionCallbackData.filter(F.action == 'cancel'), SupportFilter(support=True))
async def set_rates_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    timer = await TimerMessage.filter(id=callback_data.timer_id).first()
    if timer:
        timer.status = -1
        await timer.save()
        await callback.message.delete()

        text = "К сожалению в данный момент мы не можем выполнить данный запрос. Мы сделаем все, для того чтобы Вы больше не увидели этот текст 🍀"
        await bot.send_message(callback.message.chat.id, text)



@router.callback_query(AnswerCallbackData.filter(F.action == 'set_rates'), SupportFilter(support=True))
async def set_rates_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    await callback.answer()
    await state.set_state(Action.wait_set_rates)  
    text="Введите курс:"
    await bot.send_message(chat_id=callback.message.chat.id, text=text, reply_markup=markups.cancel_set_rates_markup) 

@router.callback_query(AnswerCallbackData.filter(F.action == 'scrap_set_rates'), SupportFilter(support=True))
async def scrap_set_rates_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    await callback.answer()
    await state.set_state(Action.wait_scrap_set_rates)  
    text="Введите номера заявок:"
    await bot.send_message(chat_id=callback.message.chat.id, text=text, reply_markup=markups.cancel_set_rates_markup) 

@router.callback_query(AnswerCallbackData.filter(F.action == 'cancel_set_rates'), SupportFilter(support=True))
async def cancel_set_rates_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    await state.clear()
    await callback.answer("✅ Операция отменана, можете продолжить работу", True)
    await callback.message.delete()

@router.callback_query(AnswerCallbackData.filter(F.action == 'cancel_rek'), SupportFilter(support=True))
async def cancel_rek_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    await state.clear()
    await callback.answer("✅ Операция отменана", True)
    await callback.message.delete()

@router.callback_query(AnswerCallbackData.filter(F.action == 'start_job'))
async def select_chat_type_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    support_user = await SupportUserChat.filter(other_bot_user=bot_user, bot_user_id__not=expressions.F("other_bot_user_id")).prefetch_related("bot_user").all()
    await callback.message.edit_text(
        text="Выберите пользователя для которых будет запущен рабочий день в группах, или нажмите на кнопку <b>Выбрать свои чаты</b> чтобы начать работу в ваших группах 👇",
        reply_markup=await create_select_support_markup(support_user, bot_user)
    )


@router.callback_query(UserChatCallbackData.filter(F.action == 'select_start_support'))
async def select_chat_type_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    select_start_chat_type = (
        InlineKeyboardBuilder()
        .button(text="КЦ/Лейки", callback_data=UserChatCallbackData(action='select_start_chat_type', data='cc', id=callback_data.id).pack())
        .button(text="Нальщики", callback_data=UserChatCallbackData(action='select_start_chat_type', data='writer', id=callback_data.id).pack())
        .button(text="Назад", callback_data=AnswerCallbackData(action='main').pack())
        .adjust(1, repeat=True)
        .as_markup()
    )

    await callback.message.edit_text(
        text="Выберите тип гуррпы, для начало рабочего дня",
        reply_markup=select_start_chat_type
    )

@router.callback_query(UserChatCallbackData.filter(F.action == 'select_start_chat_type'))
async def select_start_type_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    select_start_type = (
        InlineKeyboardBuilder()
        .button(text="Ввести текст рекламы", callback_data=UserChatCallbackData(action='write_text_and_start_job', data=callback_data.data, id=callback_data.id).pack())
        .button(text="Без рекламы", callback_data=UserChatCallbackData(action='only_start_job', data=callback_data.data, id=callback_data.id).pack())
        .button(text="Назад", callback_data=AnswerCallbackData(action='start_job').pack())
        .adjust(1, repeat=True)
        .as_markup()
    )
    await callback.message.edit_text(
        text="Выберите метод запуска:",
        reply_markup=select_start_type
    )

@router.callback_query(UserChatCallbackData.filter(F.action == 'write_text_and_start_job'))
async def write_text_and_start_job(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    await state.clear()
    await state.set_state(Action.wait_start_advertising_text)
    await state.set_data({"message_id": callback.message.message_id, "user_chat_type": callback_data.data, "bot_user_id": callback_data.id})
    await callback.message.edit_text(
        text="Введите текст для рекламы:",
        reply_markup=markups.cancel_markup
    )


@router.callback_query(UserChatCallbackData.filter(F.action == 'only_start_job'))
async def write_text_and_start_job(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    other_bot_user = await BotUser.filter(id=callback_data.id).first()
    advertising = await UserChatAdvertising.filter(bot_user=other_bot_user, user_chat_type=ChatRole[callback_data.data]).first()
    if advertising:
        advertising.text = ""
        await advertising.save()
    await callback.message.delete()
    await start_job_handler(other_bot_user, ChatRole[callback_data.data], bot_user.id) 

@router.message(Action.wait_start_advertising_text, F.text != '/start')
async def advertising_text_handler(message: types.Message, state: FSMContext, bot_user: BotUser):
    state_date = await state.get_data()
    other_bot_user = await BotUser.filter(id=state_date['bot_user_id']).first()
    advertising = await UserChatAdvertising.filter(bot_user=other_bot_user, user_chat_type=ChatRole[state_date['user_chat_type']]).first()
    if advertising is None:
        await UserChatAdvertising.create(
            bot_user=other_bot_user,
            text=message.text,
            user_chat_type=ChatRole[state_date['user_chat_type']]
        )
    else:
        advertising.text = message.text
        await advertising.save()

    await bot.delete_message(
        bot_user.id,
        state_date["message_id"]
    )
    await state.clear()
    await start_job_handler(other_bot_user, ChatRole[state_date['user_chat_type']], bot_user.id) 

@router.callback_query(DeliveryCallbackData.filter(F.action == 'select_delivery'))
async def other_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    await state.set_data({"delevery_id": callback_data.id})
    await callback.message.delete()
    await state.set_state(Action.wait_select_rek_amount)
    await callback.message.answer("Введите суммму и способ пополнения, пример: Кешин 300.000", reply_markup=markups.cancel_rek_markup)

@router.message(Action.wait_select_rek_amount, F.text)
async def wait_add_rek_fio_handler(message: types.Message, state: FSMContext, bot_user: BotUser):
    split_data = message.text.split(" ")
    try:
        if len(split_data) == 2:            
            amount = filter_amount(split_data[1])

            current_data = await state.get_data()
            delivery = await Delivery.filter(id=current_data['delevery_id']).first()
            if delivery:
                deliv_orders = await Order.filter(delivery_id=delivery.id).all().annotate(total=Sum("amount")).first().values("total")
                other_amount = amount + number_or(deliv_orders['total'])
                if delivery.limit >= other_amount:
                    user_chat = await UserChat.filter(id=message.chat.id).prefetch_related("bot_user").first()
                    await create_order(user_chat, bot_user, "{bank} {amount}".format(bank=split_data[0], amount=amount), OrderStatus.pending, delivery.id)
                    await message.answer(delivery.other_information)
                    await message.answer("Реквизит выдан на сумму {amount} рублей, превышая данную сумму вы самотоятельно отказываетесь от гарантийных условий и берете все риски на себя".format(amount=amount))
                    await bot.edit_message_text(chat_id=user_chat.id, text=await get_stats(user_chat), message_id=user_chat.secured_id, reply_markup=markups.set_rates_markup)
                    await state.clear()
                else:
                    await message.answer("Запрашиваемая сумма превышает доступный лимит!\nВведите коректное число, либо выберите свободный реквизит", reply_markup=markups.cancel_rek_markup)
            else:
                await state.clear()
                await message.answer("Реквизит не найден!", reply_markup=markups.cancel_rek_markup)
           
        else:
            await message.answer("Введите суммму и способ пополнения, пример: Кешин 300.000", reply_markup=markups.cancel_rek_markup)
    except Exception as e:
        await message.answer("Введенные данные не верны\nВведите суммму и способ пополнения, пример: Кешин 300.000", reply_markup=markups.cancel_rek_markup)
        e.with_traceback()
        
async def start_job_handler(bot_user: BotUser, chat_type: ChatRole, user_chat_id: int):    
    user_chats = await UserChat.filter(bot_user=bot_user, type=chat_type).prefetch_related("bot_user").all()
    if len(user_chats) == 0:
        return await bot.send_message(chat_id=user_chat_id, text="❗️ Не найден подходяший тип группы", reply_markup=markups.back_markup)
    await bot.send_message(chat_id=user_chat_id, text="👨‍💻 Ваш запрос обрабатывается, пожалуйста подождите...")
    success_start = 0
    fail_start = 0
    for user_chat in user_chats:
        try:
            await start_day(user_chat)
            success_start = success_start + 1
        except Exception as e:
            if hasattr(e, "migrate_to_chat_id"):
                new_user_chat = await migrate_chat_id(user_chat, e.migrate_to_chat_id)
                try:
                    await start_day(new_user_chat)
                except Exception as e:
                    code = str(e).split(": ")[1].capitalize() if len(str(e).split(": ")) > 1 else "Внутренняя ошибка, пожалуйста, обратитесь в поддержку"
                    text = "Ошибка при работе с группой <b>{user_chat.name}</b>\n\nКод: {code}".format(user_chat=user_chat, code=code)
                    await bot.send_message(user_chat_id, text)
                    fail_start = fail_start + 1
            else:
                code = str(e).split(": ")[1].capitalize() if len(str(e).split(": ")) > 1 else "Внутренняя ошибка, пожалуйста, обратитесь в поддержку"
                text = "Ошибка при работе с группой <b>{user_chat.name}</b>\n\nКод: {code}".format(user_chat=user_chat, code=code)
                await bot.send_message(user_chat_id, text)
                fail_start = fail_start + 1
    
    text = "✅ Ваш запрос обработан\n\nУспешно завершенных групп - {success_start}\nГруппы с ошибками - {fail_start}".format(success_start=success_start, fail_start=fail_start)
    await bot.send_message(user_chat_id, text, reply_markup=markups.back_markup)    

async def start_day(user_chat): 
    order = await Order.filter(user_chat=user_chat, created_date__gte=user_chat.started_date, status=OrderStatus.confirm).first()
    if order:
        taks_queue = await TaskQueue.filter(user_chat=user_chat, type=TaskQueueType.start_day, status=1).first()
        if taks_queue is None:
            taks_queue = await TaskQueue.create(user_chat=user_chat, type=TaskQueueType.start_day, status=1)
        raise Exception("TaskQueue: Найдена активная заявка, группа поставлена в очередь")

    user_chat.started_date = datetime.now(timezone(bot.config.timezone))
    user_chat.step_rates = 0
    await user_chat.save()
    text = await get_stats(user_chat)
    ms = await bot.send_message(user_chat.id, text, reply_markup=markups.set_rates_markup, disable_notification=True)
    await bot.pin_chat_message(user_chat.id, ms.message_id, disable_notification=True)
    user_chat.secured_id = ms.message_id
    await user_chat.save()

async def migrate_chat_id(user_chat, migrate_to_chat_id): 
    new_user_chat = await UserChat.filter(id=migrate_to_chat_id).first()
    if new_user_chat is None:       
        new_user_chat = await UserChat.create(
            id=migrate_to_chat_id,
            bot_user=user_chat.bot_user,
            name = user_chat.name,
            comment = user_chat.comment,
            limit = user_chat.limit,
            notify_limit = user_chat.notify_limit,
            secured_id = user_chat.secured_id,
            rates = user_chat.rates,
            is_closed = user_chat.is_closed,
            started_date = user_chat.started_date,
            created_date = user_chat.created_date,
            type = user_chat.type,
        )

    orders = await Order.filter(user_chat=user_chat).all()
    for order in orders:
        order.user_chat = new_user_chat
        await order.save()
    
    await user_chat.delete()
    return new_user_chat

async def get_stats(user_chat, is_rates=False, scrap_orders=None, other_rates=False):
    
    if is_rates:
        if not other_rates:
            user_chat.step_rates = user_chat.step_rates + 1
        else:
            user_chat.step_rates = other_rates
        
        total_amount = 0
        total_payed = 0
        formula = "<b>🧑‍💻 Формула:</b><code>"
        fine_formula = ""
        if scrap_orders:
            orders = await Order.filter(
                id__in=scrap_orders
            ).prefetch_related("other_user_chat").prefetch_related("bot_user").order_by('support_name').all()
        else:
            orders = await Order.filter(
                Q(Q(user_chat=user_chat), Q(other_user_chat=user_chat), join_type="OR"), 
                created_date__gte=user_chat.started_date, 
                status=OrderStatus.confirm
                #status__in=[OrderStatus.confirm, OrderStatus.paid]
            ).prefetch_related("other_user_chat").prefetch_related("bot_user").order_by('support_name').all()

            if user_chat.type == ChatRole.writer:
                other_orders = await Order.filter(
                    Q(Q(user_chat=user_chat), Q(other_user_chat=user_chat), join_type="OR"), 
                    created_date__gte=user_chat.started_date, 
                    status=OrderStatus.paid,
                    other_profit_amount=0
                    #status__in=[OrderStatus.confirm, OrderStatus.paid]
                ).prefetch_related("other_user_chat").prefetch_related("bot_user").order_by('support_name').all()
            else:
                other_orders = await Order.filter(
                    Q(Q(user_chat=user_chat), Q(other_user_chat=user_chat), join_type="OR"), 
                    created_date__gte=user_chat.started_date, 
                    status=OrderStatus.paid,
                    profit_amount=0
                    #status__in=[OrderStatus.confirm, OrderStatus.paid]
                ).prefetch_related("other_user_chat").prefetch_related("bot_user").order_by('support_name').all()
            for other_order in other_orders:
                try:
                    next(order for order in orders if order.id == other_order.id)
                except:
                    orders.insert(len(orders), other_order)

        # if user_chat.type == ChatRole.writer and scrap_orders is None:
        #     other_orders = await Order.filter(
        #         other_user_chat=user_chat, 
        #         created_date__gte=user_chat.started_date, 
        #         status=OrderStatus.confirm
        #     #status__in=[OrderStatus.confirm, OrderStatus.paid]
        #     ).prefetch_related("other_user_chat").all()
        #     for other_order in other_orders:
        #         try:
        #             next(order for order in orders if order.id == other_order.id)
        #         except:
        #             orders.insert(len(orders), other_order)
        for order in orders:
            order.status = OrderStatus.paid
            
            order_fine = order.fine
            if user_chat.type == ChatRole.writer:
                order_fine = order.other_fine
                order.other_rates = user_chat.rates
            else:
                order.rates = user_chat.rates

            if user_chat.type == ChatRole.writer:
                chat_commission = user_chat.commission if order.other_fine == 0 else order.other_fine
            else:
                chat_commission = user_chat.commission if order.fine == 0 else order.fine
            
            profit = int(round( float(order.amount - round((chat_commission/100*order.amount), 2)) / float(user_chat.rates), 0))
            if user_chat.type == ChatRole.writer:
                order.other_profit_amount=profit
            else:
                order.profit_amount=profit
            if order_fine > 0:
                commission_remainder = int(chat_commission/100*order.amount)
                total_payed += round(order.amount - commission_remainder, 2)
                fine_formula += " {total} - {precent}% ({commission_sum}) = {payed_amount} ".format(
                    total=round(order.amount, 2),
                    precent=chat_commission,
                    commission_sum=commission_remainder,
                    payed_amount=round(order.amount - commission_remainder, 2)
                )
            else:
                total_amount += order.amount
            order.step_rates = user_chat.step_rates
            await order.save()
        
        commission_remainder = round((user_chat.commission/100*total_amount), 2)
        total_payed += round(total_amount - commission_remainder, 2)
        if total_amount:
            formula += "{fine_formula} {total} - {precent}% ({commission_sum}) = {payed_amount} ".format(
                fine_formula=fine_formula,
                total=round(total_amount, 2),
                precent=user_chat.commission,
                commission_sum=commission_remainder,
                payed_amount=round(total_amount - commission_remainder, 2)
            )
        else:
            formula += "{fine_formula} ".format(
                fine_formula=fine_formula,
            )
        pay_from_rates = total_payed / float(user_chat.rates)
        formula = formula[:-1] + "\n{total_payed} / {user_chat.rates} = {pay_from_rates}$</code>".format(total_payed=total_payed, user_chat=user_chat, pay_from_rates=amount_fm(int(round(pay_from_rates, 0))))
            
    orders = await Order.filter(
        Q(Q(user_chat=user_chat), Q(other_user_chat=user_chat), join_type="OR"), 
        created_date__gte=user_chat.started_date
    ).prefetch_related("bot_user").order_by('support_name').all()

    wait_orders = await Order.filter(
        Q(Q(user_chat=user_chat), Q(other_user_chat=user_chat), join_type="OR"), 
        created_date__lte=user_chat.started_date,
        status=OrderStatus.pending
    ).prefetch_related("bot_user").order_by('support_name').all()

    for other_order in wait_orders:
        try:
            next(order for order in orders if order.id == other_order.id)
        except:
            orders.insert(len(orders), other_order)

    # if user_chat.type == ChatRole.writer:
    #     other_orders = await Order.filter(
    #         other_user_chat=user_chat, 
    #         created_date__gte=user_chat.started_date
    #     ).all()
    #     for other_order in other_orders:
    #         try:
    #             next(order for order in orders if order.id == other_order.id)
    #         except:
    #             orders.insert(len(orders), other_order)

    # static_orders = await Order.filter(
    #     Q(Q(user_chat=user_chat), Q(other_user_chat=user_chat), join_type="OR"), 
    #     created_date__gte=user_chat.started_date,
    #     is_static=True
    # ).prefetch_related("bot_user").order_by('support_name').all()

    # wait_static_orders = await Order.filter(
    #     Q(Q(user_chat=user_chat), Q(other_user_chat=user_chat), join_type="OR"), 
    #     created_date__lte=user_chat.started_date,
    #     status=OrderStatus.pending,
    #     is_static=True
    # ).prefetch_related("bot_user").order_by('support_name').all()

    confirm_orders_amount = 0
    paid_orders_amount = 0
    cancel_orders_amount = 0
    pending_orders_amount = 0
    all_orders_amount = 0

    # for other_order in wait_static_orders:
    #     try:
    #         next(order for order in static_orders if order.id == other_order.id)
    #     except:
    #         pending_orders_amount += other_order.amount
    #         all_orders_amount += other_order.amount
    #         static_orders.insert(len(static_orders), other_order)


    user_chat_advertising = await UserChatAdvertising.filter(bot_user=user_chat.bot_user, user_chat_type=user_chat.type).first()

    advertising_text = "" if user_chat_advertising is None else "\n{text}".format(text=user_chat_advertising.text)
    orders_text = await print_orders_text(orders, user_chat)

    orders_text = "📊 Статистика:\n{orders_text}".format(orders_text=orders_text)
   
    for order in orders:
        if order.status == OrderStatus.cancel:
            cancel_orders_amount += order.amount
        elif order.status == OrderStatus.pending:
            pending_orders_amount += order.amount
        elif order.status == OrderStatus.confirm:
            confirm_orders_amount += order.amount
        else:
            paid_orders_amount += order.amount
        all_orders_amount += order.amount
    limit_rates = await get_rates_order()
    footer_text=(
        "🎯Срезы/отмененные заявки: <b>{cancel}₽</b>\n⚖️ Процент чата: <b>{user_chat.commission}%</b>\n📲 Ожидаем: <b>{pending}₽</b>\n💳 К выплате: <b>{confirm_order}₽</b>\n✅ Выплачено: <b>{paid_order}₽</b>\n💴 Общая сумма: <b>{total}₽</b>\n\n"
        .format(
            cancel=amount_fm(cancel_orders_amount),
            user_chat=user_chat,
            pending=amount_fm(pending_orders_amount),
            confirm_order=amount_fm(confirm_orders_amount),
            paid_order=amount_fm(paid_orders_amount),
            total=amount_fm(all_orders_amount),
            dep_usd=(amount_fm(round(user_chat.limit / limit_rates)))
        )
    )
    company_name = "" if user_chat.bot_user.company_name is None else user_chat.bot_user.company_name

    if user_chat.step_rates >= 1:
        max_step_rates = await Order.filter(
            Q(Q(user_chat=user_chat), Q(other_user_chat=user_chat), join_type="OR"),
            created_date__gte=user_chat.started_date,
            status=OrderStatus.paid
        ).all().annotate(max_step=Max("step_rates")).first().values("max_step")
        orders = await Order.filter(
            Q(Q(user_chat=user_chat), Q(other_user_chat=user_chat), join_type="OR"),
            created_date__gte=user_chat.started_date,
            status=OrderStatus.paid
        ).all()

        if orders:
            await user_chat.save()
            step_with = dict()
            for i in range(max_step_rates['max_step']):
                i += 1
                step_with[i] = {"ids":"", "total": 0, "rates":""}
            for order in orders:
                amount = order.profit_amount
                if user_chat.type == ChatRole.writer:
                    amount = order.other_profit_amount
                if amount == 0:
                    continue
                step_with[order.step_rates]['ids'] += "#{id}, ".format(id=order.id)
                step_with[order.step_rates]['total'] += amount
                step_with[order.step_rates]['rates'] = str(order.other_rates if user_chat.type == ChatRole.writer else order.rates)
            i = 1
            for step in step_with:
                if step_with[step]['total']:
                    footer_text += "Выплаты💲 #{id}\n - {orders} | {rates}р | {total}$\n".format(id=i,orders=step_with[step]['ids'][0:-2],rates=step_with[step]['rates'],total=int(round(step_with[step]['total'], 0)))
                    i += 1
    dep_text = ""
    if user_chat.notify_deposit == ChatDepositNotify.active:
        dep_text = "\n🏦 Депозит {dep_usd}$({dep_rub}₽)\nИспользовано: {used_dep_usd}$({used_dep_rub}₽)".format(
            dep_usd=(amount_fm(round(user_chat.limit / limit_rates))), 
            dep_rub=amount_fm(user_chat.limit), 
            used_dep_usd=(amount_fm(round(confirm_orders_amount / limit_rates))),
            used_dep_rub=amount_fm(confirm_orders_amount)
            )
    text=(

        "📆 {company_name}\nНачало работы: {started_date}{advertising_text}\n\n{orders_text}\n{footer_text}{dep_text}"
        .format(
            company_name=company_name,
            started_date=user_chat.started_date.strftime("%Y-%m-%d"),
            advertising_text=advertising_text,
            orders_text=orders_text,
            footer_text=footer_text,
            dep_text=dep_text
        )
    )

    if is_rates:
        if other_rates:
            return formula
        await bot.send_message(chat_id=user_chat.id, text=formula)

    return text


async def get_emoji_status_order(status):
    match status:
        case OrderStatus.pending:
            return "⌛️"
        case OrderStatus.confirm:
            return "☑️"
        case OrderStatus.paid:
            return "✅"
        case OrderStatus.cancel:
            return "🎯"

async def print_orders_text(orders, user_chat, is_static=False):
    if user_chat.type == ChatRole.cc:
        orders = sorted(orders, key=attrgetter('id'))
    rates_order = await get_rates_order()
    orders_text = ""
    first_name = ""
    i = 0
    for order in orders:
        if not order.support_name or user_chat.type == ChatRole.cc:
            order.support_name = "Общее"
    for order in orders:
        if orders_text.find("#{id}".format(id=order.id)) != -1:
            continue

        if user_chat.type == ChatRole.writer:
            chat_commission = user_chat.commission if order.other_fine == 0 else order.other_fine
        else:
            chat_commission = user_chat.commission if order.fine == 0 else order.fine
        # if user_chat.type == ChatRole.writer:
        if first_name != order.support_name:
            if order.support_name:
                first_name = order.support_name
                total = 0
                total_usd = 0
                for k in range(i, len(orders)):
                    if first_name != orders[k].support_name:
                        break
                    total += orders[k].amount
                    if user_chat.type == ChatRole.writer:
                        chat_commission = user_chat.commission if orders[k].other_fine == 0 else orders[k].other_fine
                    else:
                        chat_commission = user_chat.commission if orders[k].fine == 0 else orders[k].fine
                    if orders[k].status == OrderStatus.paid:
                        total_usd += orders[k].other_profit_amount if user_chat.type == ChatRole.writer else orders[k].profit_amount
                    else:
                        total_usd += int(round( float(orders[k].amount - round((chat_commission/100*orders[k].amount), 2)) / float(rates_order), 0))
                # if int(total_usd) == 0:
                #     if rates_order:
                #         total_usd =  "(~{total_usd}$)".format(total_usd=round( float(total - round((chat_commission/100*total), 2)) / float(rates_order.rates), 2))
                # else:
                total_usd =  "({total_usd}$)".format(total_usd=int(round(total_usd, 0)))
                orders_text += "\n\n💰💰💰{first_name} - {total}₽ ~{total_usd}💰💰💰\n\n\n".format(first_name=order.support_name, total=amount_fm(total), total_usd=total_usd)

        emoji_status = await get_emoji_status_order(order.status)
        if user_chat.type == ChatRole.writer:
            amount = order.other_profit_amount
            order_rates = order.other_rates
            order_fine_text = "🏷{fine}%".format(fine=user_chat.commission) if order.other_fine == 0 else "🏷{fine}%".format(fine=order.other_fine)
        else:
            other_chat_name = ""
            if order.user_chat_id != order.other_user_chat_id:
                other_user_chat = await UserChat.filter(id=order.other_user_chat_id).first()
                other_chat_name = other_user_chat.name[0:3]
            amount = order.profit_amount
            order_rates = order.rates
            order_fine_text = "{other_chat_name} 🏷{fine}%".format(other_chat_name=other_chat_name,fine=user_chat.commission) if order.fine == 0 else "{other_chat_name} 🏷{fine}%".format(other_chat_name=other_chat_name,fine=order.fine)
        order_rates_text = ""
        if order.status == OrderStatus.paid:
            if amount == 0:
                emoji_status = "☑️"
                order_rates_text = "(~{amount}$)".format(amount=int(round( float(order.amount - round((chat_commission/100*order.amount), 2)) / float(rates_order), 0)))
            else:
                order_rates_text = "({amount}$)".format(amount=int(round(amount, 0)))
                if user_chat.type == ChatRole.writer:
                    order_rates_text = "({amount}$ | {rates}₽)".format(amount=int(round(amount, 0)), rates=order_rates)
        elif rates_order:
            order_rates_text = "(~{amount}$)".format(amount=int(round( float(order.amount - round((chat_commission/100*order.amount), 2)) / float(rates_order), 0)))
        if order.support_name ==  "Общее":
            order.support_name = ""          
        orders_text += "{emoji_status}{order_fine_text} #{order.id} | {order.bank} {order.name} {order.card_number} {order.support_name} - {amount}₽ {rates_amount}\n".format(emoji_status=emoji_status,order_fine_text=order_fine_text,order=order,rates_amount=order_rates_text,amount=amount_fm(order.amount))
        i += 1
    return orders_text

async def create_order(user_chat, bot_user, parse_text, status, delivery_id=0):
    if user_chat.type in [ChatRole.cc, ChatRole.writer]:
        orders = await Order.filter(
            user_chat=user_chat,
            created_date__gte=user_chat.started_date,
            status__in=[OrderStatus.confirm, OrderStatus.pending]
        ).all().annotate(total=Sum("amount")).first().values("total")
        data = list(filter(None, parse_text.split(" ")))
        order = Order(
            user_chat=user_chat, 
            bot_user=bot_user, 
            other_user_chat = user_chat,
            other_bot_user = bot_user,
            status=status)
        other_amount = 0
        if not str(filter_amount(data[-1])).isnumeric():
            other_amount = str(data[-2])
            order.support_name = str(data[-1]).upper()
            del data[-1]
        if len(data) == 2:
            order.bank = str(data[0])
            amount = str(data[1])
        elif len(data) == 3:
            order.bank = str(data[0])
            order.name = str(data[1])
            amount = str(data[2])
        elif len(data) == 4:
            order.bank = str(data[0])
            order.name = str(data[1])
            order.card_number = str(data[2])
            amount = str(data[3])
        elif len(data) == 5:
            order.bank = str(data[0])
            order.name = str(data[1])
            order.card_number = "{data1} {data2}".format(data1=data[2], data2=data[3])
            amount = str(data[4])
        else:
            return -1
        
        if not order.support_name:
            for d in data:
                if str(d).upper() in ['JT','LE','AL','JA','WA','TO','DI','LA','ЖТ','ДИ','ЛА','ЛЕ','АЛ','МА','ВА','ДЖ','ТО']:
                    order.support_name = str(d).upper()
                    break
        if other_amount:
            amount = other_amount
        order.amount = filter_amount(amount)
        total_amount = number_or(orders['total']) + int(order.amount)
        if total_amount >= user_chat.notify_limit and user_chat.type == ChatRole.writer:
            await bot.send_message(user_chat.id, text="🛑🛑🛑Внимание, превышен лимит депозита для данной команды 🛑🛑🛑")

        order_fine = await OrderFine.filter(user_chat=user_chat).first()
        if order_fine:
            order.fine = order_fine.fine
            order.other_fine = order.fine
            await order_fine.delete()
        
        order_static = await OrderStatic.filter(user_chat=user_chat, bank=order.bank.upper()).first()
        if order_static:
            order.fine = order_static.commission - order.fine
            order.other_fine = order.fine
            order.is_static = True
        
        order.delivery_id = delivery_id
        await order.save()

        return order.id
    return 0

def number_or(amount):
    return 0 if amount is None else amount

def amount_fm(amount):
    return "{:,}".format(0 if amount is None else amount)

def can_convert_to_float(string):
    try:
        number = float(string)

        return number
    except ValueError:
        return False


async def create_select_support_markup(supports: SupportUserChat, current_bot_user: BotUser):
    markup = (
        InlineKeyboardBuilder()
        .add(*(types.InlineKeyboardButton(
            text="{bot_user.first_name}|{bot_user.username}".format(bot_user=support.bot_user),
            callback_data=UserChatCallbackData(action='select_start_support', data='', id=support.bot_user.id).pack(),
        ) for support in supports))
        .button(text="Выбрать свои чаты", callback_data=UserChatCallbackData(action='select_start_support', data='', id=current_bot_user.id).pack())
        .button(text="Назад", callback_data=AnswerCallbackData(action='main').pack())
        .adjust(1, repeat=True)
        .as_markup()
    )
    return markup

async def create_delivery_markup(delivery):
    markup = (
        InlineKeyboardBuilder()
        .add(*(types.InlineKeyboardButton(
            text="{data}".format(data=deliv["data"]),
            callback_data=DeliveryCallbackData(action='select_delivery', id=deliv["id"]).pack(),
        ) for deliv in delivery))
        .adjust(2, repeat=True)
        .as_markup()
    )
    return markup

def filter_amount(amount_str: str):
    amount_str = amount_str.replace(",", ".")
    upper_data = amount_str.upper()
    amount = ""
    try:
        if upper_data.find("КК") != -1:
            return int(float(upper_data.replace("КК", "")) * 1000000)
        elif upper_data.find("К") != -1:
            return int(float(upper_data.replace("К", "")) * 1000)
        elif upper_data.find("ТТ") != -1:
            return int(float(upper_data.replace("ТТ", "")) * 1000000)
        elif upper_data.find("Т") != -1:
            return int(float(upper_data.replace("Т", "")) * 1000)
        else:
            return amount_str.replace(".", "")
    except:
        return amount_str


async def get_rates_order(): 
    # return 98.5
    yesterday = datetime.now(timezone(bot.config.timezone)) - timedelta(days=1)
    yesterday = yesterday.replace(hour=23, minute=59)
    rates_order = await Order.filter(created_date__lte=yesterday,  rates__gt=0, user_chat__type=ChatRole.cc).order_by("-id").first()
    if rates_order is None:
        rates_order = await Order.filter(rates__gt=0, user_chat__type=ChatRole.cc).order_by("-id").first()
    return rates_order.rates