from typing import Optional

from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, KeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from .bot import bot
from .callback_data import AnswerCallbackData, UserChatCallbackData, GameActionCallbackData, CloverBountyCallbackData
from .services.database.models import BotUser
from .state import RegisterState
from .models.phrases.bot_phrases import BotPhrases

remove_markup = types.ReplyKeyboardRemove(remove_keyboard=True)

main_menu_markup = (
    InlineKeyboardBuilder()
    .add(InlineKeyboardButton(text="Начать рабочий день", callback_data=AnswerCallbackData(action='start_job').pack()))
    .add(InlineKeyboardButton(text="Рассылка по группам", callback_data=AnswerCallbackData(action='sletter_select_chat_type').pack()))
    .row(
        InlineKeyboardButton(text="Добавить в группу", callback_data=AnswerCallbackData(action='add_chat').pack()),
        InlineKeyboardButton(text="Реклама в закрепе", callback_data=AnswerCallbackData(action='advertising').pack()),
        InlineKeyboardButton(text="Статистика", callback_data=AnswerCallbackData(action='stats').pack()),
        InlineKeyboardButton(text="Проверить рек", callback_data=AnswerCallbackData(action='check_rek').pack()),
        InlineKeyboardButton(text="Поддежрка", callback_data=AnswerCallbackData(action='support').pack()),
        InlineKeyboardButton(text="Редакция групп", callback_data=AnswerCallbackData(action='edit_chat').pack()),
        InlineKeyboardButton(text="Уведомление", callback_data=AnswerCallbackData(action='notification').pack()),
        #InlineKeyboardButton(text="Крайняк", callback_data=AnswerCallbackData(action='other').pack()),
        InlineKeyboardButton(text="Резак копусты", callback_data=AnswerCallbackData(action='profit').pack()),
        InlineKeyboardButton(text="Настройки кабинета", callback_data=AnswerCallbackData(action='settings').pack()),
        InlineKeyboardButton(text="Интерактивы для клиентов", callback_data=AnswerCallbackData(action='interactives').pack()),
        InlineKeyboardButton(text="Автоматизация работы", callback_data=AnswerCallbackData(action='automation').pack()),
        width=2
    )
    .as_markup()
)

select_start_chat_type = (
    InlineKeyboardBuilder()
    .button(text="КЦ/Лейки", callback_data=UserChatCallbackData(action='select_start_chat_type', data='cc', id=0).pack())
    .button(text="Нальщики", callback_data=UserChatCallbackData(action='select_start_chat_type', data='writer', id=0).pack())
    .button(text="Назад", callback_data=AnswerCallbackData(action='main').pack())
    .adjust(1, repeat=True)
    .as_markup()
)


select_start_type = (
    InlineKeyboardBuilder()
    .button(text="Ввести текст рекламы", callback_data=AnswerCallbackData(action='write_text_and_start_job').pack())
    .button(text="Без рекламы", callback_data=AnswerCallbackData(action='only_start_job').pack())
    .button(text="Назад", callback_data=AnswerCallbackData(action='main').pack())
    .adjust(1, repeat=True)
    .as_markup()
)

game_clover_markup = (
    InlineKeyboardBuilder()
    .button(text="🎟️ 1", callback_data=GameActionCallbackData(game_id=0, action='set_username', data='1', other_data='').pack())
    .button(text="🎟️ 2", callback_data=GameActionCallbackData(game_id=0,action='set_username', data='2', other_data='').pack())
    .button(text="🎟️ 3", callback_data=GameActionCallbackData(game_id=0, action='set_username', data='3', other_data='').pack())
    .button(text="Отменить", callback_data=GameActionCallbackData(game_id=0, action='cancel', data='', other_data='').pack())
    .adjust(1, repeat=True)
    .as_markup()
)

