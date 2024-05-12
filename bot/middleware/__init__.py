from ..utils.dispatcher import Dispatcher
from .bot_user import BotUserMiddleware
from .services_di import ServicesDIMiddleware


def setup(dispatcher: Dispatcher):
    bot_user_middleware = BotUserMiddleware()
    dispatcher.message.outer_middleware.register(bot_user_middleware)
    dispatcher.callback_query.outer_middleware.register(bot_user_middleware)

    services_di_middleware = ServicesDIMiddleware(dispatcher)
    dispatcher.message.middleware.register(services_di_middleware)
    dispatcher.callback_query.middleware.register(services_di_middleware)
