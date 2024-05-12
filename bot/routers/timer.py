from aiogram import F, types
from aiogram.filters.command import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder


from ..models.config.bot_config import BotConfig
from ..models.phrases.bot_phrases import BotPhrases
from ..utils.bot import Bot

from .. import markups
from ..bot import bot, scheduler
from ..filters.registered import RegisteredFilter
from ..filters.registered import SupportFilter
from ..callback_data import TimerActionCallbackData

from ..services.database.models import BotUser, TimerMessage
from ..utils.router import Router
from . import root_handlers_router
import time 
from contextlib import suppress
import aiohttp

router = Router()
router.filter(RegisteredFilter(registered=False))
root_handlers_router.include_router(router)


@router.message(F.chat.type != "private", F.text == "/START_TIMER_INTERVAL", SupportFilter(support=True))
async def interval_timer(message: types.Message):
    pass
    # bot2 = Bot(BotConfig.load_first(), BotPhrases.load_first(), parse_mode="HTML")
    # timer_messages = await TimerMessage.filter(status=1).all()
    # for timer in timer_messages:
    #     with suppress(Exception):
    #         text = ""
    #         day_function_markup = ""
    #         m, s = divmod(abs(time.time()-timer.end_time), 60)
    #         if timer.steep == 1:
    #             day_function_markup = (
    #                 InlineKeyboardBuilder()
    #                 .button(text="✅ Успел", callback_data=TimerActionCallbackData(action='done', timer_id=timer.id).pack())
    #                 .button(text="➕ Еще 3 мин", callback_data=TimerActionCallbackData(action='add_minutes', timer_id=timer.id).pack())
    #                 .button(text="🚫 Нет такого", callback_data=TimerActionCallbackData(action='cancel', timer_id=timer.id).pack())
    #                 .adjust(1, repeat=True)
    #                 .as_markup()
    #             )
    #             text="Таймер запушен, у вас асталось: {m}:{s}м.".format(m=int(m),s=int(s))
    #         else:
    #             day_function_markup = (
    #                 InlineKeyboardBuilder()
    #                 .button(text="✅ Успел", callback_data=TimerActionCallbackData(action='done', timer_id=timer.id).pack())
    #                 .button(text="🚫 Нет такого", callback_data=TimerActionCallbackData(action='cancel', timer_id=timer.id).pack())
    #                 .adjust(1, repeat=True)
    #                 .as_markup()
    #             )
    #             text="🔄 Тимер успешно обновлен, у вас осталось: {m}:{s}м.".format(m=int(m),s=int(s))
    #         if timer.end_time>time.time():
    #             await bot2.edit_message_text(chat_id=timer.user_chat_id,text=text, reply_markup=day_function_markup, message_id=timer.message_id)
    #         else:
    #             timer.status = 0
    #             await timer.save()
    #             day_function_markup = (
    #                 InlineKeyboardBuilder()
    #                 .button(text="✅ Реквизит выдан", callback_data=TimerActionCallbackData(action='done', timer_id=timer.id).pack())
    #                 .button(text="🚫 Реквизит не выдан", callback_data=TimerActionCallbackData(action='cancel', timer_id=timer.id).pack())
    #                 .adjust(1, repeat=True)
    #                 .as_markup()
    #             )
    #             text="Время выдачи реквизита вышло, выберете действие:"
    #             await bot2.edit_message_text(chat_id=timer.user_chat_id,text=text, reply_markup=day_function_markup, message_id=timer.message_id)
    