bounty_clover_count = (
    InlineKeyboardBuilder()
    .button(text="🎟️ 1", callback_data=CloverBountyCallbackData(id=1, action='bounty_clover_count').pack())
    .button(text="🎟️ 2", callback_data=CloverBountyCallbackData(id=2,action='bounty_clover_count').pack())
    .button(text="🎟️ 3", callback_data=CloverBountyCallbackData(id=3, action='bounty_clover_count').pack())
    .button(text="Отменить", callback_data=AnswerCallbackData(action='main').pack())
    .adjust(1, repeat=True)
    .as_markup()
)

game_cancel_markup = (
    InlineKeyboardBuilder()
    .button(text="Отменить", callback_data=GameActionCallbackData(game_id=0, action='cancel', data='', other_data='').pack())
    .adjust(1, repeat=True)
    .as_markup()
)

support_markup = (
    InlineKeyboardBuilder()
    .button(text="О нас", callback_data=AnswerCallbackData(action='about').pack())
    .button(text="Тех. Поддержка", callback_data=AnswerCallbackData(action='support_contact').pack())
    .button(text="Часто задаваемые вопросы", callback_data=AnswerCallbackData(action='support_faq').pack())
    .button(text="Назад", callback_data=AnswerCallbackData(action='main').pack())
    .adjust(1, repeat=True)
    .as_markup()
)

settings_markup = (
    InlineKeyboardBuilder()
    .button(text="Название компании", callback_data=AnswerCallbackData(action='setting_set_company_name').pack())
    .button(text="Назначить саппорта", callback_data=AnswerCallbackData(action='setting_set_support').pack())
    .button(text="Получить статус", callback_data=AnswerCallbackData(action='setting_get_status').pack())
    .button(text="Подробнее", callback_data=AnswerCallbackData(action='setting_instruciton').pack())
    .button(text="Назад", callback_data=AnswerCallbackData(action='main').pack())
    .adjust(1, repeat=True)
    .as_markup()
)

interactives_markup = (
    InlineKeyboardBuilder()
    .button(text="Добавить призы", callback_data=AnswerCallbackData(action='interactives_add_clover_bounty').pack())
    .button(text="Условия Билета", callback_data=AnswerCallbackData(action='interactives_set_clover_amount').pack())
    .button(text="Выдать Билет", callback_data=AnswerCallbackData(action='interactives_issue_clover').pack())
    .button(text="Подробнее", callback_data=AnswerCallbackData(action='interactives_instruciton').pack())
    .button(text="Назад", callback_data=AnswerCallbackData(action='main').pack())
    .adjust(1, repeat=True)
    .as_markup()
)

automation_markup = (
    InlineKeyboardBuilder()
    .button(text="Добавить реквизит", callback_data=AnswerCallbackData(action='automation_add_rek').pack())
    .button(text="Функция «Рек»", callback_data=AnswerCallbackData(action='automation_function_rek').pack())
    .button(text="Функция «Дай»", callback_data=AnswerCallbackData(action='automation_function_day').pack())
    .button(text="Назад", callback_data=AnswerCallbackData(action='main').pack())
    .adjust(1, repeat=True)
    .as_markup()
)

automation_include_bot_markup = (
    InlineKeyboardBuilder()
    .button(text="Выбрать группу", callback_data=AnswerCallbackData(action='automation_select_add_rek').pack())
    .button(text="Назад", callback_data=AnswerCallbackData(action='automation').pack())
    .adjust(1, repeat=True)
    .as_markup()
)


# main_menu_markup = (
#     InlineKeyboardBuilder()
#     .add(start_joob_markup)
#     .row(
#         InlineKeyboardButton
#     )
#     .as_markup
                    
# )


add_chat_markup = (
    InlineKeyboardBuilder()
    .button(text="КЦ/Лейки", callback_data=UserChatCallbackData(action='select_action', data='cc', id=0).pack())
    .button(text="Нальщики", callback_data=UserChatCallbackData(action='select_action', data='writer', id=0).pack())
    .button(text="Назад", callback_data=AnswerCallbackData(action='main').pack())
    .adjust(1, repeat=True)
    .as_markup()
)

