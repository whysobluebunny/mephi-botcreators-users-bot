import logging
from pathlib import Path
from typing import List, Dict, Optional

from aiogram import Bot

log = logging.getLogger(__name__)

async def download_files(bot: Bot, files_data: List[Dict[str, str]], base_dir: Path, user_id: Optional[int] = None) -> List[Path]:
    downloaded_paths = []
    
    for file_info in files_data:
        file_id = file_info["file_id"]
        file_name = file_info["file_name"]
        
        destination = base_dir / file_name
        
        log.info(
            "event=file_download_start user_id=%s file_name=%s file_id=%s",
            user_id,
            file_name,
            file_id,
        )
        
        try:
            # Скачиваем файл
            await bot.download(file=file_id, destination=destination)
            
            log.info(
                "event=file_download_ok user_id=%s file_name=%s local_path=%s",
                user_id,
                file_name,
                str(destination),
            )
            downloaded_paths.append(destination)
            
        except Exception:
            log.exception(
                "event=file_download_failed user_id=%s file_name=%s",
                user_id,
                file_name,
            )
            # Решаем, прерывать ли процесс или продолжать. 
            # Обычно лучше упасть или пропустить. В requirements не сказано, но логичнее пропустить или упасть.
            # Если упадем, то весь процесс остановится, что наверное правильно если файл критичен.
            raise
        
    return downloaded_paths
