import asyncio
import json
import logging
import re
from pathlib import Path
from typing import Any

from aiogram import Bot

from .base import ChatExportParser
from ...models.export_result import ExportParseResult

# Regex для @username: должен быть в начале слова или после пробела
MENTION_RE = re.compile(r"(?:^|[\s\(])@([a-zA-Z0-9_]{5,})")
# Regex для исключения @user<числа> (ID вместо username)
USER_ID_RE = re.compile(r"^user\d{7,}$")
TME_RE = re.compile(r"(?:https?://)?t\.me/([a-zA-Z0-9_]{5,})")

log = logging.getLogger(__name__)


class TelegramJsonParser(ChatExportParser):
    def __init__(self, bot: Bot | None = None):
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

        messages = data.get("messages", [])
        if not isinstance(messages, list):
            log.warning("Expected 'messages' to be a list, got %s", type(messages))
            return result

        for msg in messages:
            if not isinstance(msg, dict):
                continue

            text = self._extract_text_from_message(msg)
            if text:
                for mention in MENTION_RE.findall(text):
                    # Исключаем @user<числа> (ID вместо username)
                    if not USER_ID_RE.match(mention.lower()):
                        result.mentioned_usernames.add(mention.lower())

                for ch in TME_RE.findall(text):
                    log.debug(f"Channel @{ch} extracted")
                    result.channels.add(ch.lower())
            self._extract_names_from_message(msg, result)

        log.info(
            "Parsed %d messages from %s, found %d unique usernames",
            len(messages),
            path.name,
            len(result.mentioned_usernames),
        )

        if self.bot:
            try:
                loop = asyncio.get_running_loop()
                log.warning("Cannot verify usernames - already in async context")
            except RuntimeError:
                asyncio.run(self._verify_usernames(result))
        else:
            result.verified_usernames = result.mentioned_usernames.copy()
            log.debug("No bot instance provided, verified_usernames = usernames")

        return result

    async def _verify_usernames(self, result: ExportParseResult) -> None:
        for username in result.mentioned_usernames:
            try:
                user = await self.bot.get_chat(f"@{username}")
                result.verified_usernames.add(username)
                log.debug(f"User @{username} verified")
            except Exception as e:
                log.debug(f"User @{username} not found or not accessible: {e}")
                continue

        log.info(
            "Verified %d out of %d usernames",
            len(result.verified_usernames),
            len(result.mentioned_usernames),
        )

    def _extract_text_from_message(self, msg: dict[str, Any]) -> str:
        text_field = msg.get("text")
        if not text_field:
            return ""

        if isinstance(text_field, str):
            return text_field

        if isinstance(text_field, list):
            text_parts = []
            for item in text_field:
                if isinstance(item, str):
                    text_parts.append(item)
                elif isinstance(item, dict):
                    item_text = item.get("text") or item.get("value")
                    if isinstance(item_text, str):
                        text_parts.append(item_text)
            return "".join(text_parts)

        if text_field:
            return str(text_field)

        return ""

    def _extract_names_from_message(self, msg: dict[str, Any], result: ExportParseResult) -> None:
        name_fields = ['from', 'forwarded_from', 'actor']
        for field in name_fields:
            name = msg.get(field)
            if isinstance(name, str) and name.strip():
                if USER_ID_RE.match(name):
                    log.debug(f"Skipped ID from field '{field}': {name}")
                    continue

                result.chat_names.add(name)
                log.debug(f"Extracted name from field '{field}': {name}")
