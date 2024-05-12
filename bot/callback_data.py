from enum import IntEnum

from aiogram.filters.callback_data import CallbackData


class AnswerCallbackData(CallbackData, prefix="answer"):
    action: str

class UserChatCallbackData(CallbackData, prefix="answer"):
    id: int
    action: str
    data: str

class UserChatPaginationCallbackData(CallbackData, prefix="answer"):
    id: int
    action: str
    data: str
    page: int

class UserPeopleCallbackData(CallbackData, prefix="answer"):
    id: int
    other_id: int
    action: str

class SupportUserChatCallbackData(CallbackData, prefix="answer"):
    id: int
    other_user: int
    action: str

class CloverBountyCallbackData(CallbackData, prefix="answer"):
    id: int
    action: str

class DeliveryCallbackData(CallbackData, prefix="answer"):
    id: int
    action: str

class GameActionCallbackData(CallbackData, prefix="answer"):
    game_id: int
    action: str
    data: str
    other_data: str

class TimerActionCallbackData(CallbackData, prefix="answer"):
    action: str
    timer_id: int