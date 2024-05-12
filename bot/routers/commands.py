from aiogram import F, types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.types import ReactionTypeEmoji
from contextlib import suppress
import time
from tortoise.expressions import Q

from .. import markups
from ..bot import bot
from ..filters.registered import SupportFilter
from ..services.database.models import BotUser, UserChat, Order, ProfitUserChat, TimerMessage, ProfitUser, OrderStatic, Delivery, SupportUserChat, TaskQueue, Notify
from ..enums import ChatRole, OrderStatus, TaskQueueType, ChatDepositNotify
from ..utils.router import Router
from . import root_handlers_router
from ..state import Action
from ..callback_data import TimerActionCallbackData
from tortoise.functions import Sum
from datetime import datetime, timedelta
from pytz import timezone
from .chat import get_stats, start_day, migrate_chat_id, number_or, create_delivery_markup, create_order, can_convert_to_float, filter_amount, amount_fm, get_rates_order

router = Router()
root_handlers_router.include_router(router)

@router.message(F.chat.type != "private", F.text.lower() == '/start', SupportFilter(support=True))
async def start_handler(message: types.Message, bot_user: BotUser):
    user_chat = await UserChat.filter(id=message.chat.id).prefetch_related("bot_user").first()
    if user_chat:
        if user_chat.type == ChatRole.none:
            return await message.answer("Выберите подходящий тип группы в ЛС бота")
        try:
            await start_day(user_chat)
        except Exception as e:
            if hasattr(e, "migrate_to_chat_id"):
                new_user_chat = await migrate_chat_id(user_chat, e.migrate_to_chat_id)
                try:
                    await start_day(new_user_chat)
                except Exception as e:
                    code = str(e).split(": ")[1].capitalize() if len(str(e).split(": ")) > 1 else "Внутренняя ошибка, пожалуйста, обратитесь в поддержку"
                    text = "Ошибка при работе с группой <b>{user_chat.name}</b>\n\nКод: {code}".format(user_chat=user_chat, code=code)
                    await bot.send_message(bot_user.id, text)
            else:
                code = str(e).split(": ")[1].capitalize() if len(str(e).split(": ")) > 1 else "Внутренняя ошибка, пожалуйста, обратитесь в поддержку"
                if code == "Найдена активная заявка, группа поставлена в очередь":
                    await message.answer("❗️Ошибка: {code}".format(code=code))
                text = "Ошибка при работе с группой <b>{user_chat.name}</b>\n\nКод: {code}".format(user_chat=user_chat, code=code)
                await bot.send_message(bot_user.id, text)

@router.message(F.chat.type != "private", F.text.find("/adm") == 0, SupportFilter(support=True))
async def create_support_in_chat_handler(message: types.Message, state: FSMContext, bot_user: BotUser):
    user_chat = await UserChat.filter(id=message.chat.id).prefetch_related("bot_user").first()
    if user_chat:
        usernames = list(filter(None,message.text.replace("/adm ", "").replace("/adm ", "").replace("@", "").split(" ")))
        for username in usernames:
            other_user = await BotUser.filter(username=username).first()
            if username == message.from_user.username:
                await message.answer("❗️ Ошибка, Вы не можете добавить себя")
            elif other_user is None:
                support_user_chat = await SupportUserChat.filter(bot_user=user_chat.bot_user, username=username).first()
                if support_user_chat:
                    await message.answer("❗️ Ошибка, пользователь уже добавлен в список для @{username}".format(username=username))
                else:
                    support_user_chat = await SupportUserChat.create(
                            bot_user=user_chat.bot_user, 
                            other_bot_user=bot_user,
                            username=username
                        )
                    await message.answer("✅ Саппорт @{username} успешно добавлен в список".format(username=username))
            else:
                support_user_chat = await SupportUserChat.filter(bot_user=user_chat.bot_user, other_bot_user=other_user).first()
                if support_user_chat:
                    await message.answer("❗️ Ошибка, пользователь уже добавлен в список для @{username}".format(username=username))
                else:
                    support_user_chat = await SupportUserChat.create(
                            bot_user=user_chat.bot_user, 
                            other_bot_user=other_user
                        )
                    await message.answer("✅ Саппорт @{other_user.username} успешно добавлен в список".format(other_user=other_user))

