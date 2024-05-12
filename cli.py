import os
import sys
from pathlib import Path

import typer

from bot import ENCODING
from bot.models.config.bot_config import BotConfig
from bot.models.phrases.bot_phrases import BotPhrases
from bot.utils.paths import routers_path

app = typer.Typer()


@app.command()
def dev():
    for config_filepath in BotConfig.__filepaths__():
        create_json_file(config_filepath)
        BotConfig.refresh(config_filepath)


@app.command()
def update():
    for config_filepath in BotConfig.__exist_filepaths__():
        BotConfig.update(config_filepath)

    for phrases_filepath in BotPhrases.__exist_filepaths__():
        BotPhrases.update(phrases_filepath)


@app.command()
def refresh():
    for config_filepath in BotConfig.__exist_filepaths__():
        if config_filepath.name.startswith("_"):
            continue

        BotConfig.refresh(config_filepath)

    for phrases_filepath in BotPhrases.__exist_filepaths__():
        BotPhrases.refresh(phrases_filepath)

    os.system(f"{sys.executable} -m pip freeze > requirements.txt")


@app.command()
def router(name: str, file: bool = False, jump: bool = False):
    FILE_ROUTER_CODE = """from aiogram import F, types
from aiogram.fsm.context import FSMContext

from .. import markups
from ..bot import bot
from ..services.database.models import BotUser
from ..utils.router import Router
from . import root_handlers_router

router = Router()
root_handlers_router.include_router(router)
"""

    DIR_ROUTER_CODE = """from ...utils.router import Router
from .. import root_handlers_router

router = Router()
root_handlers_router.include_router(router)
"""

    if file:
        router_filepath = routers_path / f"{name}.py"
        router_filepath.write_text(FILE_ROUTER_CODE, encoding=ENCODING)
        typer.echo(f"Created router in {router_filepath}")

        if jump:
            jump_to_file(router_filepath)

        return

    router_dirpath = routers_path / name
    init_filepath = router_dirpath / "__init__.py"
    router_dirpath.mkdir(exist_ok=True)
    init_filepath.write_text(DIR_ROUTER_CODE, encoding=ENCODING)
    typer.echo(f"Created router in {init_filepath}")

    if jump:
        jump_to_file(init_filepath)


@app.command()
def handler(router: str, name: str, jump: bool = False):
    HANDLER_CODE = """from aiogram import F, types
from aiogram.fsm.context import FSMContext

from ... import markups
from ...bot import bot
from ...services.database.models import BotUser
from . import router
"""

    router_dirpath = routers_path / router

    if not router_dirpath.exists():
        return typer.echo(f"Router {router} does not exist")

    handler_filepath = router_dirpath / f"{name}.py"

    if handler_filepath.exists():
        typer.echo(f"Handler {handler_filepath} is already created")
    else:
        handler_filepath.write_text(HANDLER_CODE, encoding=ENCODING)
        typer.echo(f"Handler {handler_filepath} has been created")

    if jump:
        jump_to_file(handler_filepath)


def jump_to_file(path: Path):
    os.system(f"code {path.absolute()}")


def create_json_file(filepath: Path) -> bool:
    if filepath.exists():
        return False

    filepath.write_text(r"{}", encoding="utf")
    return True


def create_handler(handlers_dirpath: Path, handler_name: str):
    HANDLER_CODE = """from aiogram import types

from ..bot import dispatcher, bot
"""

    handler_path = handlers_dirpath / f"{handler_name.lower()}.py"
    handler_path.write_text(HANDLER_CODE, ENCODING)
    return handler_path


if __name__ == "__main__":
    app()
