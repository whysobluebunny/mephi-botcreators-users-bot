from pydantic import BaseModel
from typing import Set


class ExportParseResult(BaseModel):
    mentioned_usernames: Set[str] = set()

class FinalResult(BaseModel):
    mentioned_usernames: list[str]
