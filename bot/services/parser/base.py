from abc import ABC, abstractmethod
from pathlib import Path

from ...models.export_result import ExportParseResult


class ChatExportParser(ABC):
    @abstractmethod
    def can_handle(self, path: Path) -> bool:
        raise NotImplementedError

    @abstractmethod
    def parse(self, path: Path) -> ExportParseResult:
        raise NotImplementedError
