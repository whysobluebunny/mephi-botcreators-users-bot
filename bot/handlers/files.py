import logging

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from ..states import UploadState

router = Router()
log = logging.getLogger(__name__)
# Захардкоженные настройки (позже можно вынести в конфиг)
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB
ALLOWED_EXTENSIONS = {".json", ".html", ".zip"}


@router.message(F.document)
async def handle_document(message: Message, state: FSMContext) -> None:
    # Устанавливаем состояние, если его еще нет
    current_state = await state.get_state()
    if current_state is None:
        await state.set_state(UploadState.waiting_files)

    document = message.document
    log.info(
        "event=document_received user_id=%s chat_id=%s file_name=%s file_size=%s mime=%s",
        message.from_user.id if message.from_user else None,
        message.chat.id if message.chat else None,
        document.file_name,
        document.file_size,
        document.mime_type,
    )

    if document.file_size and document.file_size > MAX_FILE_SIZE:
        log.warning(
            "event=document_rejected reason=file_too_large user_id=%s file_name=%s file_size=%s limit=%s",
            message.from_user.id if message.from_user else None,
            document.file_name,
            document.file_size,
            MAX_FILE_SIZE,
        )
        await message.answer(
            f"❌ Файл слишком большой. Максимальный размер: {MAX_FILE_SIZE / (1024 * 1024):.0f} MB"
        )
        return

    file_name = document.file_name or ""
    file_extension = None
    for ext in ALLOWED_EXTENSIONS:
        if file_name.lower().endswith(ext):
            file_extension = ext
            break

    if not file_extension:
        allowed_str = ", ".join(ALLOWED_EXTENSIONS)
        log.warning(
            "event=document_rejected reason=unsupported_extension user_id=%s file_name=%s",
            message.from_user.id if message.from_user else None,
            document.file_name,
        )
        await message.answer(
            f"❌ Неподдерживаемый формат файла. Разрешены: {allowed_str}"
        )
        return

    log.info(
        "document received user_id=%s name=%s size=%s",
        message.from_user.id,
        document.file_name,
        document.file_size,
    )

    data = await state.get_data()
    files = data.get("files", [])

    file_metadata = {
        "file_id": document.file_id,
        "file_name": file_name,
        "file_size": document.file_size,
        "file_extension": file_extension,
    }
    files.append(file_metadata)

    await state.update_data(files=files)
    log.info(
        "event=document_accepted user_id=%s file_name=%s queued=%s",
        message.from_user.id if message.from_user else None,
        document.file_name,
        len(files),
    )
    count = len(files)
    await message.answer(
        f"✅ Файл принят, сейчас в очереди {count} файл(ов). "
        "Используйте /process когда будете готовы."
    )


@router.message(Command("reset"))
async def cmd_reset(message: Message, state: FSMContext) -> None:
    log.info(
        "cmd=/reset user_id=%s chat_id=%s",
        message.from_user.id if message.from_user else None,
        message.chat.id if message.chat else None,
    )
    await state.clear()
    await message.answer("🔄 Очередь файлов очищена.")
