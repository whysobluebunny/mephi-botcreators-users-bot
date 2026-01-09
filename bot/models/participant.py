from pydantic import BaseModel


class Participant(BaseModel):
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    bio: str | None = None
    # дата регистрации может быть None или датой первой активности по экспорту
    registration_date: str | None = None
    has_channel_in_profile: bool | None = None