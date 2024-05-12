from aiogram import types
from aiogram.filters.command import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile

from .. import markups
from ..bot import bot
from ..filters.registered import RegisteredFilter
from ..services.database.models import BotUser
from ..utils.router import Router
from . import root_handlers_router

router = Router()
router.filter(RegisteredFilter(registered=False))
root_handlers_router.include_router(router)


@router.message(CommandStart())
async def start_handler(message: types.Message, state: FSMContext, bot_user: BotUser):
    if message.chat.type == 'private':
        await state.clear()
        text = "Добро пожаловать <b>" + message.from_user.first_name + "</b>!\n\nВыберите действия 👇" 
        await message.answer( text, reply_markup=markups.main_menu_markup )