@router.message(F.chat.type != "private", F.text.find("/set_profit") == 0, SupportFilter(support=True))
async def create_pending_order_handler(message: types.Message, state: FSMContext, bot_user: BotUser):
    user_chat = await UserChat.filter(id=message.chat.id).prefetch_related("bot_user").first()
    profit_user_chat = await ProfitUserChat.filter(user_chat=user_chat).first()
    
    if profit_user_chat:
        return await message.answer("Данный чат уже добавлен в список <b>Резак Капусты</b>")
    if user_chat.type == ChatRole.cc:
        explode_data = message.text.split(" ")
        profit_user = await ProfitUser.filter(uuid=explode_data[1]).prefetch_related("bot_user").first()
        if profit_user:
            if profit_user.bot_user_id == user_chat.bot_user_id:
                return await message.answer("Вы не можете добавить себя в качестве реферала")
            await ProfitUserChat.create(
                bot_user=profit_user.bot_user,
                user_chat=user_chat
            )
            text="✅ Чат <b>{chat_name}</b> успешно добавлен в модуль <b>Резак Капусты</b>, для пользователя @{username}\n\n<i>❕ Установите комиссию вознограждения для этого пользователя, в разделе <b>Резак капусты</b></i>".format(chat_name=user_chat.name,username=profit_user.bot_user.username)
            await bot.send_message(user_chat.bot_user.id, text, reply_markup=markups.skip_markup)
            await message.answer("✅ Чат успешно добавлен")

@router.message(F.chat.type != "private", F.text.lower() == '/help')
async def help_handler(message: types.Message,  bot_user: BotUser):
    text = ("Доступные команды для чата:\n\n<b>✔️(Банк) (Способ пополнения) (Фамилия дропа/Номер карты )(2 буквы имени саппорта) (сумма в рублях) (имя саппорта)</b> – данная команда ставит заявку в статус «подтверждена». Этот статус означает что сторона Б подтверждает наличие средств на балансе но еще не выплатила долю стороне А. Пример: <code>✔️Альфа Кешин Козлов 300.000</code> или <code>✔️Альфа Кешин Козлов 300.000 Лебовский</code>\n\n<b>✅#(Номер записи)</b> - данная команда ставит заявку в статус «Оплачено». Этот статус означает что сторона Б подтвердила и оплатила данную заявку стороне А. Пример: <code>✅#77</code>\n\n<b>⏳(Банк) (Способ пополнения) (Фамилия дропа) (сумма в рублях)</b> - данная команда ставит заявку в статус «В ожидании». Этот статус означает что сторона А отправила средства на выданный реквизит, но сторона Б данные средства еще не получила. Заявки отмеченные данным статусом переносятся на все последующие дни, пока сторона Б не изменит данный статус заявки. Пример: <code>⏳Альфа Кешин Козлов 300.000</code>\n\n<b>🚫#(Номер записи)</b> - данная команда Удаляет выбранную заявку из статы в закрепе. Пример: <code>🚫#77</code>\n\n<b>✍️(Банк) (сумма в рублях)</b> - данная команда необходима для редактирования процента комиссии по определенной заявке.. Пример: <code>✍️Альфа 30%</code>\n\n<b>✍️(Номер записи) (процент)</b> - данная команда изменяет процент по определнной заявке... Пример: <code>✍️#77 15.00%</code>\n\n<b>🔄(Номер записи) (сумма в рублях)</b> - данная команда необходима для редактирования суммы к определенной зявке... Пример: <code>🔄#77 100.000</code>\n\n<b>💱(Номер записи) (курс)</b> - данная заявка изменяет курс для определнной выплаченной заявке... Пример: <code>💱#77 92.54</code>")
    await message.answer(text=text)

@router.message(F.chat.type != "private", F.text.lower() == '/botinfo')
async def bot_info_handler(message: types.Message, bot_user: BotUser):
    text = "/gameinfo - правилы игры\n/help - доступные команду и информация о них"
    await message.answer(text=text)

@router.message(F.chat.type != "private", F.text.lower() == '/gameinfo')
async def game_info_handler(message: types.Message, bot_user: BotUser):
    text = "Правило игры заполняется для начало отправьте команду /game"
    await message.answer(text=text)

@router.message(F.chat.type != "private", F.text.lower() == '/stats')
async def stats_handler(message: types.Message, bot_user: BotUser):
    text = "Выберите метод фильтрации:"
    await message.answer(text=text, reply_markup=markups.user_chat_filter_stats_markup)

