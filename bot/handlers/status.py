from __future__ import annotations

import logging
import os

from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from ..version import APP_VERSION

router = Router()
log = logging.getLogger(__name__)


@router.message(Command("status"))
async def cmd_status(message: Message) -> None:
    log.info(
        "cmd=/status user_id=%s chat_id=%s",
        message.from_user.id if message.from_user else None,
        message.chat.id if message.chat else None,
    )
    env = os.getenv("ENV", "dev").lower()

    text = (
        "✅ Bot status\n\n"
        f"Версия: {APP_VERSION}\n"
        f"Режим: {env}\n\n"
        "Функциональность:\n"
        "• /start, /help — ✅\n"
        "• Приём файлов экспорта — ✅\n"
        "• Обработка экспортов и выгрузка результата — 🚧 (в разработке)"  # todo
    )
    await message.answer(text)
