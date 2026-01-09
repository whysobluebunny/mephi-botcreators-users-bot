from pydantic import BaseModel
from typing import Set


class ExportParseResult(BaseModel):
    # @username из текста сообщений (@testuser, @john_doe и т.д.)
    mentioned_usernames: Set[str] = set()
    # Проверенные @username (существуют в Telegram)
    verified_usernames: Set[str] = set()
    # Имена из полей 'from', 'forwarded_from' и т.д. (Иван, Лев, Artyom и т.д.)
    chat_names: Set[str] = set()


class FinalResult(BaseModel):
    usernames: list[str]
    names: list[str]
