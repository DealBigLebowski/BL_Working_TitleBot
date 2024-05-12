from aiogram import F, types
from aiogram.filters.command import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.filters import IS_NOT_MEMBER, IS_MEMBER, ChatMemberUpdatedFilter, IS_ADMIN
from aiogram.types import CallbackQuery
from tortoise.contrib.sqlite.functions import Random


from .. import markups
from ..bot import bot
from ..services.database.models import BotUser, UserChat, Clover, Game, GameAction, CloverBounty
from ..enums import GameStatus
from ..utils.router import Router
from . import root_handlers_router
from ..state import Action
from ..callback_data import  GameActionCallbackData

router = Router()
root_handlers_router.include_router(router)

@router.message(F.chat.type != "private", F.text == '/game')
async def status_info_handler(message: types.Message, bot_user: BotUser):
    user_chat = await UserChat.filter(id=message.chat.id).prefetch_related("bot_user").first()    
    clover = await Clover.filter(user_chat=user_chat).first()
    if clover:
        if clover.count != 0:
            game = await Game.filter(user_chat=user_chat, status=GameStatus.active).first()
            if game is None:
                await Game.create(
                    user_chat=user_chat,
                    bot_user=bot_user,
                    steep="wait_clover",
                    clover_count=0,
                    status=GameStatus.active
                )
                text = "У тебя есть <b>{clover.count}</b> 🎟 для игры. Можешь начать с 1 🎟 или отложить и сыграть позже за <b>3</b> 🎟, чтобы выиграть более ценные призы 🎁\n\nПомни, в этой игре важно не только смело начинать, но и стратегически использовать свои 🎟 🤘\n\nУдача сопутствует смелым! \n\n💡Выбери количество билетов , у тебя доступно <b>{clover.count}</b> 🎟️".format(clover=clover)
                await message.answer(text=text, reply_markup=markups.game_clover_markup)
            else:
                text = "Бро. В этом чате уже имеется активная игра, пожалуста отмени его и попробуйте еще раз"
                await message.answer(text=text, reply_markup=markups.game_cancel_markup)

@router.callback_query(GameActionCallbackData.filter(F.action == 'cancel'))
async def set_rates_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    user_chat = await UserChat.filter(id=callback.message.chat.id).prefetch_related("bot_user").first()
    game = await Game.filter(user_chat=user_chat, status=GameStatus.active).first()
    if game:
        if game.bot_user_id == bot_user.id:
            await game.delete()
            await callback.message.edit_text("✅ Игра успешно удалена")
        else:
            await callback.answer("❗️ У вас нету доступа к этой функции игры", True)
    else:
        await callback.message.edit_text("🔍 Игра не найдена!")

@router.callback_query(GameActionCallbackData.filter(F.action == 'set_username'))
async def set_rates_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    user_chat = await UserChat.filter(id=callback.message.chat.id).prefetch_related("bot_user").first()
    game = await Game.filter(user_chat=user_chat, bot_user=bot_user, status=GameStatus.active).first()
    if game:
        clover = await Clover.filter(user_chat=user_chat).first()
        if clover.count >= int(callback_data.data):
            await state.set_state(Action.wait_game_username)  
            game.clover_count = int(callback_data.data)
            game.steep = "wait_username"
            await game.save()
            text = "💡 Банковский Спарринг:\nШаг 1. Определите имя вашего оппонента из, с кем будешь соревноваться в получении бонуса. В формате: @userTakoyTo\n\n<i>Напоминаем, что в этой игре иногда важно не только побеждать, но и находить уроки в поражениях. 🌐✌️</i>"
            await callback.message.edit_text(text=text, reply_markup=markups.game_cancel_markup)
        else:
            await callback.answer("❗️ Недостаточно билетов, выбери другое значение", True)

