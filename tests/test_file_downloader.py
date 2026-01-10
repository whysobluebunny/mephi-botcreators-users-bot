from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from bot.services.file_downloader import download_files


@pytest.mark.asyncio
async def test_download_files():
    bot = AsyncMock()
    files_data = [
        {"file_id": "id1", "file_name": "file1.json"},
        {"file_id": "id2", "file_name": "file2.json"}
    ]
    base_dir = Path("/tmp/test")

    paths = await download_files(bot, files_data, base_dir, user_id=123)

    # Проверяем количество вызовов download
    assert bot.download.call_count == 2

    # Проверяем правильность формирования путей
    assert len(paths) == 2
    assert paths[0] == base_dir / "file1.json"
    assert paths[1] == base_dir / "file2.json"

    # Проверяем аргументы вызова bot.download
    # 1 вызов
    bot.download.assert_any_call(file="id1", destination=base_dir / "file1.json")
    # 2 вызов
    bot.download.assert_any_call(file="id2", destination=base_dir / "file2.json")
