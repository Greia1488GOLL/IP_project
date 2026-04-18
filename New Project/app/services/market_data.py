from __future__ import annotations

import aiohttp
import csv
import io


class MarketAPIError(Exception):
    pass


class TwelveDataClient:
    BASE_URL = "https://stooq.com/q/l/"

    def __init__(self) -> None:
        self.session = aiohttp.ClientSession()

    async def close(self) -> None:
        await self.session.close()

    @staticmethod
    def normalize_symbol(symbol: str) -> str:
        normalized = symbol.strip().lower()
        if "." in normalized:
            return normalized
        return f"{normalized}.us"

    async def get_quote(self, symbol: str) -> dict:
        params = {
            "s": self.normalize_symbol(symbol),
            "f": "sd2t2ohlcvn",
            "h": "",
            "e": "csv",
        }
        async with self.session.get(self.BASE_URL, params=params, timeout=15) as response:
            if response.status != 200:
                raise MarketAPIError(f"HTTP {response.status}")

            raw_csv = await response.text()

        try:
            reader = csv.DictReader(io.StringIO(raw_csv))
            data = next(reader)
        except Exception as exc:
            raise MarketAPIError("Failed to parse market response") from exc

        close_price = (data.get("Close") or "").strip()
        name = (data.get("Name") or symbol.upper()).strip()
        exchange = (data.get("Time") or "unknown").strip()

        if not close_price or close_price in {"N/D", "-"}:
            raise MarketAPIError("Ticker not found or price unavailable")

        try:
            return {
                "symbol": symbol.upper(),
                "price": float(close_price),
                "currency": "USD",
                "exchange": exchange,
                "name": name,
            }
        except (KeyError, ValueError, TypeError) as exc:
            raise MarketAPIError("Unexpected API response") from exc