@router.message(F.chat.type != "private", F.text.lower().find("#рек") != -1)
async def send_rek_handler(message: types.Message, bot_user: BotUser):
    user_chat = await UserChat.filter(id=message.chat.id).prefetch_related("bot_user").first()    
    if user_chat.bot_user.function_rek:
        delivery = await Delivery.filter(bot_user=user_chat.bot_user).all()
        if len(delivery) > 0:
            delivery_data = list()
            for deliv in delivery:
                deliv_orders = await Order.filter(delivery_id=deliv.id).all().annotate(total=Sum("amount")).first().values("total")
                order_sum = number_or(deliv_orders['total'])
                data = "{bank} {order_sum}/{limit}".format(
                    bank=deliv.bank_name, 
                    order_sum=order_sum if order_sum < 1000000 else "{order_sum}кк".format(order_sum=str(order_sum/1000000).replace(".0", "")),
                    limit=deliv.limit if deliv.limit < 1000000 else "{limit}кк".format(limit=str(deliv.limit/1000000).replace(".0", ""))
                    )
                delivery_data.append({"data": data, "id": deliv.id})
            await message.answer("Выберите раздел:", reply_markup= await create_delivery_markup(delivery_data))
        else:
           await message.answer("Реквизиты не найдены.")

@router.message(F.chat.type != "private", F.text.lower().find("#дай") != -1)
async def start_timer_handler(message: types.Message, bot_user: BotUser):
    user_chat = await UserChat.filter(id=message.chat.id).prefetch_related("bot_user").first()    
    if user_chat.bot_user.function_day:
        start_time = time.time()
        end_time = start_time + 180
        timer = await TimerMessage.create(
            user_chat=user_chat,
            start_time=start_time,
            end_time=end_time
        )
        day_function_markup = (
            InlineKeyboardBuilder()
            .button(text="✅ Успел", callback_data=TimerActionCallbackData(action='done', timer_id=timer.id).pack())
            .button(text="➕ Еще 3 мин", callback_data=TimerActionCallbackData(action='add_minutes', timer_id=timer.id).pack())
            .button(text="🚫 Нет такого", callback_data=TimerActionCallbackData(action='cancel', timer_id=timer.id).pack())
            .adjust(1, repeat=True)
            .as_markup()
        )
        timer_message = await message.answer("Таймер запушен, у вас асталось: 3:00м.", reply_markup=day_function_markup)
        timer.message_id = timer_message.message_id
        await timer.save()
        await message.react([ReactionTypeEmoji(emoji="🔥")])

@router.message(F.chat.type != "private", F.text.find("⏹") == 0, SupportFilter(support=True))
async def stop_notify_deposit_limit_handler(message: types.Message, state: FSMContext, bot_user: BotUser):
    user_chat = await UserChat.filter(id=message.chat.id).prefetch_related("bot_user").first()    
    user_chat.notify_deposit = ChatDepositNotify.disabled
    await user_chat.save()
    await message.answer("✅Уведомление успешно отключено")

@router.message(F.chat.type != "private", F.text.find("🏦") == 0, SupportFilter(support=True))
async def create_deposit_limit_handler(message: types.Message, state: FSMContext, bot_user: BotUser):
    data = message.text.replace("🏦 ", "").replace("🏦", "").lstrip()
    if data.find("$") != -1:
        amount = int(await get_rates_order() * int(data.replace(".", "").replace("$", "")))
    else:
        amount = int(data.replace(".", ""))
    # await message.answer(amount)
    if can_convert_to_float(amount):
        user_chat = await UserChat.filter(id=message.chat.id).prefetch_related("bot_user").first()    
        user_chat.limit = amount
        user_chat.notify_deposit = ChatDepositNotify.active
        await user_chat.save()
        notify = await Notify.filter(user_chat=user_chat).first()
        if notify:
            await notify.delete()
        await message.answer("✅ Депозит на сумму <b>{amount}₽</b> успешно создан".format(amount=amount_fm(amount)))
        await bot.edit_message_text(chat_id=user_chat.id, text=await get_stats(user_chat), message_id=user_chat.secured_id, reply_markup=markups.set_rates_markup)
    else:
        return await message.answer("Неверный формат команды, введите число")


