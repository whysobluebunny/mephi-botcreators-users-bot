import time
import logging
import tempfile
from pathlib import Path
from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile

from bot.states import UploadState
from bot.services.file_downloader import download_files
from bot.services.aggregator import Aggregator
from bot.services.excel_exporter import ExcelExporter

router = Router()
log = logging.getLogger(__name__)

@router.message(Command("process"))
async def process_files(message: types.Message, state: FSMContext) -> None:
    t0 = time.monotonic()
    
    log.info(
        "cmd=/process user_id=%s chat_id=%s",
        message.from_user.id if message.from_user else None,
        message.chat.id if message.chat else None,
    )

    data = await state.get_data()
    files = data.get("files", [])
    
    log.info(
        "event=process_started user_id=%s files_count=%s",
        message.from_user.id if message.from_user else None,
        len(files),
    )

    if not files:
        log.warning(
            "event=process_aborted reason=no_files user_id=%s",
            message.from_user.id if message.from_user else None,
        )
        await message.answer("⚠️ Нет файлов для обработки. Загрузите их сначала (отправьте JSON файлы).")
        return

    status_msg = await message.answer("⏳ Начинаю обработку файлов...")

    try:
        # Создаем временную директорию
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Скачиваем файлы (логирование внутри)
            file_paths = await download_files(
                message.bot, 
                files, 
                temp_path, 
                user_id=message.from_user.id if message.from_user else None
            )
            
            # Агрегируем данные
            aggregator = Aggregator()
            
            log.info(
                "event=parsing_start user_id=%s files_count=%s",
                message.from_user.id if message.from_user else None,
                len(file_paths),
            )
            
            result = aggregator.parse_exports([str(p) for p in file_paths])
            mentions_count = len(result.mentioned_usernames)
            names_count = len(result.chat_names)
            
            log.info(
                "event=parsing_ok user_id=%s mentions_found=%d names_found=%d",
                message.from_user.id if message.from_user else None,
                mentions_count,
                names_count,
            )
            
            if mentions_count < 50 or names_count < 50:
                # Отправляем @username
                if result.mentioned_usernames:
                    text_list = "\n".join([f"@{u}" for u in sorted(result.mentioned_usernames)])
                    text = f"📌 Найдено {mentions_count} @username:\n\n{text_list}"
                    await message.answer(text)
                    
                    log.info(
                        "event=usernames_sent user_id=%s count=%d",
                        message.from_user.id if message.from_user else None,
                        mentions_count,
                    )
                
                # Отправляем имена отдельно
                if result.chat_names:
                    names_list = "\n".join([f"• {name}" for name in sorted(result.chat_names)])
                    text = f"👤 Найдено {names_count} имён пользователей:\n\n{names_list}"
                    await message.answer(text)
                    
                    log.info(
                        "event=names_sent user_id=%s count=%d",
                        message.from_user.id if message.from_user else None,
                        names_count,
                    )
                
                # Если ничего не найдено
                if not result.mentioned_usernames and not result.chat_names:
                    text = "Результат: Упомянутых пользователей и имён не найдено."
                    await message.answer(text)
            else:
                exporter = ExcelExporter()
                excel_filename = f"mentions_{message.from_user.id}.xlsx"
                excel_path = temp_path / excel_filename

                exporter.build_excel(result, excel_path)

                log.info(
                    "event=excel_generated user_id=%s path=%s",
                    message.from_user.id if message.from_user else None,
                    str(excel_path),
                )

                # Отправляем файл
                input_file = FSInputFile(excel_path)
                await message.answer_document(
                    input_file,
                    caption=f"📊 Найдено {mentions_count} пользователей. Список во вложении."
                )

                log.info(
                    "event=excel_sent user_id=%s",
                    message.from_user.id if message.from_user else None,
                )
        
        # Очищаем состояние
        await state.clear()
        
        log.info(
            "event=process_finished user_id=%s elapsed_ms=%d",
            message.from_user.id if message.from_user else None,
            int((time.monotonic() - t0) * 1000),
        )
        
        # Удаляем сообщение со статусом
        await status_msg.delete()
        
    except Exception as e:
        log.exception(
            "event=process_failed user_id=%s error=%s",
            message.from_user.id if message.from_user else None,
            str(e)
        )
        await message.answer(f"❌ Произошла ошибка при обработке: {e}")
