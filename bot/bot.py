from aiogram.fsm.storage.memory import MemoryStorage

from .models.config.bot_config import BotConfig
from .models.phrases.bot_phrases import BotPhrases
from .utils.bot import Bot
from .utils.dispatcher import Dispatcher
from apscheduler.schedulers.background import BackgroundScheduler

bot = Bot(BotConfig.load_first(), BotPhrases.load_first(), parse_mode="HTML")
dispatcher = Dispatcher(storage=MemoryStorage())
scheduler = BackgroundScheduler()