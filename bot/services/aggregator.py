import logging
from pathlib import Path
from typing import Iterable, Protocol

from ..models.export_result import ExportParseResult

logger = logging.getLogger(__name__)


class Parser(Protocol):
    def parse(self, path: Path) -> ExportParseResult:
        ...


class Aggregator:
    def __init__(self, parsers: list[Parser] | None = None):
        if parsers is None:
            # Инициализируем парсеры по умолчанию
            from .parser.telegram_json_parser import TelegramJsonParser
            self.parsers = [TelegramJsonParser(bot=None)]
        else:
            self.parsers = parsers
    
    def _select_parser(self, path: Path) -> Parser | None:
        extension = path.suffix.lower()
        
        for parser in self.parsers:
            # Пытаемся использовать can_handle (новый способ)
            if hasattr(parser, "can_handle"):
                try:
                    if parser.can_handle(path):
                        return parser
                except Exception as e:
                    logger.debug(f"Ошибка при вызове can_handle для {parser}: {e}")
                    continue
            
            # Старый способ для совместимости
            if hasattr(parser, "can_parse"):
                try:
                    if parser.can_parse(path):
                        return parser
                except Exception as e:
                    logger.debug(f"Ошибка при вызове can_parse для {parser}: {e}")
                    continue
            
            if hasattr(parser, "extensions"):
                if extension in parser.extensions:
                    return parser
        
        return None
    
    def parse_exports(self, paths: Iterable[Path]) -> ExportParseResult:
        all_usernames: set[str] = set()
        all_names: set[str] = set()
        
        for path in paths:
            # Конвертируем строку в Path если необходимо
            if isinstance(path, str):
                path = Path(path)
            
            parser = self._select_parser(path)
            
            if parser is None:
                logger.warning(
                    f"Не найден подходящий парсер для файла {path.name} "
                    f"(расширение: {path.suffix}). Файл будет пропущен."
                )
                continue
            
            try:
                result = parser.parse(path)
                all_usernames.update(result.mentioned_usernames)
                all_names.update(result.chat_names)
                logger.info(
                    f"Успешно обработан файл {path.name}: "
                    f"найдено {len(result.mentioned_usernames)} usernames, {len(result.chat_names)} names"
                )
            except Exception as e:
                logger.error(
                    f"Ошибка при парсинге файла {path.name}: {e}",
                    exc_info=True
                )
                continue
        
        return ExportParseResult(mentioned_usernames=all_usernames, chat_names=all_names)
