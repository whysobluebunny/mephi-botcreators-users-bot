import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from bot.models.export_result import ExportParseResult
from bot.services.parser.telegram_json_parser import TelegramJsonParser


# Мультизамена: mentioned_usernames -> usernames, проверка names


@pytest.fixture
def sample_telegram_export():
    """Пример JSON-экспорта Telegram."""
    return {
        "name": "Test Chat",
        "type": "private_supergroup",
        "id": 123456789,
        "messages": [
            {
                "id": 1,
                "type": "message",
                "date": "2024-01-01T12:00:00",
                "from": "Test User",
                "from_id": "user123456789",
                "text": "Hey @testuser, check this out!"
            },
            {
                "id": 2,
                "type": "message",
                "date": "2024-01-01T12:05:00",
                "from": "Test User",
                "from_id": "user123456789",
                "text": [
                    "Message with multiple mentions: ",
                    "@username1 ",
                    "@username2"
                ]
            },
            {
                "id": 3,
                "type": "message",
                "date": "2024-01-01T12:10:00",
                "from": "Test User",
                "from_id": "user123456789",
                "text": "Invalid mentions @test, @u and valid @valid_user"
            },
            {
                "id": 4,
                "type": "message",
                "date": "2024-01-01T12:15:00",
                "from": "Test User",
                "from_id": "user123456789",
                "text": ""
            },
            {
                "id": 5,
                "type": "message",
                "date": "2024-01-01T12:20:00",
                "from": "Test User",
                "from_id": "user123456789"
            },
            {
                "id": 6,
                "type": "message",
                "date": "2024-01-01T12:25:00",
                "from": "Test User",
                "from_id": "user123456789",
                "text": [
                    {"type": "link", "text": "@another_user"},
                    " and ",
                    {"type": "plain", "text": "@yet_another"}
                ]
            }
        ]
    }


@pytest.fixture
def parser():
    """Парсер без проверки существования пользователей."""
    return TelegramJsonParser(bot=None)


@pytest.fixture
def parser_with_bot():
    """Парсер с мок-ботом для проверки существования пользователей."""
    bot = AsyncMock()
    return TelegramJsonParser(bot=bot)


def test_can_handle_json_file():
    """Тест: парсер должен обрабатывать .json файлы."""
    parser = TelegramJsonParser()
    assert parser.can_handle(Path("export.json")) is True
    assert parser.can_handle(Path("data.JSON")) is True
    assert parser.can_handle(Path("export.html")) is False
    assert parser.can_handle(Path("export.zip")) is False


def test_parse_simple_message(parser, sample_telegram_export):
    """Тест: парсер должен извлекать @username из простых сообщений."""
    with tempfile.TemporaryDirectory() as tmpdir:
        json_path = Path(tmpdir) / "export.json"
        with json_path.open("w", encoding="utf-8") as f:
            json.dump(sample_telegram_export, f)

        result = parser.parse(json_path)

        assert isinstance(result, ExportParseResult)
        assert "testuser" in result.mentioned_usernames
        assert "valid_user" in result.mentioned_usernames


def test_parse_array_messages(parser, sample_telegram_export):
    """Тест: парсер должен извлекать @username из массивов текста."""
    with tempfile.TemporaryDirectory() as tmpdir:
        json_path = Path(tmpdir) / "export.json"
        with json_path.open("w", encoding="utf-8") as f:
            json.dump(sample_telegram_export, f)

        result = parser.parse(json_path)

        assert "username1" in result.mentioned_usernames
        assert "username2" in result.mentioned_usernames


def test_parse_complex_objects(parser, sample_telegram_export):
    """Тест: парсер должен извлекать @username из сложных структур."""
    with tempfile.TemporaryDirectory() as tmpdir:
        json_path = Path(tmpdir) / "export.json"
        with json_path.open("w", encoding="utf-8") as f:
            json.dump(sample_telegram_export, f)

        result = parser.parse(json_path)

        assert "another_user" in result.mentioned_usernames
        assert "yet_another" in result.mentioned_usernames


def test_parse_skips_empty_messages(parser, sample_telegram_export):
    """Тест: парсер должен пропускать пустые сообщения без ошибок."""
    with tempfile.TemporaryDirectory() as tmpdir:
        json_path = Path(tmpdir) / "export.json"
        with json_path.open("w", encoding="utf-8") as f:
            json.dump(sample_telegram_export, f)

        result = parser.parse(json_path)

        # Не должно быть исключений
        assert isinstance(result, ExportParseResult)