@router.message(F.chat.type != "private", F.text.find("✍️") == 0, SupportFilter(support=True))
async def create_static_order_handler(message: types.Message, state: FSMContext, bot_user: BotUser):
    user_chat = await UserChat.filter(id=message.chat.id).prefetch_related("bot_user").first()    
    data = message.text.replace("%", "").replace("✍️ ", "").replace("✍️", "").lstrip()
    list_data = data.split("\n")
    for data in list_data:
        if can_convert_to_float(data):
            user_chat.commission = data
            await user_chat.save()
            await message.answer("✅ Процента чата успешно изменен на {commission}%".format(commission=user_chat.commission))
            return await bot.edit_message_text(chat_id=user_chat.id, text=await get_stats(user_chat), message_id=user_chat.secured_id, reply_markup=markups.set_rates_markup)
        elif data.find("#") == 0:
            split_data = data.replace("#", "").split(" ")
            if can_convert_to_float(split_data[0]) and can_convert_to_float(split_data[1] and len(split_data) == 2):
                order = await Order.filter(
                    Q(Q(user_chat=user_chat), Q(other_user_chat=user_chat), join_type="OR"),
                    id=split_data[0]).first()
                if order:
                    if user_chat.type == ChatRole.writer:
                        order.other_fine = float(split_data[1])
                    else:
                        order.fine = float(split_data[1])
                    await order.save()
                    if order.status == OrderStatus.paid:
                        await get_stats(user_chat, True, [order.id])
        else:
            split_data = list(filter(None, data.split(" ")))
            last_index = len(split_data) - 1
            if can_convert_to_float(split_data[last_index]):
                commission = split_data[last_index]
                del split_data[last_index]
                bank_name = " ".join(map(str, split_data)).strip()
                if bank_name[1] == " ":
                    bank_name = bank_name[2:]
                order_static = await OrderStatic.filter(user_chat=user_chat, bank=bank_name.upper()).first()
                if order_static:
                    order_static.commission = commission
                else:
                    order_static = OrderStatic(
                        user_chat=user_chat,
                        bank=bank_name.upper(),
                        commission=commission
                    )
                await order_static.save()
                await message.answer("✅ Данные для {bank} успешно обновлены".format(bank=order_static.bank))
                orders = await Order.filter(user_chat=user_chat, created_date__gte=user_chat.started_date, status__in=[OrderStatus.confirm, OrderStatus.pending])
                if orders:
                    for order in orders:
                        if order.bank.upper() == order_static.bank:
                            if user_chat.type == ChatRole.writer:
                                order.other_fine = float(split_data[1])
                            else:
                                order.fine = float(split_data[1])
                            order.is_static = True
                            await order.save()
            else:
                return await message.answer("Введите число!")
    await bot.edit_message_text(chat_id=user_chat.id, text=await get_stats(user_chat), message_id=user_chat.secured_id, reply_markup=markups.set_rates_markup)
    await message.react([ReactionTypeEmoji(emoji="🔥")])

@router.message(F.chat.type != "private", F.text.find("⏳") == 0, SupportFilter(support=True))
async def create_pending_order_handler(message: types.Message, state: FSMContext, bot_user: BotUser):
    user_chat = await UserChat.filter(id=message.chat.id).prefetch_related("bot_user").first()    
    data =  message.text.lstrip().replace("#", "").replace("⏳", "").lstrip()
    list_data = data.split("\n")
    for data in list_data:
        result = await create_order(user_chat, bot_user, data, OrderStatus.pending)
        if result == -1:
            return await message.answer("Неверный формат команды")
        if result == 0:
            return await message.answer("Не подходяший тип группы для этой команды")
        await bot.edit_message_text(chat_id=user_chat.id, text=await get_stats(user_chat), message_id=user_chat.secured_id, reply_markup=markups.set_rates_markup)
    #reaction = list(ReactionTypeEmoji(type=ReactionTypeType.EMOJI, emoji="👍"))
    #await bot.set_message_reaction(user_chat.id, message.message_id, reaction, is_big=False)
    await message.react([ReactionTypeEmoji(emoji="🔥")])
    await message.answer("#{order_id}".format(order_id=result))

