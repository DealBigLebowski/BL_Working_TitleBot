from enum import IntEnum, StrEnum


class Gender(IntEnum):
    male = 0
    female = 1


class HeightParams(IntEnum):
    less_165 = 1
    less_170 = 2
    above_170 = 3
    less_180 = 4
    above_180 = 5
    other = 6

class UserRole(IntEnum):
    user = 1
    manager = 2
    admin = 3

class ChatRole(IntEnum):
    none = 0
    writer = 1
    cc = 2
    rek = 3

class ChatDepositNotify(IntEnum):
    disabled = 0
    active = 1

class NotifyType(StrEnum):
    deposit = "Deposit"


class CloverBountyType(IntEnum):
    text = 1
    file = 2

class OrderStatus(StrEnum):
    pending = "Pending"
    confirm = "Confirm"
    paid = "Paid"
    cancel = "Cancel"

class GameStatus(IntEnum):
    inactive = 0
    active = 1
    
class TaskQueueType(StrEnum):
    start_day = "StartDay"
    send_message = "SendMessage"