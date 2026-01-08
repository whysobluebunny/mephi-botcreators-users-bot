from pydantic import BaseModel


class ExportParseResult(BaseModel):
    """Результат парсинга одного файла экспорта."""
    mentioned_usernames: list[str]


class FinalResult(BaseModel):
    """Итоговый результат объединения нескольких ExportParseResult."""
    mentioned_usernames: list[str]