@router.message(F.chat.type != "private", F.text.find("✅") == 0, SupportFilter(support=True))
async def create_pending_order_handler(message: types.Message, state: FSMContext, bot_user: BotUser):
    user_chat = await UserChat.filter(id=message.chat.id, type=ChatRole.cc).prefetch_related("bot_user").first()  
    if user_chat:  
        order_id = message.text.replace("#", "").replace("✅", "").replace("✅ ", "").lstrip()
        list_data = order_id.split("\n")
        is_reaction = False
        for order_id in list_data:
            if order_id.isnumeric():
                order = await Order.filter(id=order_id).prefetch_related("other_user_chat").first()
                if order is None:
                    return await message.answer("Заявка не найдена")
                order.fine = 0
            else:
                split_data = order_id.replace("%", "").split(" ")
                order = await Order.filter(id=split_data[0]).prefetch_related("other_user_chat").first()
                if order is None:
                    return await message.answer("Заявка не найдена")
                order.fine = split_data[1]
            if order:
                if order.user_chat_id == user_chat.id:
                    return await message.answer("Данная заявка уже добавлена в эту группу")
                if order.user_chat_id != order.other_user_chat_id:
                    return await message.answer("Данная заявка уже добавлена в другую группу")
                if order.user_chat_id == order.other_user_chat_id:
                    old_user_chat = 0
                else:
                    old_user_chat = order.user_chat_id
                order.created_date = datetime.now(timezone(bot.config.timezone))
                # order.bot_user = bot_user
                order.user_chat = user_chat
                #order.status = OrderStatus.paid
                order.other_bot_user = bot_user
                await order.save()
                await order.other_user_chat.fetch_related("bot_user")
                if not is_reaction:
                    await message.react([ReactionTypeEmoji(emoji="🔥")])
                if old_user_chat:
                    with suppress(Exception):
                        old_user_chat = await UserChat.filter(id=old_user_chat).prefetch_related("bot_user").first()  
                        await bot.edit_message_text(chat_id=old_user_chat.id, text=await get_stats(old_user_chat), message_id=old_user_chat.secured_id, reply_markup=markups.set_rates_markup)
                with suppress(Exception):
                    await bot.edit_message_text(chat_id=user_chat.id, text=await get_stats(user_chat), message_id=user_chat.secured_id, reply_markup=markups.set_rates_markup)
                with suppress(Exception):
                    await bot.edit_message_text(chat_id=order.other_user_chat.id, text=await get_stats(order.other_user_chat), message_id=order.other_user_chat.secured_id, reply_markup=markups.set_rates_markup)
            else:
                await message.answer("Заявка не найдена")
                await bot.edit_message_text(chat_id=user_chat.id, text=await get_stats(user_chat), message_id=user_chat.secured_id, reply_markup=markups.set_rates_markup)
    else:
        await message.answer("Команда не преднозначена для этого типа группы или данные для группые не найдены")
        await bot.edit_message_text(chat_id=user_chat.id, text=await get_stats(user_chat), message_id=user_chat.secured_id, reply_markup=markups.set_rates_markup)

@router.message(F.chat.type != "private", F.text.find("🔄") == 0, SupportFilter(support=True))
async def update_amount_handler(message: types.Message, state: FSMContext, bot_user: BotUser):
    user_chat = await UserChat.filter(id=message.chat.id).prefetch_related("bot_user").first()    
    data = message.text.replace("#", "").replace("🔄", "").replace("🔄 ", "").lstrip()
    list_data = data.split("\n")
    is_reaction = False
    for data in list_data:
        split_data = data.split(" ")
        if split_data[0].isnumeric() and len(split_data) == 2:
            order = await Order.filter(
                Q(Q(user_chat=user_chat), Q(other_user_chat=user_chat), join_type="OR"),
                id=split_data[0]).first()
            if order:
                order.amount = filter_amount(split_data[1])
                await order.save()
                if not is_reaction:
                    await message.react([ReactionTypeEmoji(emoji="🔥")])
                    is_reaction = True
                if order.status == OrderStatus.paid:
                    text = await get_stats(user_chat, True, [order.id])
                else:
                    text = await get_stats(user_chat)
                await bot.edit_message_text(chat_id=user_chat.id, text=text, message_id=user_chat.secured_id, reply_markup=markups.set_rates_markup)
            else:
                await message.answer("Заявка не найдена или удалена")
                await bot.edit_message_text(chat_id=user_chat.id, text=await get_stats(user_chat), message_id=user_chat.secured_id, reply_markup=markups.set_rates_markup)


