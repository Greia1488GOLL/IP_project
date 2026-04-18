import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.exceptions import TelegramUnauthorizedError

from app.config import get_settings
from app.database import Database
from app.handlers import register_routers
from app.services.alerts import AlertMonitor
from app.services.market_data import TwelveDataClient


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    settings = get_settings()
    db = Database(settings.database_path)
    await db.connect()
    await db.init_schema()

    bot = Bot(token=settings.bot_token)
    dp = Dispatcher()

    market_client = TwelveDataClient()
    alert_monitor = AlertMonitor(
        bot=bot,
        db=db,
        market_client=market_client,
        interval_seconds=settings.alert_check_interval,
    )

    dp["db"] = db
    dp["market_client"] = market_client
    register_routers(dp)

    monitor_task = asyncio.create_task(alert_monitor.run(), name="alert-monitor")

    try:
        await dp.start_polling(bot)
    finally:
        monitor_task.cancel()
        await asyncio.gather(monitor_task, return_exceptions=True)
        await market_client.close()
        await db.close()
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except TelegramUnauthorizedError:
        logging.error(
            "Telegram rejected the bot token. Update BOT_TOKEN in .env with a valid token from BotFather."
        )
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped")
