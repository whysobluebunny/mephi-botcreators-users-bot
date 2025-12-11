from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from ..states import UploadState

router = Router()

# Захардкоженные настройки (позже можно вынести в конфиг)
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB
ALLOWED_EXTENSIONS = {".json", ".html", ".zip"}


@router.message(F.document)
async def handle_document(message: Message, state: FSMContext) -> None:
    """Обработчик документов."""
    # Устанавливаем состояние, если его еще нет
    current_state = await state.get_state()
    if current_state is None:
        await state.set_state(UploadState.waiting_files)

    document = message.document

    # Проверка размера файла
    if document.file_size and document.file_size > MAX_FILE_SIZE:
        await message.answer(
            f"❌ Файл слишком большой. Максимальный размер: {MAX_FILE_SIZE / (1024 * 1024):.0f} MB"
        )
        return

    # Проверка расширения файла
    file_name = document.file_name or ""
    file_extension = None
    for ext in ALLOWED_EXTENSIONS:
        if file_name.lower().endswith(ext):
            file_extension = ext
            break

    if not file_extension:
        allowed_str = ", ".join(ALLOWED_EXTENSIONS)
        await message.answer(
            f"❌ Неподдерживаемый формат файла. Разрешены: {allowed_str}"
        )
        return

    # Получаем текущий список файлов из состояния
    data = await state.get_data()
    files = data.get("files", [])

    # Добавляем метаданные файла
    file_metadata = {
        "file_id": document.file_id,
        "file_name": file_name,
        "file_size": document.file_size,
        "file_extension": file_extension,
    }
    files.append(file_metadata)

    # Сохраняем обновленный список в состояние
    await state.update_data(files=files)

    # Отвечаем пользователю
    count = len(files)
    await message.answer(
        f"✅ Файл принят, сейчас в очереди {count} файл(ов). "
        "Используйте /process когда будете готовы."
    )


@router.message(Command("reset"))
async def cmd_reset(message: Message, state: FSMContext) -> None:
    """Команда для очистки состояния и очереди файлов."""
    await state.clear()
    await message.answer("🔄 Очередь файлов очищена.")

