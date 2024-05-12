from tortoise import fields
from tortoise.models import Model
from ...enums import UserRole, ChatRole, CloverBountyType, OrderStatus, GameStatus, TaskQueueType, ChatDepositNotify, NotifyType

class BotUser(Model):
    id = fields.IntField(pk=True, unique=True)  # telegram user id
    username = fields.TextField(null=True, default="")
    first_name = fields.TextField(null=True, default="")
    last_name = fields.TextField(null=True, default="")
    role = fields.IntEnumField(UserRole)
    company_name = fields.TextField(null=True, default="")
    clover_limit = fields.IntField(default='0')
    function_day = fields.BooleanField(default=False)
    function_rek = fields.BooleanField(default=False)
    created_date = fields.DatetimeField(auto_now_add=True)
    class Meta:
        table = "bot_user"

class UserChat(Model):
    id = fields.IntField(pk=True, unique=True)  # telegram user id
    bot_user: fields.ForeignKeyRelation[BotUser] = fields.ForeignKeyField(
        "models.BotUser", related_name="chat_user"
    )
    name = fields.TextField(null=True, default="")
    comment = fields.TextField(null=True, default="")
    limit = fields.IntField(default='10000000')
    notify_limit = fields.IntField(default='10000000')
    commission = fields.FloatField(default='0')
    secured_id = fields.IntField(null=True)
    rates = fields.FloatField(default='0')
    step_rates = fields.IntField(default='0')
    is_closed = fields.BooleanField(default=True)
    started_date = fields.DatetimeField(null=True)
    created_date = fields.DatetimeField(auto_now_add=True)
    type = fields.IntEnumField(ChatRole)
    notify_deposit = fields.IntEnumField(ChatDepositNotify, default=ChatDepositNotify.disabled)
    clover: fields.OneToOneRelation["Clover"]
    class Meta:
        table = "user_chat"

class SupportUserChat(Model):
    id = fields.IntField(pk=True, unique=True) 
    other_bot_user: fields.ForeignKeyRelation[BotUser] = fields.ForeignKeyField(
        "models.BotUser", related_name="support_other_bot_user"
    )
    bot_user: fields.ForeignKeyRelation[BotUser] = fields.ForeignKeyField(
        "models.BotUser", related_name="support_bot_user"
    )
    username = fields.TextField(null=True, default="")
    class Meta:
        table = "support_user_chat"

class UserPeople(Model):
    bot_user: fields.ForeignKeyRelation[BotUser] = fields.ForeignKeyField(
        "models.BotUser", related_name="user_people_bot_user"
    )
    other_bot_user: fields.ForeignKeyRelation[BotUser] = fields.ForeignKeyField(
        "models.BotUser", related_name="user_people_other_bot_user"
    )
    class Meta:
        table = "user_people"

class UserChatAdvertising(Model):
    bot_user: fields.ForeignKeyRelation[BotUser] = fields.ForeignKeyField(
        "models.BotUser", related_name="chat_advertising_user"
    )
    text = fields.TextField()
    user_chat_type = fields.IntEnumField(ChatRole)
    class Meta:
        table = "user_chat_advertising"

class ProfitUserChat(Model):
    bot_user: fields.ForeignKeyRelation[BotUser] = fields.ForeignKeyField(
        "models.BotUser", related_name="profit_chat_bot_user"
    )
    user_chat: fields.ForeignKeyRelation[UserChat] = fields.ForeignKeyField(
        "models.UserChat", related_name="profit_user_chat"
    )
    created_date = fields.DatetimeField(auto_now_add=True)
    commission = fields.FloatField(default='0')
    class Meta:
        table = "profit_user_chat"

class ProfitUser(Model):
    id = fields.IntField(pk=True, unique=True) 
    uuid = fields.CharField(unique=True, max_length=8) 
    bot_user: fields.ForeignKeyRelation[BotUser] = fields.ForeignKeyField(
        "models.BotUser", related_name="profit_bot_user"
    )
    last_action = fields.DatetimeField(auto_now_add=True)
    class Meta:
        table = "profit_user"
    
class CloverBounty(Model):
    id = fields.IntField(pk=True, unique=True)
    type = fields.IntEnumField(CloverBountyType)
    data = fields.TextField(null=True, default="")
    clover_count = fields.IntField(default=0)
    created_date = fields.DatetimeField(auto_now_add=True)
    bot_user: fields.ForeignKeyRelation[BotUser] = fields.ForeignKeyField(
        "models.BotUser", related_name="clover_bounty_bot_user"
    )
    class Meta:
        table = "clover_bounty"

class Clover(Model):
    id = fields.IntField(pk=True, unique=True)
    user_chat: fields.ForeignKeyRelation[UserChat] = fields.ForeignKeyField(
        "models.UserChat", related_name="clover_user_chat"
    )
    count = fields.IntField(default=0)
    created_date = fields.DatetimeField(auto_now_add=True)

class TaskQueue(Model):
    id = fields.IntField(pk=True, unique=True)
    user_chat: fields.ForeignKeyRelation[UserChat] = fields.ForeignKeyField(
        "models.UserChat", related_name="task_queue_user_chat"
    )
    data = fields.TextField(default="")
    type = fields.CharEnumField(TaskQueueType)
    status = fields.SmallIntField(default=1)
    class Meta:
            table = "task_queue"

