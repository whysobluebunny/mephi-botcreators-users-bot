from typing import Set

from pydantic import BaseModel


class ExportParseResult(BaseModel):
    # @username из текста сообщений (@testuser, @john_doe и т.д.)
    mentioned_usernames: Set[str] = set()
    # Проверенные @username (существуют в Telegram, проверяются среди пользаков бота)
    verified_usernames: Set[str] = set()
    # Имена из полей 'from', 'forwarded_from' и т.д. (Иван, Лев, Artyom и т.д.)
    chat_names: Set[str] = set()