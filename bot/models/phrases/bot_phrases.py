from typing import Dict, List
from pydantic import Field

from ...enums import Gender, HeightParams
from ..config_model import ConfigModel
from .ru import Ru, En


class BotPhrases(ConfigModel):
    __filenames__ = ("phrases.json",)

    ru: Ru = Field(Ru())  # type: ignore
    en: En = Field(En())
    