class TimerMessage(Model):
    id = fields.IntField(pk=True, unique=True)
    user_chat: fields.ForeignKeyRelation[UserChat] = fields.ForeignKeyField(
        "models.UserChat", related_name="timer_user_chat"
    )
    message_id = fields.IntField(default=0)
    start_time = fields.FloatField()
    end_time = fields.FloatField()
    steep = fields.IntField(default=1)
    status = fields.IntField(default=1)
    class Meta:
        table = "timer_message"

    

class Order(Model):
    id = fields.IntField(pk=True, unique=True)
    bot_user: fields.ForeignKeyRelation[BotUser] = fields.ForeignKeyField(
        "models.BotUser", related_name="order_bot_user"
    )
    other_bot_user: fields.ForeignKeyRelation[BotUser] = fields.ForeignKeyField(
        "models.BotUser", related_name="order_other_bot_user"
    )
    user_chat: fields.ForeignKeyRelation[UserChat] = fields.ForeignKeyField(
        "models.UserChat", related_name="order_user_chat"
    )
    other_user_chat: fields.ForeignKeyRelation[UserChat] = fields.ForeignKeyField(
        "models.UserChat", related_name="order_other_user_chat"
    )
    delivery_id = fields.IntField(default=0)
    name = fields.TextField(null=True, default="")
    bank = fields.TextField(null=True, default="")
    card_number = fields.TextField(null=True, default="")
    support_name = fields.TextField(null=True, default="")
    amount = fields.FloatField()
    profit_amount = fields.FloatField(default=0)
    other_profit_amount = fields.FloatField(default=0)
    rates = fields.FloatField(default='0')
    other_rates = fields.FloatField(default='0')
    step_rates = fields.IntField(default='0')
    is_static = fields.BooleanField(default=False)
    fine = fields.FloatField(default=0)
    other_fine = fields.FloatField(default=0)
    status = fields.CharEnumField(OrderStatus)
    created_date = fields.DatetimeField(auto_now_add=True)

class OrderFine(Model):
    id = fields.IntField(pk=True, unique=True)
    user_chat: fields.ForeignKeyRelation[UserChat] = fields.ForeignKeyField(
        "models.UserChat", related_name="order_fine_user_chat"
    )
    fine = fields.FloatField(default=0)
    class Meta:
        table = "order_fine"

class OrderStatic(Model):
    user_chat: fields.ForeignKeyRelation[UserChat] = fields.ForeignKeyField(
        "models.UserChat", related_name="order_static_user_chat"
    )
    bank = fields.TextField(null=True, default="")
    name = fields.TextField(null=True, default="")
    commission = fields.FloatField()
    class Meta:
        table = "order_static"

class Delivery(Model):
    id = fields.IntField(pk=True, unique=True)
    bot_user: fields.ForeignKeyRelation[BotUser] = fields.ForeignKeyField(
        "models.BotUser", related_name="delivery_bot_user"
    )
    fio = fields.TextField(null=True, default="")
    bank_name = fields.TextField(null=True, default="")
    limit = fields.IntField()
    other_information = fields.TextField(null=True, default="")
    class Meta:
        table = "delivery"


class Game(Model):
    id = fields.IntField(pk=True, unique=True)
    bot_user: fields.ForeignKeyRelation[BotUser] = fields.ForeignKeyField(
        "models.BotUser", related_name="game_bot_user"
    )
    user_chat: fields.ForeignKeyRelation[UserChat] = fields.ForeignKeyField(
        "models.UserChat", related_name="game_user_chat"
    )
    username = fields.TextField(null=True, default="")
    steep = fields.TextField(null=True, default="")
    score = fields.IntField(default=0)
    other_score = fields.IntField(default=0)
    clover_count = fields.IntField()
    created_date = fields.DatetimeField(auto_now_add=True)
    status = fields.IntEnumField(GameStatus)

class GameAction(Model):
    id = fields.IntField(pk=True, unique=True)
    game: fields.ForeignKeyRelation[Game] = fields.ForeignKeyField(
        "models.Game", related_name="game"
    )
    game_type = fields.CharField(max_length=8)
    bot_user: fields.ForeignKeyRelation[BotUser] = fields.ForeignKeyField(
        "models.BotUser", related_name="game_action_bot_user"
    )
    score = fields.IntField(default=0)
    other_score = fields.IntField(default=0)
    move: fields.ForeignKeyRelation[BotUser] = fields.ForeignKeyField(
        "models.BotUser", related_name="game_action_move_bot_user"
    )
    raund = fields.IntField(default=0)


class Notify(Model):
    id = fields.IntField(pk=True, unique=True)
    user_chat: fields.ForeignKeyRelation[UserChat] = fields.ForeignKeyField(
        "models.UserChat", related_name="notify_user_chat"
    )
    type = fields.CharEnumField(NotifyType)
    notify_count = fields.IntField(default=0)
    created_date = fields.DatetimeField(auto_now_add=True)
    notify_date = fields.DatetimeField(auto_now_add=True)


