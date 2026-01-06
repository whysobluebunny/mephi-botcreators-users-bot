import logging

from aiogram import Router
from aiogram.types import Message
from aiogram.filters import CommandStart, Command

router = Router()
log = logging.getLogger(__name__)


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    log.info(
        "cmd=/start user_id=%s chat_id=%s username=%s",
        message.from_user.id if message.from_user else None,
        message.chat.id if message.chat else None,
        message.from_user.username if message.from_user else None,
    )
    text = (
        "Привет! 👋\n\n"
        "Я бот для анализа экспортов чатов Telegram.\n\n"
        "Что я делаю:\n"
        "• Принимаю **только файлы экспорта чатов** из Telegram Desktop.\n"
        "• Извлекаю **только те @username, которые встречаются в экспорте** "
        "(например, как упоминания в сообщениях).\n"
        "• Я **не запрашиваю** у Telegram дополнительные данные о пользователях и "
        "не могу по message_id или user_id узнать скрытый username.\n\n"
        "Дальше команда /help объяснит, как подготовить экспорт и отправить его боту."
    )
    await message.answer(text)


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    log.info(
        "cmd=/help user_id=%s chat_id=%s",
        message.from_user.id if message.from_user else None,
        message.chat.id if message.chat else None,
    )
    text = (
        "Как пользоваться ботом:\n\n"
        "1️⃣ Открой Telegram Desktop и экспортируй историю нужного чата.\n"
        "   • Настройки → Advanced → Export Telegram data\n"
        "   • Или через меню чата: 'Export chat history'\n"
        "   • Рекомендуется формат JSON, можно без медиа, чтобы файл был меньше.\n\n"
        "2️⃣ Отправь полученный файл экспорта **как документ** в диалог со мной.\n"
        "   Позже мы добавим возможность отправлять несколько файлов подряд.\n\n"
        "3️⃣ После разработки следующих частей бот сможет обработать экспорт, "
        "извлечь все встречающиеся в нём @username и выдать результат списком "
        "или Excel-файлом (в зависимости от количества).\n\n"
        "Важно про ограничения:\n"
        "• Я работаю только с тем, что содержится в файлах экспорта.\n"
        "• Если username нигде не фигурирует (ни в полях экспорта, ни в @упоминаниях), "
        "я не смогу его узнать.\n"
        "• Я не делаю дополнительных запросов к Telegram API для получения полных "
        "списков участников и не различаю приватные/публичные группы по их внутренним "
        "параметрам — только по данным экспорта."
    )
    await message.answer(text)
