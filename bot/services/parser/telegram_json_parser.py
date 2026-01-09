from pathlib import Path
import json
import re
import logging
from typing import Any

from .base import ChatExportParser
from ...models.export_result import ExportParseResult


MENTION_RE = re.compile(r"@([a-zA-Z0-9_]{5,})")

log = logging.getLogger(__name__)


class TelegramJsonParser(ChatExportParser):
    """
    Парсер JSON-экспорта Telegram Desktop.
    Извлекает @username из текста сообщений.
    """

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
            if not text:
                continue

            # Ищем все @username в тексте
            mentions = MENTION_RE.findall(text)
            for mention in mentions:
                # Сохраняем в lowercase для единообразия
                result.mentioned_usernames.add(mention.lower())

        log.info(
            "Parsed %d messages from %s, found %d unique usernames",
            len(messages),
            path.name,
            len(result.mentioned_usernames),
        )

        return result

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
