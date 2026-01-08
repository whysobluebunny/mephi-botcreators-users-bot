import pytest
from unittest.mock import AsyncMock, MagicMock
from aiogram.types import Message, Document
from aiogram.fsm.context import FSMContext

from bot.handlers.files import handle_document, cmd_reset, MAX_FILE_SIZE, ALLOWED_EXTENSIONS
from bot.states import UploadState


class TestHandleDocument:
    """Тесты для обработчика документов."""

    @pytest.mark.asyncio
    async def test_handle_document_success_json(self, message_with_document, fsm_context):
        """Тест успешной обработки JSON файла."""
        # Вызываем обработчик
        await handle_document(message_with_document, fsm_context)

        # Проверяем, что состояние установлено
        state = await fsm_context.get_state()
        assert state == UploadState.waiting_files

        # Проверяем, что файл сохранен в состоянии
        data = await fsm_context.get_data()
        assert "files" in data
        assert len(data["files"]) == 1
        assert data["files"][0]["file_id"] == "test_file_id_json"
        assert data["files"][0]["file_name"] == "export.json"
        assert data["files"][0]["file_extension"] == ".json"

        # Проверяем, что отправлен ответ
        message_with_document.answer.assert_called_once()
        call_args = message_with_document.answer.call_args[0][0]
        assert "✅ Файл принят" in call_args
        assert "1 файл(ов)" in call_args

    @pytest.mark.asyncio
    async def test_handle_document_success_html(self, message, document_html, fsm_context):
        """Тест успешной обработки HTML файла."""
        object.__setattr__(message, 'document', document_html)
        object.__setattr__(message, 'answer', AsyncMock())

        await handle_document(message, fsm_context)

        data = await fsm_context.get_data()
        assert len(data["files"]) == 1
        assert data["files"][0]["file_extension"] == ".html"
        assert data["files"][0]["file_name"] == "export.html"

    @pytest.mark.asyncio
    async def test_handle_document_success_zip(self, message, document_zip, fsm_context):
        """Тест успешной обработки ZIP файла."""
        object.__setattr__(message, 'document', document_zip)
        object.__setattr__(message, 'answer', AsyncMock())

        await handle_document(message, fsm_context)

        data = await fsm_context.get_data()
        assert len(data["files"]) == 1
        assert data["files"][0]["file_extension"] == ".zip"
        assert data["files"][0]["file_name"] == "export.zip"

    @pytest.mark.asyncio
    async def test_handle_document_multiple_files(self, message, document_json, document_html, fsm_context):
        """Тест обработки нескольких файлов подряд."""
        # Первый файл
        object.__setattr__(message, 'document', document_json)
        object.__setattr__(message, 'answer', AsyncMock())
        await handle_document(message, fsm_context)

        # Второй файл
        object.__setattr__(message, 'document', document_html)
        object.__setattr__(message, 'answer', AsyncMock())
        await handle_document(message, fsm_context)

        # Проверяем, что оба файла сохранены
        data = await fsm_context.get_data()
        assert len(data["files"]) == 2
        assert data["files"][0]["file_extension"] == ".json"
        assert data["files"][1]["file_extension"] == ".html"

        # Проверяем, что во втором ответе указано 2 файла
        call_args = message.answer.call_args[0][0]
        assert "2 файл(ов)" in call_args

    @pytest.mark.asyncio
    async def test_handle_document_file_too_large(self, message, document_large, fsm_context):
        """Тест отклонения файла из-за превышения размера."""
        object.__setattr__(message, 'document', document_large)
        object.__setattr__(message, 'answer', AsyncMock())

        await handle_document(message, fsm_context)

        # Проверяем, что файл не сохранен
        data = await fsm_context.get_data()
        files = data.get("files", [])
        assert len(files) == 0

        # Проверяем сообщение об ошибке
        message.answer.assert_called_once()
        call_args = message.answer.call_args[0][0]
        assert "❌ Файл слишком большой" in call_args
        assert f"{MAX_FILE_SIZE / (1024 * 1024):.0f} MB" in call_args

    @pytest.mark.asyncio
    async def test_handle_document_invalid_extension(self, message, document_invalid_extension, fsm_context):
        """Тест отклонения файла с неподдерживаемым расширением."""
        object.__setattr__(message, 'document', document_invalid_extension)
        object.__setattr__(message, 'answer', AsyncMock())

        await handle_document(message, fsm_context)

        # Проверяем, что файл не сохранен
        data = await fsm_context.get_data()
        files = data.get("files", [])
        assert len(files) == 0

        # Проверяем сообщение об ошибке
        message.answer.assert_called_once()
        call_args = message.answer.call_args[0][0]
        assert "❌ Неподдерживаемый формат файла" in call_args
        # Проверяем, что в сообщении указаны разрешенные расширения
        for ext in ALLOWED_EXTENSIONS:
            assert ext in call_args

    @pytest.mark.asyncio
    async def test_handle_document_case_insensitive_extension(self, message, fsm_context):
        """Тест обработки файла с расширением в верхнем регистре."""
        document = Document(
            file_id="test_file_id",
            file_unique_id="test_unique_id",
            file_name="export.JSON",  # Верхний регистр
            file_size=1024,
        )
        object.__setattr__(message, 'document', document)
        object.__setattr__(message, 'answer', AsyncMock())

        await handle_document(message, fsm_context)

        data = await fsm_context.get_data()
        assert len(data["files"]) == 1
        assert data["files"][0]["file_extension"] == ".json"

    @pytest.mark.asyncio
    async def test_handle_document_no_file_size(self, message, fsm_context):
        """Тест обработки файла без указания размера."""
        document = Document(
            file_id="test_file_id",
            file_unique_id="test_unique_id",
            file_name="export.json",
            file_size=None,  # Размер не указан
        )
        object.__setattr__(message, 'document', document)
        object.__setattr__(message, 'answer', AsyncMock())

        await handle_document(message, fsm_context)

        # Файл должен быть принят, так как проверка размера пропускается при None
        data = await fsm_context.get_data()
        assert len(data["files"]) == 1

    @pytest.mark.asyncio
    async def test_handle_document_no_file_name(self, message, fsm_context):
        """Тест обработки файла без имени."""
        document = Document(
            file_id="test_file_id",
            file_unique_id="test_unique_id",
            file_name=None,  # Имя не указано
            file_size=1024,
        )
        object.__setattr__(message, 'document', document)
        object.__setattr__(message, 'answer', AsyncMock())

        await handle_document(message, fsm_context)

        # Файл должен быть отклонен из-за отсутствия расширения
        data = await fsm_context.get_data()
        files = data.get("files", [])
        assert len(files) == 0

        message.answer.assert_called_once()
        call_args = message.answer.call_args[0][0]
        assert "❌ Неподдерживаемый формат файла" in call_args

    @pytest.mark.asyncio
    async def test_handle_document_state_preserved(self, message, document_json, fsm_context):
        """Тест сохранения состояния при обработке нескольких файлов."""
        # Устанавливаем состояние заранее
        await fsm_context.set_state(UploadState.waiting_files)
        await fsm_context.update_data(files=[])

        object.__setattr__(message, 'document', document_json)
        object.__setattr__(message, 'answer', AsyncMock())
        await handle_document(message, fsm_context)

        # Проверяем, что состояние сохранилось
        state = await fsm_context.get_state()
        assert state == UploadState.waiting_files

        data = await fsm_context.get_data()
        assert len(data["files"]) == 1


