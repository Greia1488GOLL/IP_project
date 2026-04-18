from __future__ import annotations

import asyncio
import logging

from aiogram import Bot

from app.database import Database
from app.services.market_data import MarketAPIError, TwelveDataClient

logger = logging.getLogger(__name__)


class AlertMonitor:
    def __init__(
        self,
        bot: Bot,
        db: Database,
        market_client: TwelveDataClient,
        interval_seconds: int = 60,
    ) -> None:
        self.bot = bot
        self.db = db
        self.market_client = market_client
        self.interval_seconds = interval_seconds

    async def run(self) -> None:
        while True:
            try:
                await self.check_alerts()
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Unexpected error while checking alerts")

            await asyncio.sleep(self.interval_seconds)

    async def check_alerts(self) -> None:
        alerts = await self.db.get_active_alerts()
        if not alerts:
            return

        for alert in alerts:
            try:
                quote = await self.market_client.get_quote(alert["symbol"])
            except MarketAPIError as exc:
                logger.warning(
                    "Failed to fetch quote for %s: %s",
                    alert["symbol"],
                    exc,
                )
                continue

            current_price = quote["price"]
            is_triggered = (
                alert["direction"] == "above" and current_price >= alert["target_price"]
            ) or (
                alert["direction"] == "below" and current_price <= alert["target_price"]
            )

            if not is_triggered:
                continue

            await self.bot.send_message(
                alert["telegram_id"],
                (
                    f"Сработал алерт #{alert['id']}.\n"
                    f"{alert['symbol']} достиг {current_price:.2f}\n"
                    f"Условие: {alert['direction']} {alert['target_price']:.2f}"
                ),
            )
            await self.db.deactivate_alert(alert["id"], current_price)
