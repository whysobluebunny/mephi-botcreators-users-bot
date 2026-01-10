from datetime import datetime
from unittest.mock import AsyncMock

import pytest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, User, Chat, Document


@pytest.fixture
def memory_storage():
    """Фикстура для MemoryStorage."""
    return MemoryStorage()


@pytest.fixture
def fsm_context(memory_storage):
    """Фикстура для FSMContext."""
    from aiogram import Bot
    bot = Bot(token="123:ABC")
    return FSMContext(
        storage=memory_storage,
        key=StorageKey(bot_id=bot.id, user_id=123, chat_id=123)
    )


@pytest.fixture
def user():
    """Фикстура для пользователя."""
    return User(
        id=123,
        is_bot=False,
        first_name="Test",
        username="testuser"
    )


@pytest.fixture
def chat():
    """Фикстура для чата."""
    return Chat(id=123, type="private")


@pytest.fixture
def message(user, chat):
    """Базовая фикстура для сообщения."""
    msg = Message(
        message_id=1,
        date=datetime.now(),
        chat=chat,
        from_user=user
    )
    object.__setattr__(msg, 'answer', AsyncMock())
    return msg


@pytest.fixture
def document_json():
    """Фикстура для документа JSON."""
    return Document(
        file_id="test_file_id_json",
        file_unique_id="test_unique_id_json",
        file_name="export.json",
        file_size=1024 * 1024,  # 1 MB
    )


@pytest.fixture
def document_html():
    """Фикстура для документа HTML."""
    return Document(
        file_id="test_file_id_html",
        file_unique_id="test_unique_id_html",
        file_name="export.html",
        file_size=2 * 1024 * 1024,  # 2 MB
    )


@pytest.fixture
def document_zip():
    """Фикстура для документа ZIP."""
    return Document(
        file_id="test_file_id_zip",
        file_unique_id="test_unique_id_zip",
        file_name="export.zip",
        file_size=5 * 1024 * 1024,  # 5 MB
    )


@pytest.fixture
def document_large():
    """Фикстура для большого документа."""
    return Document(
        file_id="test_file_id_large",
        file_unique_id="test_unique_id_large",
        file_name="export.json",
        file_size=101 * 1024 * 1024,  # 101 MB (превышает лимит)
    )


@pytest.fixture
def document_invalid_extension():
    """Фикстура для документа с неподдерживаемым расширением."""
    return Document(
        file_id="test_file_id_invalid",
        file_unique_id="test_unique_id_invalid",
        file_name="export.txt",
        file_size=1024,  # 1 KB
    )


@pytest.fixture
def message_with_document(message, document_json):
    """Сообщение с документом."""
    object.__setattr__(message, 'document', document_json)
    return message
