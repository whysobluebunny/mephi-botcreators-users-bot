import logging
from pathlib import Path
from typing import Iterable, Protocol

from ..models.export_result import ExportParseResult, FinalResult

logger = logging.getLogger(__name__)


class Parser(Protocol):
    """Протокол для парсеров экспортов."""
    
    def parse(self, path: Path) -> ExportParseResult:
        """Парсит файл экспорта и возвращает результат."""
        ...


class Aggregator:
    """Агрегатор для объединения результатов парсинга нескольких экспортов."""
    
    def __init__(self, parsers: list[Parser]):
        """
        Инициализирует агрегатор с списком парсеров.
        
        Args:
            parsers: Список парсеров (JSON, HTML, ZIP и т.д.)
        """
        self.parsers = parsers
    
    def _select_parser(self, path: Path) -> Parser | None:
        """
        Выбирает подходящий парсер для файла по расширению.
        
        Args:
            path: Путь к файлу
            
        Returns:
            Парсер или None, если подходящий парсер не найден
        """
        extension = path.suffix.lower()
        
        for parser in self.parsers:
            # Приоритет 1: метод can_parse (если есть)
            if hasattr(parser, "can_parse"):
                try:
                    if parser.can_parse(path):
                        return parser
                except Exception as e:
                    logger.debug(f"Ошибка при вызове can_parse для {parser}: {e}")
                    continue
            
            # Приоритет 2: атрибут extensions (если есть)
            if hasattr(parser, "extensions"):
                if extension in parser.extensions:
                    return parser
        
        return None
    
    def parse_exports(self, paths: Iterable[Path]) -> FinalResult:
        """
        Парсит несколько файлов экспорта и объединяет результаты.
        
        Args:
            paths: Итерируемый объект с путями к файлам экспорта
            
        Returns:
            FinalResult с отсортированным списком всех упомянутых username без дублей
        """
        all_usernames: set[str] = set()
        
        for path in paths:
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
                logger.info(
                    f"Успешно обработан файл {path.name}: "
                    f"найдено {len(result.mentioned_usernames)} username"
                )
            except Exception as e:
                logger.error(
                    f"Ошибка при парсинге файла {path.name}: {e}",
                    exc_info=True
                )
                # Продолжаем обработку остальных файлов
                continue
        
        # Сортируем и создаем итоговый результат
        sorted_usernames = sorted(all_usernames)
        
        return FinalResult(mentioned_usernames=sorted_usernames)