@router.message(F.chat.type != "private", F.text.find("💱") == 0, SupportFilter(support=True))
async def update_amount_handler(message: types.Message, state: FSMContext, bot_user: BotUser):
    user_chat = await UserChat.filter(id=message.chat.id).prefetch_related("bot_user").first()    
    data = message.text.replace("#", "").replace("💱", "").replace("💱 ", "").lstrip()
    list_data = data.split("\n")
    is_reaction = False
    for data in list_data:
        split_data = data.split(" ")
        if split_data[0].isnumeric() and len(split_data) == 2:
            order = await Order.filter(
                Q(Q(user_chat=user_chat), Q(other_user_chat=user_chat), join_type="OR"),
                id=split_data[0],
                status=OrderStatus.paid).first()
            if order:
                user_chat.rates = float(split_data[1])
                await user_chat.save()
                if not is_reaction:
                    await message.react([ReactionTypeEmoji(emoji="🔥")])
                    is_reaction = True
                text = await get_stats(user_chat, True, [order.id])
                await bot.edit_message_text(chat_id=user_chat.id, text=text, message_id=user_chat.secured_id, reply_markup=markups.set_rates_markup)
            else:
                await message.answer("Заявка не найдена или удалена")
                await bot.edit_message_text(chat_id=user_chat.id, text=await get_stats(user_chat), message_id=user_chat.secured_id, reply_markup=markups.set_rates_markup)

@router.message(F.chat.type != "private", F.text.find("✔️") == 0, SupportFilter(support=True))
async def create_confirm_order_handler(message: types.Message, state: FSMContext, bot_user: BotUser):
    user_chat = await UserChat.filter(id=message.chat.id).prefetch_related("bot_user").first()
    data = message.text.replace("#", "").replace("✔️", "").replace("✔️ ", "").lstrip()
    list_data = data.split("\n")
    is_reaction = False
    for data in list_data:
        if can_convert_to_float(data):
            order = await Order.filter(Q(Q(user_chat=user_chat), Q(other_user_chat=user_chat), join_type="OR"),id=data).first()
            if order:
                if order.status == OrderStatus.pending:
                    order.created_date = datetime.now(timezone(bot.config.timezone))
                order.status = OrderStatus.confirm
                await order.save()
        else:
            result = await create_order(user_chat, bot_user, data, OrderStatus.confirm)
            if result == -1:
                return await message.answer("Неверный формат команды")
            if result == 0:
                return await message.answer("Не подходяший тип группы для этой команды")
        await bot.edit_message_text(chat_id=user_chat.id, text=await get_stats(user_chat), message_id=user_chat.secured_id, reply_markup=markups.set_rates_markup)
        if not is_reaction:
            await message.react([ReactionTypeEmoji(emoji="🔥")])
            await message.answer("#{order_id}".format(order_id=result))
            is_reaction = True
@router.message(F.chat.type != "private", F.text.find("🚫") == 0, SupportFilter(support=True))
async def remove_order_handler(message: types.Message, state: FSMContext, bot_user: BotUser):
    user_chat = await UserChat.filter(id=message.chat.id).prefetch_related("bot_user").first()    
    data = message.text.replace("#", "").replace("🚫", "").replace("🚫 ", "").lstrip()
    list_data = data.split("\n")
    is_reaction = False
    for order_id in list_data:
        if order_id.isnumeric():
            order = await Order.filter(Q(Q(user_chat=user_chat), Q(other_user_chat=user_chat), join_type="OR"),id=order_id).prefetch_related("user_chat").prefetch_related("other_user_chat").first()
            if order:
                other_user_chat = False
                if order.user_chat_id != order.other_user_chat_id:
                    if user_chat.id == order.user_chat_id:
                        other_user_chat = order.other_user_chat_id
                        order.fine = order.other_fine
                        order.user_chat_id = other_user_chat
                    else:
                        other_user_chat = order.user_chat_id
                        order.other_user_chat_id = other_user_chat
                    await order.save()
                else:
                    await order.delete()
                if not is_reaction:
                    await message.react([ReactionTypeEmoji(emoji="🔥")])
                    is_reaction = True
                await bot.edit_message_text(chat_id=user_chat.id, text=await get_stats(user_chat), message_id=user_chat.secured_id, reply_markup=markups.set_rates_markup)
                if other_user_chat:
                    user_chat = await UserChat.filter(id=other_user_chat).prefetch_related("bot_user").first()    
                    await bot.edit_message_text(chat_id=user_chat.id, text=await get_stats(user_chat), message_id=user_chat.secured_id, reply_markup=markups.set_rates_markup)
            else:
                await message.answer("Заявка не найдена или удалена")
                await bot.edit_message_text(chat_id=user_chat.id, text=await get_stats(user_chat), message_id=user_chat.secured_id, reply_markup=markups.set_rates_markup)