@router.message(Action.wait_game_username, F.text)
async def wait_set_rates_handler(message: types.Message, state: FSMContext, bot_user: BotUser):
    user_chat = await UserChat.filter(id=message.chat.id).first()
    game = await Game.filter(user_chat=user_chat, bot_user=bot_user, status=GameStatus.active).first()
    if game:
        await state.clear()
        username = message.text.replace("@", "")
        text = "Шаг2. Выбери одну из игр ниже для розыгрыша:"
        game_type_markup = (
            InlineKeyboardBuilder()
            .button(text="🎲 Кости", callback_data=GameActionCallbackData(game_id=0, action='game', data='🎲', other_data=username).pack())
            .button(text="🎳 Боулинг", callback_data=GameActionCallbackData(game_id=0,action='game', data='🎳', other_data=username).pack())
            .button(text="🏀 Баскетбол", callback_data=GameActionCallbackData(game_id=0, action='game', data='🏀', other_data=username).pack())
            .button(text="Отменить", callback_data=GameActionCallbackData(game_id=0, action='cancel', data='', other_data='').pack())
            .adjust(1, repeat=True)
            .as_markup()
        )
        await message.answer(text=text, reply_markup=game_type_markup)
    else:
        await state.clear()

@router.callback_query(GameActionCallbackData.filter(F.action == 'game'))
async def set_rates_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    user_chat = await UserChat.filter(id=callback.message.chat.id).first()
    game = await Game.filter(user_chat=user_chat, bot_user=bot_user, status=GameStatus.active).first()
    if game:
        if callback_data.data == '🎲':
            text = "Ты выбрал игру 🎲 Кости. Правила: игра до трех побед.\nПобеждает игрок, набравший три раза наибольшее число очков, выбросая кости"
        elif callback_data.data == '🎳':
            text = "Ты выбрал игру 🎳 Боулинг. Правила: игра до трех побед.\nПобеждает игрок, набравший три раза наибольшее число очков, сбив наибольшее количество кедлей"
        elif callback_data.data == '🏀':
            text = "Ты выбрал игру 🏀 Баскетбол. Правила: игра до трех побед.\nПобеждает игрок, набравший три раза наибольшее число очков."
        
        other_bot_user = await BotUser.filter(username=callback_data.other_data).first()
        if other_bot_user is None:
            other_bot_user = bot_user
        await GameAction.create(
            game=game,
            game_type=callback_data.data,
            bot_user=bot_user,
            move=other_bot_user
        )   
        start_game_markup = (
            InlineKeyboardBuilder()
            .button(text="♠️ Начать игру", callback_data=GameActionCallbackData(game_id=game.id, action='start_game', data=callback_data.data, other_data=callback_data.other_data).pack())
            .button(text="Отменить", callback_data=GameActionCallbackData(game_id=0, action='cancel', data='', other_data='').pack())
            .adjust(1, repeat=True)
            .as_markup()
        )
        text += "\n\n<i>❕ Ожидаем подтверждение игрока @{callback_data.other_data}</i>".format(callback_data=callback_data)
        await callback.message.edit_text(text=text,reply_markup=start_game_markup)

@router.callback_query(GameActionCallbackData.filter(F.action == 'start_game'))
async def set_rates_handler(callback: CallbackQuery, callback_data: dict, state: FSMContext, bot_user: BotUser):
    if bot_user.username == callback_data.other_data:
        user_chat = await UserChat.filter(id=callback.message.chat.id).first()
        game = await Game.filter(user_chat=user_chat, status=GameStatus.active).prefetch_related("bot_user").first()
        if game:
            game_action = await GameAction.filter(game=game).first()
            if callback_data.data == '🎲':
                game_type = "🎲 Кости."
            elif callback_data.data == '🎳':
                game_type = "🎳 Боулинг."
            elif callback_data.data == '🏀':
                game_type = "🏀 Баскетбол."
            await callback.message.delete()
            game.steep = 'start_game'
            await game.save()
            game_action.bot_user = bot_user
            await game_action.save()
            text = "♠️ Игра началась\n\n🕹 Тип игры: {game_type}\n👤 Игрок @{game.bot_user.username} - 0\n👤 Игрок @{game_action.bot_user.username} - 0\n\n<i>❕ Отправьте эмоджи</i> {game_action.game_type}".format(
                game=game,
                game_action=game_action,
                game_type=game_type,
            )
            await callback.message.answer(text=text)
            text = "Ходит @{game_action.bot_user.username}".format(game_action=game_action)
            await callback.message.answer(text=text)


