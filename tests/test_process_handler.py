from unittest.mock import AsyncMock, MagicMock, patch, ANY

import pytest
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, Chat
from aiogram.types.user import User

from bot.handlers.process import process_files
from bot.models.export_result import ExportParseResult


@pytest.fixture
def message():
    msg = AsyncMock(spec=Message)
    msg.from_user = MagicMock(spec=User)
    msg.from_user.id = 12345
    msg.chat = MagicMock(spec=Chat)
    msg.chat.id = 67890
    return msg


@pytest.fixture
def fsm_context():
    context = AsyncMock(spec=FSMContext)
    context.get_data.return_value = {"files": [{"file_id": "test_id", "file_name": "test.json"}]}
    context.clear = AsyncMock()
    return context


@pytest.mark.asyncio
async def test_process_files_no_files(message, fsm_context):
    fsm_context.get_data.return_value = {}

    await process_files(message, fsm_context)

    message.answer.assert_called_with("⚠️ Нет файлов для обработки. Загрузите их сначала (отправьте JSON файлы).")


@pytest.mark.asyncio
async def test_process_files_text_response(message, fsm_context):
    """Тест: < 50 пользователей, отправляем текст."""
    with patch("bot.handlers.process.download_files") as mock_download, \
            patch("bot.handlers.process.Aggregator") as MockAggregator, \
            patch("bot.handlers.process.tempfile.TemporaryDirectory") as mock_temp_dir:

        # Mock temp dir
        mock_temp_dir.return_value.__enter__.return_value = "/tmp/test"

        # Mock download
        mock_download.return_value = ["/tmp/test/test.json"]

        # Mock Aggregator
        agg_instance = MockAggregator.return_value
        agg_instance.parse_exports.return_value = ExportParseResult(mentioned_usernames=["user1", "user2"],
                                                                    chat_names=[])

        await process_files(message, fsm_context)

        # Проверяем последовательность
        mock_download.assert_called_once_with(ANY, ANY, ANY, user_id=12345)
        agg_instance.parse_exports.assert_called_once()

        # Проверяем ответ
        # Проверяем, что есть вызов с результатом
        found_result = False
        for call in message.answer.call_args_list:
            if call[0] and "📌 Найдено 2 @username" in call[0][0]:
                found_result = True
                assert "@user1" in call[0][0]
                assert "@user2" in call[0][0]
                break
        assert found_result

        # State очищен
        fsm_context.clear.assert_called_once()


@pytest.mark.asyncio
async def test_process_files_excel_response(message, fsm_context):
    """Тест: >= 50 пользователей, отправляем Excel."""
    users = [f"user{i}" for i in range(60)]

    with patch("bot.handlers.process.download_files") as mock_download, \
            patch("bot.handlers.process.Aggregator") as MockAggregator, \
            patch("bot.handlers.process.ExcelExporter") as MockExporter, \
            patch("bot.handlers.process.FSInputFile") as MockInputFile, \
            patch("bot.handlers.process.tempfile.TemporaryDirectory") as mock_temp_dir:
        mock_temp_dir.return_value.__enter__.return_value = "/tmp/test"
        mock_download.return_value = ["/tmp/test/test.json"]

        agg_instance = MockAggregator.return_value
        agg_instance.parse_exports.return_value = ExportParseResult(mentioned_usernames=users, chat_names=[])

        await process_files(message, fsm_context)

        # Проверяем ExcelExporter
        MockExporter.assert_called_once()
        exporter_instance = MockExporter.return_value
        exporter_instance.build_excel.assert_called_once()

        # Проверяем отправку документа
        message.answer_document.assert_called_once()
        fsm_context.clear.assert_called_once()