def test_parse_invalid_usernames(parser, sample_telegram_export):
    """Тест: парсер должен игнорировать коротких @username."""
    with tempfile.TemporaryDirectory() as tmpdir:
        json_path = Path(tmpdir) / "export.json"
        with json_path.open("w", encoding="utf-8") as f:
            json.dump(sample_telegram_export, f)

        result = parser.parse(json_path)

        # Короткие имена (@test, @u) не должны быть включены
        assert "test" not in result.mentioned_usernames
        assert "u" not in result.mentioned_usernames


def test_parse_lowercase_normalization(parser, sample_telegram_export):
    """Тест: парсер должен нормализовать usernames в lowercase."""
    export = {
        "name": "Test",
        "messages": [
            {
                "id": 1,
                "type": "message",
                "date": "2024-01-01T12:00:00",
                "text": "@TestUser @ANOTHER_User"
            }
        ]
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        json_path = Path(tmpdir) / "export.json"
        with json_path.open("w", encoding="utf-8") as f:
            json.dump(export, f)

        result = parser.parse(json_path)

        assert "testuser" in result.mentioned_usernames
        assert "another_user" in result.mentioned_usernames
        # Исходные версии не должны быть добавлены отдельно
        assert "TestUser" not in result.mentioned_usernames


def test_parse_invalid_json(parser):
    """Тест: парсер должен обрабатывать невалидный JSON без падения."""
    with tempfile.TemporaryDirectory() as tmpdir:
        json_path = Path(tmpdir) / "invalid.json"
        with json_path.open("w", encoding="utf-8") as f:
            f.write("{ invalid json")

        result = parser.parse(json_path)

        assert isinstance(result, ExportParseResult)
        assert len(result.mentioned_usernames) == 0


def test_parse_missing_messages_field(parser):
    """Тест: парсер должен обрабатывать JSON без поля 'messages'."""
    export = {"name": "Test Chat", "type": "private"}

    with tempfile.TemporaryDirectory() as tmpdir:
        json_path = Path(tmpdir) / "export.json"
        with json_path.open("w", encoding="utf-8") as f:
            json.dump(export, f)

        result = parser.parse(json_path)

        assert isinstance(result, ExportParseResult)
        assert len(result.mentioned_usernames) == 0


def test_parse_messages_not_list(parser):
    """Тест: парсер должен обрабатывать случай, когда 'messages' не список."""
    export = {"name": "Test Chat", "messages": "not a list"}

    with tempfile.TemporaryDirectory() as tmpdir:
        json_path = Path(tmpdir) / "export.json"
        with json_path.open("w", encoding="utf-8") as f:
            json.dump(export, f)

        result = parser.parse(json_path)

        assert isinstance(result, ExportParseResult)
        assert len(result.mentioned_usernames) == 0


def test_parse_file_not_found(parser):
    """Тест: парсер должен обрабатывать отсутствующий файл."""
    non_existent = Path("/tmp/non_existent_file_12345.json")

    result = parser.parse(non_existent)

    assert isinstance(result, ExportParseResult)
    assert len(result.mentioned_usernames) == 0


def test_parser_without_bot_copies_to_verified(parser, sample_telegram_export):
    """Тест: без бота verified_usernames = usernames."""
    with tempfile.TemporaryDirectory() as tmpdir:
        json_path = Path(tmpdir) / "export.json"
        with json_path.open("w", encoding="utf-8") as f:
            json.dump(sample_telegram_export, f)

        result = parser.parse(json_path)

        assert result.verified_usernames == result.mentioned_usernames
        assert len(result.verified_usernames) > 0


def test_parser_with_bot_verifies_users():
    """Тест: с ботом проверяются существующие пользователи."""
    export = {
        "name": "Test",
        "messages": [
            {
                "id": 1,
                "type": "message",
                "date": "2024-01-01T12:00:00",
                "text": "@testuser @other_user"
            }
        ]
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        json_path = Path(tmpdir) / "export.json"
        with json_path.open("w", encoding="utf-8") as f:
            json.dump(export, f)

        # Создаем мок-бот
        bot = AsyncMock()

        # Мок: @testuser существует, @other_user нет
        async def mock_get_chat(username):
            if username == "@testuser":
                return MagicMock()
            raise Exception(f"User {username} not found")

        bot.get_chat = mock_get_chat

        parser = TelegramJsonParser(bot=bot)
        result = parser.parse(json_path)

        # Проверяем, что найдены оба пользователя в usernames
        assert "testuser" in result.mentioned_usernames
        assert "other_user" in result.mentioned_usernames


def test_multiple_mentions_same_user(parser, sample_telegram_export):
    """Тест: одно и то же имя несколько раз должно быть в результате один раз."""
    export = {
        "name": "Test",
        "messages": [
            {
                "id": 1,
                "type": "message",
                "date": "2024-01-01T12:00:00",
                "text": "@testuser @testuser @testuser"
            }
        ]
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        json_path = Path(tmpdir) / "export.json"
        with json_path.open("w", encoding="utf-8") as f:
            json.dump(export, f)

        result = parser.parse(json_path)

        assert result.mentioned_usernames == {"testuser"}
        assert len(result.mentioned_usernames) == 1


def test_parse_mixed_content(parser):
    """Тест: парсер должен работать со смешанным контентом."""
    export = {
        "name": "Test",
        "messages": [
            {
                "id": 1,
                "type": "message",
                "date": "2024-01-01T12:00:00",
                "text": "Text with @user1 and link to @user2. Not a mention: user3@example.com"
            },
            {
                "id": 2,
                "type": "message",
                "date": "2024-01-01T12:05:00",
                "text": ["@user3 mentioned in ", "array"]
            },
            {
                "id": 3,
                "type": "message",
                "date": "2024-01-01T12:10:00",
                "text": [
                    {"text": "@user4 in object"},
                    " and @user5"
                ]
            }
        ]
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        json_path = Path(tmpdir) / "export.json"
        with json_path.open("w", encoding="utf-8") as f:
            json.dump(export, f)

        result = parser.parse(json_path)

        assert "user1" in result.mentioned_usernames
        assert "user2" in result.mentioned_usernames
        assert "user3" in result.mentioned_usernames
        assert "user4" in result.mentioned_usernames
        assert "user5" in result.mentioned_usernames
        # Должно быть 5 пользователей, user3@example.com не считается
        assert len(result.mentioned_usernames) == 5


def test_extract_names_from_from_field(parser):
    """Тест: парсер должен извлекать имена из поля 'from' в names."""
    export = {
        "name": "Test",
        "messages": [
            {
                "id": 1,
                "type": "message",
                "date": "2024-01-01T12:00:00",
                "from": "Лев",
                "text": "Hello"
            },
            {
                "id": 2,
                "type": "message",
                "date": "2024-01-01T12:05:00",
                "from": "Artyom",
                "text": "Hi there"
            }
        ]
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        json_path = Path(tmpdir) / "export.json"
        with json_path.open("w", encoding="utf-8") as f:
            json.dump(export, f)

        result = parser.parse(json_path)

        assert "Лев" in result.chat_names
        assert "Artyom" in result.chat_names


def test_skip_user_ids_from_from_field(parser):
    """Тест: парсер должен пропускать ID типа 'user710927765'."""
    export = {
        "name": "Test",
        "messages": [
            {
                "id": 1,
                "type": "message",
                "date": "2024-01-01T12:00:00",
                "from": "user710927765",  # ID, а не username
                "text": "Some text"
            },
            {
                "id": 2,
                "type": "message",
                "date": "2024-01-01T12:05:00",
                "from": "Den",  # Реальное имя
                "text": "Another message"
            }
        ]
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        json_path = Path(tmpdir) / "export.json"
        with json_path.open("w", encoding="utf-8") as f:
            json.dump(export, f)

        result = parser.parse(json_path)

        # user710927765 НЕ должно быть добавлено в names
        assert "user710927765" not in result.chat_names
        # Den должно быть добавлено
        assert "Den" in result.chat_names


def test_extract_forwarded_from(parser):
    """Тест: парсер должен извлекать имена из поля 'forwarded_from' в names."""
    export = {
        "name": "Test",
        "messages": [
            {
                "id": 1,
                "type": "message",
                "date": "2024-01-01T12:00:00",
                "from": "Alice",
                "forwarded_from": "Bob",
                "text": "Forwarded message"
            }
        ]
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        json_path = Path(tmpdir) / "export.json"
        with json_path.open("w", encoding="utf-8") as f:
            json.dump(export, f)

        result = parser.parse(json_path)

        assert "Alice" in result.chat_names
        assert "Bob" in result.chat_names


def test_mentions_and_names_combined(parser):
    """Тест: парсер должен извлекать как @mentions в usernames, так и имена в names."""
    export = {
        "name": "Test",
        "messages": [
            {
                "id": 1,
                "type": "message",
                "date": "2024-01-01T12:00:00",
                "from": "Иван",
                "text": "@testuser привет @another_user"
            }
        ]
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        json_path = Path(tmpdir) / "export.json"
        with json_path.open("w", encoding="utf-8") as f:
            json.dump(export, f)

        result = parser.parse(json_path)

        # Имя должно быть в names
        assert "Иван" in result.chat_names
        # @mentions должны быть в usernames
        assert "testuser" in result.mentioned_usernames
        assert "another_user" in result.mentioned_usernames
        # В names не должны быть mentions
        assert "testuser" not in result.chat_names
        assert len(result.chat_names) == 1
        assert len(result.mentioned_usernames) == 2
