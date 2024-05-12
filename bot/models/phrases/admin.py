from pydantic import BaseModel, Field


class AdminPhrases(BaseModel):
    admin: str = Field("Админка")
