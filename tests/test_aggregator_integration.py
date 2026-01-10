"""
Интеграционный тест для Aggregator с TelegramJsonParser
"""

import json
import tempfile
from pathlib import Path

from bot.services.aggregator import Aggregator


def test_aggregator_with_telegram_parser():
    """Тест: Aggregator работает с TelegramJsonParser по умолчанию."""

    # Создаем тестовый JSON-экспорт
    export_data = {
        "name": "Test Chat",
        "messages": [
            {"id": 1, "text": "Hello @testuser1"},
            {"id": 2, "text": "Hi @testuser2 and @testuser3"},
        ]
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        # Сохраняем файл
        json_file = Path(tmpdir) / "export.json"
        with json_file.open("w") as f:
            json.dump(export_data, f)

        # Инициализируем Aggregator без параметров
        aggregator = Aggregator()

        # Парсим файлы
        result = aggregator.parse_exports([json_file])

        # Проверяем результаты
        assert "testuser1" in result.mentioned_usernames
        assert "testuser2" in result.mentioned_usernames
        assert "testuser3" in result.mentioned_usernames
        assert len(result.mentioned_usernames) == 3

        print(f"✅ Найдено {len(result.mentioned_usernames)} пользователей: {result.mentioned_usernames}")


def test_aggregator_with_string_paths():
    """Тест: Aggregator работает со строками вместо Path."""

    export_data = {
        "name": "Test",
        "messages": [
            {"id": 1, "text": "@user_one @user_two"},
        ]
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        json_file = Path(tmpdir) / "export.json"
        with json_file.open("w") as f:
            json.dump(export_data, f)

        aggregator = Aggregator()

        # Передаем строку вместо Path
        result = aggregator.parse_exports([str(json_file)])

        assert "user_one" in result.mentioned_usernames
        assert "user_two" in result.mentioned_usernames

        print(f"✅ Aggregator корректно работает со строковыми путями")


if __name__ == "__main__":
    test_aggregator_with_telegram_parser()
    test_aggregator_with_string_paths()
    print("\n✨ Все интеграционные тесты пройдены!")
