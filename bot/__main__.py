import logging
from . import middleware, routers, services
from .bot import bot, dispatcher, scheduler
from .utils.paths import root_path, routers_path
from .routers.timer import interval_timer
from .services.database.models import BotUser
from aiogram.types import Message, Chat
from datetime import datetime
import asyncio
import aiohttp

def timer():
    message = Message(message_id=0, chat=Chat(id=0,type='group'), date=datetime.now())
    asyncio.run(interval_timer(message))
 

async def schedule_jobs():
    
    job = scheduler.add_job(timer, trigger="interval", seconds=5)

@dispatcher.startup()
async def on_startup():
    await services.setup(dispatcher)
    await schedule_jobs()
    me = await bot.get_me()
    print(bot.phrases.bot_started.format(me=me))

@dispatcher.shutdown()
async def on_shutdown():
    await services.dispose(dispatcher)
    scheduler.shutdown()
    session = aiohttp.ClientSession()
    await session.close()


def import_routers():
    for router_path in routers_path.glob("*"):
        if router_path.stem.startswith("__") and router_path.stem.endswith("__"):
            continue

        if router_path.is_file():
            __import__(f"bot.routers.{router_path.stem}")
            continue

        sorted_handler_file_paths = sorted(
            router_path.glob("*.*"), key=lambda p: p.stem
        )

        for handler_file_path in sorted_handler_file_paths:
            if not handler_file_path.is_file():
                continue

            __import__(f"bot.routers.{router_path.stem}.{handler_file_path.stem}")


def main():
    log_filename = str((root_path / "logs.log").resolve())

    logging.basicConfig(
        filename=log_filename,
        level=logging.ERROR,
        format=r"%(asctime)s %(levelname)s %(funcName)s(%(lineno)d) %(message)s",
    )

    middleware.setup(dispatcher)
    import_routers()
    dispatcher.include_router(routers.root_handlers_router)

    used_update_types = dispatcher.resolve_used_update_types()
    scheduler.start()
    dispatcher.run_polling(bot, allowed_updates=used_update_types)


main()