edit_chat_markup = (
    InlineKeyboardBuilder()
    .button(text="Группы  КЦ/Лейки", callback_data=UserChatCallbackData(action='edit_chat_select_action', data='cc', id=0).pack())
    .button(text="Группы нальщики", callback_data=UserChatCallbackData(action='edit_chat_select_action', data='writer', id=0).pack())
    .button(text="Назад", callback_data=AnswerCallbackData(action='main').pack())
    .adjust(1, repeat=True)
    .as_markup()
)

advertising_markup = (
    InlineKeyboardBuilder()
    .button(text="Ввести текст", callback_data=AnswerCallbackData(action='advertising_chat_type').pack())
    .button(text="Подробнее", callback_data=AnswerCallbackData(action='advertising_instruciton').pack())
    .button(text="Назад", callback_data=AnswerCallbackData(action='main').pack())
    .adjust(1, repeat=True)
    .as_markup()
)

advertising_chat_type_markup = (
    InlineKeyboardBuilder()
    .button(text="КЦ/Лейки", callback_data=UserChatCallbackData(action='enter_advertising_text', data='cc', id=0).pack())
    .button(text="Нальщики", callback_data=UserChatCallbackData(action='enter_advertising_text', data='writer', id=0).pack())
    .button(text="Назад", callback_data=AnswerCallbackData(action='advertising').pack())
    .adjust(1, repeat=True)
    .as_markup()
)

stats_select_chat_type = (
    InlineKeyboardBuilder()
    .button(text="КЦ/Лейки", callback_data=UserChatCallbackData(action='stats_select_chat_type', data='cc', id=0).pack())
    .button(text="Нальщики", callback_data=UserChatCallbackData(action='stats_select_chat_type', data='writer', id=0).pack())
    .button(text="Все типы", callback_data=UserChatCallbackData(action='stats_select_chat_type', data='all', id=0).pack())
    .button(text="Назад", callback_data=AnswerCallbackData(action='stats').pack())
    .adjust(1, repeat=True)
    .as_markup()
)


stats_markup = (
    InlineKeyboardBuilder()
    .button(text="Сформировать", callback_data=AnswerCallbackData(action='get_stats').pack())
    .button(text="Инструкция", callback_data=AnswerCallbackData(action='stats_instruciton').pack())
    .button(text="Назад", callback_data=AnswerCallbackData(action='main').pack())
    .adjust(1, repeat=True)
    .as_markup()
)

filter_stats_markup = (
    InlineKeyboardBuilder()
    .button(text="Выбранной дате", callback_data=AnswerCallbackData(action='get_stats_select_day').pack())
    .button(text="Выбранному промежутку дат", callback_data=AnswerCallbackData(action='get_stats_select_betwen').pack())
    .button(text="По саппортам", callback_data=AnswerCallbackData(action='get_stats_support').pack())
    .button(text="Назад", callback_data=AnswerCallbackData(action='stats').pack())
    .adjust(1, repeat=True)
    .as_markup()
)

user_chat_filter_stats_markup = (
    InlineKeyboardBuilder()
    .button(text="Выбранной дате", callback_data=AnswerCallbackData(action='get_stats_select_day').pack())
    .button(text="Выбранному промежутку дат", callback_data=AnswerCallbackData(action='get_stats_select_betwen').pack())
    .adjust(1, repeat=True)
    .as_markup()
)

notify_markup = (
    InlineKeyboardBuilder()
    .button(text="Выбрать из списка", callback_data=AnswerCallbackData(action='select_notification_chat').pack())
    .button(text="Подробнее", callback_data=AnswerCallbackData(action='notification_instruction').pack())
    .button(text="Назад", callback_data=AnswerCallbackData(action='main').pack())
    .adjust(1, repeat=True)
    .as_markup()
)