class TestCmdReset:
    """Тесты для команды /reset."""

    @pytest.mark.asyncio
    async def test_cmd_reset_clears_state(self, message, fsm_context):
        """Тест очистки состояния командой /reset."""
        # Устанавливаем состояние и данные
        await fsm_context.set_state(UploadState.waiting_files)
        await fsm_context.update_data(files=[{"file_id": "test"}])

        object.__setattr__(message, 'answer', AsyncMock())

        # Вызываем команду
        await cmd_reset(message, fsm_context)

        # Проверяем, что состояние очищено
        state = await fsm_context.get_state()
        assert state is None

        # Проверяем, что данные очищены
        data = await fsm_context.get_data()
        assert not data or "files" not in data

        # Проверяем ответ
        message.answer.assert_called_once()
        call_args = message.answer.call_args[0][0]
        assert "🔄 Очередь файлов очищена" in call_args

    @pytest.mark.asyncio
    async def test_cmd_reset_empty_state(self, message, fsm_context):
        """Тест /reset при пустом состоянии."""
        object.__setattr__(message, 'answer', AsyncMock())

        await cmd_reset(message, fsm_context)

        # Команда не должна падать
        message.answer.assert_called_once()
        call_args = message.answer.call_args[0][0]
        assert "🔄 Очередь файлов очищена" in call_args

    @pytest.mark.asyncio
    async def test_cmd_reset_with_multiple_files(self, message, fsm_context):
        """Тест /reset с несколькими файлами в очереди."""
        # Добавляем несколько файлов
        await fsm_context.set_state(UploadState.waiting_files)
        await fsm_context.update_data(files=[
            {"file_id": "file1"},
            {"file_id": "file2"},
            {"file_id": "file3"},
        ])

        object.__setattr__(message, 'answer', AsyncMock())

        await cmd_reset(message, fsm_context)

        # Проверяем, что все очищено
        state = await fsm_context.get_state()
        assert state is None

        data = await fsm_context.get_data()
        assert not data or "files" not in data