@router.message(Action.wait_scrap_set_rates, F.text, SupportFilter(support=True))
async def wait_scrap_set_rates_handler(message: types.Message, state: FSMContext, bot_user: BotUser):
    user_chat = await UserChat.filter(id=message.chat.id).prefetch_related("bot_user").first()
    is_set_rates = True if len(list(filter(None, message.text.split("\n")[0].split(" ")))) == 2 else False
    if is_set_rates:
        other_split_data = message.text.replace("#", "").split("\n")
        scrap_orders = []
        for data in other_split_data:
            order_data = data.split(" ")
            order = await Order.filter(
                Q(Q(user_chat=user_chat), Q(other_user_chat=user_chat), join_type="OR"),
                id=order_data[0]).first()
            if order is None:
                return await message.answer("❗️ Введите правильные данные", reply_markup=markups.cancel_set_rates_markup)
            scrap_orders.append(order_data[0])
            if user_chat.type == ChatRole.writer:
                order.other_rates = order_data[1]
            else:
                order.rates = order_data[1]
            await order.save()
        all_amount = 0
        text = "🧑‍💻 Формула:"
        step_rates = user_chat.step_rates + 1
        for order_id in scrap_orders:
            order = await Order.filter(id=order_id).first()
            if user_chat.type == ChatRole.writer:
                user_chat.rates = order.other_rates
            else:
                user_chat.rates = order.rates
            await user_chat.save()
            text += str(await get_stats(user_chat, True, [order.id], step_rates)).replace("🧑‍💻 Формула:", "")
            order = await Order.filter(id=order_id).first()
            if user_chat.type == ChatRole.writer:
                all_amount += order.other_profit_amount
            else:
                all_amount += order.profit_amount
        await state.clear()
        text = "{text} <code>\n\nТотал: {all_amount}$</code>".format(text=text, all_amount=round(all_amount, 2))
        await message.answer(text)
        try:
            await bot.edit_message_text(chat_id=user_chat.id, text=await get_stats(user_chat), message_id=user_chat.secured_id, reply_markup=markups.set_rates_markup)
        finally:
            await task_queue_checker(user_chat)
    else:
        split_data = message.text.replace(",", "").replace("#", "").split("\n")
        for order_id in split_data:
            order = await Order.filter(
                Q(Q(user_chat=user_chat), Q(other_user_chat=user_chat), join_type="OR"),
                id=order_id).first()
            if order is None:
                return await message.answer("❗️ Введите правильные данные", reply_markup=markups.cancel_set_rates_markup)
        await state.set_data({"scrap_orders": split_data})
        await state.set_state(Action.wait_set_rates)  
        text="Введите курс:"
        await message.answer(text, reply_markup=markups.cancel_set_rates_markup)

@router.message(Action.wait_set_rates, F.text, SupportFilter(support=True))
async def wait_set_rates_handler(message: types.Message, state: FSMContext, bot_user: BotUser):
    if can_convert_to_float(message.text):
        current_state = await state.get_data()
        await state.clear()
        user_chat = await UserChat.filter(id=message.chat.id).prefetch_related("bot_user").first()
        user_chat.rates = message.text
        await user_chat.save()
        await message.answer("✅ Курс успешно установлен")
        text = await get_stats(user_chat, True, current_state['scrap_orders']) if "scrap_orders" in current_state else await get_stats(user_chat, True)
        try:
            await bot.edit_message_text(chat_id=user_chat.id, text=text, message_id=user_chat.secured_id, reply_markup=markups.set_rates_markup)
        finally:
            await task_queue_checker(user_chat=user_chat)
             

def filter_data(data: str):
    return data[2:].lstrip().replace("#", "")


async def task_queue_checker(user_chat: UserChat):
    order = await Order.filter(user_chat=user_chat, created_date__gte=user_chat.started_date, status=OrderStatus.confirm).first()
    if order is None:
        task_queue = await TaskQueue.filter(user_chat=user_chat, type=TaskQueueType.start_day, status=1).first()
        if task_queue:
            task_queue.status=0
            await task_queue.save()
            await start_day(user_chat=user_chat)