profit_markup = (
    InlineKeyboardBuilder()
    .button(text="Собрать урожай", callback_data=AnswerCallbackData(action='profit_collect').pack())
    .button(text="Добавить группу", callback_data=AnswerCallbackData(action='profit_add_chat').pack())
    .button(text="Статистика", callback_data=AnswerCallbackData(action='profit_stats').pack())
    .button(text="Установить комиссию", callback_data=AnswerCallbackData(action='profit_add_commission').pack())
    .button(text="Подробнее", callback_data=AnswerCallbackData(action='profit_instruction').pack())
    .button(text="Назад", callback_data=AnswerCallbackData(action='main').pack())
    .adjust(1, repeat=True)
    .as_markup()

)

other_markup = (
    InlineKeyboardBuilder()
    .button(text="Отправить запрос", callback_data=AnswerCallbackData(action='other_send_request').pack())
    .button(text="Доверенные люди", callback_data=AnswerCallbackData(action='other_people').pack())
    .button(text="Подробнее", callback_data=AnswerCallbackData(action='other_instruciton').pack())
    .button(text="Назад", callback_data=AnswerCallbackData(action='main').pack())
    .adjust(1, repeat=True)
    .as_markup()
)

check_rek_markup = (
    InlineKeyboardBuilder()
    .button(text="Ввести номер карты/счета", callback_data=AnswerCallbackData(action='enter_rek').pack())
    .button(text="Подробнее", callback_data=AnswerCallbackData(action='check_rek_instruciton').pack())
    .button(text="Назад", callback_data=AnswerCallbackData(action='main').pack())
    .adjust(1, repeat=True)
    .as_markup()
)

cancel_markup = (
    InlineKeyboardBuilder()
    .button(text="Отмена", callback_data=AnswerCallbackData(action='main').pack())
    .adjust(1, repeat=True)
    .as_markup()
)

back_markup = (
    InlineKeyboardBuilder()
    .button(text="Назад", callback_data=AnswerCallbackData(action='main').pack())
    .adjust(1, repeat=True)
    .as_markup()
)

skip_markup = (
    InlineKeyboardBuilder()
    .button(text="Скрыть", callback_data=AnswerCallbackData(action='skip_text').pack())
    .adjust(1, repeat=True)
    .as_markup()
)

set_rates_markup = (
    InlineKeyboardBuilder()
    .button(text="Установить курс на все заявки", callback_data=AnswerCallbackData(action='set_rates').pack())
    .button(text="Установить курс на определенные заявки", callback_data=AnswerCallbackData(action='scrap_set_rates').pack())
    .adjust(1, repeat=True)
    .as_markup()
)

other_set_rates_markup = (
    InlineKeyboardBuilder()
    .button(text="Установить курс на все заявки", callback_data=AnswerCallbackData(action='set_rates').pack())
    .button(text="Установить курс на определенные заявки", callback_data=AnswerCallbackData(action='scrap_set_rates').pack())
    .adjust(1, repeat=True)
    .as_markup()
)

cancel_set_rates_markup = (
    InlineKeyboardBuilder()
    .button(text="Отмена, продолжить день", callback_data=AnswerCallbackData(action='cancel_set_rates').pack())
    .adjust(1, repeat=True)
    .as_markup()
)

cancel_rek_markup = (
    InlineKeyboardBuilder()
    .button(text="Отменить", callback_data=AnswerCallbackData(action='cancel_rek').pack())
    .adjust(1, repeat=True)
    .as_markup()
)


# main_menu_markup = (
#     ReplyKeyboardBuilder()
#     .button(text="📂 Загрузить файл")
#     .as_markup(resize_keyboard=True)
# )

# cancel_markup = (
#     ReplyKeyboardBuilder()
#     .button(text="🚫 Отмена")
#     .as_markup(resize_keyboard=True)
# )

async def create_back_markup(data):
    return (
        InlineKeyboardBuilder()
        .button(text="Назад", callback_data=data)
        .adjust(1, repeat=True)
        .as_markup()
    )