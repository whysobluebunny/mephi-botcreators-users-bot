import os

from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()


class Settings(BaseModel):
    bot_token: str
    env: str = "dev"
    log_level: str = "INFO"


def get_settings() -> Settings:
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN is not set in environment")

    return Settings(
        bot_token=token,
        env=os.getenv("ENV", "dev"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
    )
