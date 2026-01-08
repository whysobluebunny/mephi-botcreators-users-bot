from pydantic import BaseModel


class ExportParseResult(BaseModel):
    mentioned_usernames: list[str]