@router.message(F.dice)
async def wait_set_rates_handler(message: types.Message, state: FSMContext, bot_user: BotUser):
    user_chat = await UserChat.filter(id=message.chat.id).prefetch_related("bot_user").first()
    game = await Game.filter(user_chat=user_chat, steep='start_game', status=GameStatus.active).prefetch_related("bot_user").first()
    if game:
        end_game = False
        game_action = await GameAction.filter(game=game, move=bot_user).prefetch_related("move", "bot_user").first()
        if game_action:
            if game_action.game_type == message.dice.emoji:
                dice_value = message.dice.value
                if game_action.game_type == '🏀':
                    if dice_value <= 3:
                        dice_value = 1
                    else:
                        dice_value = 2
            if game_action.move == game_action.bot_user:
                game_action.move = game.bot_user
                game_action.score = dice_value
            else:
                game_action.move = game_action.bot_user
                game_action.other_score = dice_value
            
            await game_action.save()

            if game_action.raund == 2:
                win_username = ""
                if game_action.score == game_action.other_score:
                    await message.answer("Ничья")
                elif game_action.score > game_action.other_score:
                    game.other_score = game.other_score + 1
                    win_username = game_action.bot_user.username
                    looser = game.bot_user.username
                else:
                    game.score = game.score + 1
                    win_username = game.bot_user.username
                    looser = game_action.bot_user.username
                await game.save()
                if win_username:
                    if game.score == 3:
                        win_bot_user = game.bot_user
                        end_game = True
                    elif game.other_score == 3:
                        win_bot_user = game_action.bot_user
                        end_game = True
                    else:
                        text = "💥 Выиграл @{win_username}\n\n🕹 Тип игры: {game_action.game_type}\n👤 Игрок @{game.bot_user.username} - {game.score}\n👤 Игрок @{game_action.bot_user.username} - {game.other_score}\n🎟️ Использовано билетов {game.clover_count}".format(
                            game=game,
                            game_action=game_action,
                            win_username=win_username
                        )
                        await message.answer(text=text)
                    if end_game:
                        text = "💥 Выиграл @{win_username}\n\n🕹 Тип игры: {game_action.game_type}\n👤 Игрок @{game.bot_user.username} - {game.score}\n👤 Игрок @{game_action.bot_user.username} - {game.other_score}\n🎟️ Использовано билетов {game.clover_count}".format(
                            game=game,
                            game_action=game_action,
                            win_username=win_username
                        )
                        await message.answer(text=text)
                        await message.answer("Пользователь @{win_username} выиграл!".format(win_username=win_username))
                        clover = await Clover.filter(user_chat=user_chat).first()
                        clover.count = clover.count - game.clover_count
                        await clover.save()
                        clover_bounty = await CloverBounty.filter(bot_user=user_chat.bot_user, clover_count=game.clover_count).annotate(random=Random()).order_by("random").first()
                        if clover_bounty:
                            await message.answer(clover_bounty.data)
                        else:
                            await message.answer("🥹 Ты выиграл игру, но к сожалению призов больше не осталось")
                        
                        game.status = GameStatus.inactive
                        await game.save()
                game_action.score = 0
                game_action.other_score = 0
                game_action.raund = 1
                await game_action.save()
            else:
                game_action.raund = 2
                await game_action.save()
            if not end_game:
                await message.answer("Ходит @{game_action.move.username}".format(game_action=game_action))


            
                
