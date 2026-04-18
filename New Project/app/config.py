from dataclasses import dataclass
from functools import lru_cache
import os

from dotenv import load_dotenv


load_dotenv()


@dataclass(slots=True)
class Settings:
    bot_token: str
    database_path: str = "bot.db"
    alert_check_interval: int = 60


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    bot_token = os.getenv("BOT_TOKEN", "").strip()
    database_path = os.getenv("DATABASE_PATH", "bot.db").strip()
    alert_check_interval = int(os.getenv("ALERT_CHECK_INTERVAL", "60"))

    if not bot_token:
        raise ValueError("BOT_TOKEN is not set")

    return Settings(
        bot_token=bot_token,
        database_path=database_path,
        alert_check_interval=alert_check_interval,
    )
