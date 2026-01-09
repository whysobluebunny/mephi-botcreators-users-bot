from pathlib import Path
import json
import re
import logging
import asyncio
from typing import Any

from aiogram import Bot
from .base import ChatExportParser
from ...models.export_result import ExportParseResult


# Regex для @username: должен быть в начале слова или после пробела
MENTION_RE = re.compile(r"(?:^|[\s\(])@([a-zA-Z0-9_]{5,})")

# Regex для исключения @user<числа> (ID вместо username)
USER_ID_RE = re.compile(r"^user\d{7,}$")

log = logging.getLogger(__name__)


class TelegramJsonParser(ChatExportParser):
    """
    Парсер JSON-экспорта Telegram Desktop.
    Извлекает @username из текста сообщений и проверяет их существование.
    """

    def __init__(self, bot: Bot | None = None):
        """
        :param bot: Объект Bot для проверки существования пользователей.
                   Если None, проверка не будет выполняться.
        """
        self.bot = bot

    def can_handle(self, path: Path) -> bool:
        return path.suffix.lower() == ".json"

    def parse(self, path: Path) -> ExportParseResult:
        result = ExportParseResult()

        try:
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            log.error("Failed to parse JSON file %s: %s", path, e)
            return result
        except Exception as e:
            log.error("Unexpected error reading file %s: %s", path, e)
            return result

        # Проходим по сообщениям
        messages = data.get("messages", [])
        if not isinstance(messages, list):
            log.warning("Expected 'messages' to be a list, got %s", type(messages))
            return result

        for msg in messages:
            if not isinstance(msg, dict):
                continue

            # Извлекаем текст сообщения
            text = self._extract_text_from_message(msg)
            if text:
                # Ищем все @username в тексте
                mentions = MENTION_RE.findall(text)
                for mention in mentions:
                    # Исключаем @user<числа> (ID вместо username)
                    if not USER_ID_RE.match(mention.lower()):
                        # Сохраняем в lowercase для единообразия
                        result.usernames.add(mention.lower())
            
            # Извлекаем имена из полей "from", "forwarded_from" и т.д.
            self._extract_names_from_message(msg, result)

        log.info(
            "Parsed %d messages from %s, found %d unique usernames",
            len(messages),
            path.name,
            len(result.usernames),
        )

        # Если есть бот, проверяем существование пользователей
        if self.bot:
            try:
                # Пытаемся получить текущий event loop
                loop = asyncio.get_running_loop()
                # Если мы здесь, значит loop уже работает (например, в async контексте)
                # Не можем использовать asyncio.run(), нужно использовать create_task
                log.warning("Cannot verify usernames - already in async context")
            except RuntimeError:
                # Нет работающего loop, используем asyncio.run()
                asyncio.run(self._verify_usernames(result))
        else:
            # Если нет бота, копируем все найденные usernames в verified
            result.verified_usernames = result.usernames.copy()
            log.debug("No bot instance provided, verified_usernames = usernames")

        return result

    async def _verify_usernames(self, result: ExportParseResult) -> None:
        """
        Проверяет существование пользователей через Telegram API.
        """
        for username in result.usernames:
            try:
                # Пытаемся получить информацию о пользователе
                user = await self.bot.get_chat(f"@{username}")
                result.verified_usernames.add(username)
                log.debug(f"User @{username} verified")
            except Exception as e:
                log.debug(f"User @{username} not found or not accessible: {e}")
                continue

        log.info(
            "Verified %d out of %d usernames",
            len(result.verified_usernames),
            len(result.usernames),
        )

    def _extract_text_from_message(self, msg: dict[str, Any]) -> str:
        """
        Извлекает текст из сообщения.
        Текст может быть:
        - строкой в поле "text"
        - массивом строк
        - массивом объектов с полем "text"
        """
        text_field = msg.get("text")
        if not text_field:
            return ""

        # Если текст - простая строка
        if isinstance(text_field, str):
            return text_field

        # Если текст - массив
        if isinstance(text_field, list):
            text_parts = []
            for item in text_field:
                if isinstance(item, str):
                    text_parts.append(item)
                elif isinstance(item, dict):
                    # Может быть объект с полем "text" или просто строка в значении
                    item_text = item.get("text") or item.get("value")
                    if isinstance(item_text, str):
                        text_parts.append(item_text)
            return "".join(text_parts)

        # Если это другой тип, пытаемся преобразовать в строку
        if text_field:
            return str(text_field)

        return ""

    def _extract_names_from_message(self, msg: dict[str, Any], result: ExportParseResult) -> None:
        """
        Извлекает имена пользователей из различных полей сообщения.
        Ищет в полях: 'from', 'forwarded_from', 'actor', и т.д.
        
        Примеры:
        - "from": "Лев" → добавляется "Лев"
        - "from": "user710927765" → пропускается (это ID)
        - "forwarded_from": "Artyom" → добавляется "Artyom"
        """
        # Поля, в которых могут быть имена пользователей
        name_fields = ['from', 'forwarded_from', 'actor']
        
        for field in name_fields:
            name = msg.get(field)
            if isinstance(name, str) and name.strip():
                # Пропускаем если это ID типа "user710927765"
                if USER_ID_RE.match(name):
                    log.debug(f"Пропущен ID из поля '{field}': {name}")
                    continue
                
                # Добавляем имя в отдельный список
                result.names.add(name)
                log.debug(f"Извлечено имя из поля '{field}': {name}")
