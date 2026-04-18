from __future__ import annotations

from typing import Any

import aiosqlite


class Database:
    def __init__(self, path: str) -> None:
        self.path = path
        self.conn: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        self.conn = await aiosqlite.connect(self.path)
        self.conn.row_factory = aiosqlite.Row
        await self.conn.execute("PRAGMA foreign_keys = ON;")

    async def close(self) -> None:
        if self.conn is not None:
            await self.conn.close()

    async def init_schema(self) -> None:
        await self.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                username TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        await self.execute(
            """
            CREATE TABLE IF NOT EXISTS user_tickers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL,
                symbol TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(telegram_id, symbol),
                FOREIGN KEY (telegram_id) REFERENCES users (telegram_id) ON DELETE CASCADE
            );
            """
        )
        await self.execute(
            """
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL,
                symbol TEXT NOT NULL,
                direction TEXT NOT NULL CHECK(direction IN ('above', 'below')),
                target_price REAL NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1,
                last_triggered_price REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (telegram_id) REFERENCES users (telegram_id) ON DELETE CASCADE
            );
            """
        )
        await self.conn.commit()

    async def execute(self, query: str, params: tuple[Any, ...] = ()) -> aiosqlite.Cursor:
        if self.conn is None:
            raise RuntimeError("Database is not connected")
        cursor = await self.conn.execute(query, params)
        await self.conn.commit()
        return cursor

    async def fetchone(self, query: str, params: tuple[Any, ...] = ()) -> aiosqlite.Row | None:
        if self.conn is None:
            raise RuntimeError("Database is not connected")
        cursor = await self.conn.execute(query, params)
        return await cursor.fetchone()

    async def fetchall(self, query: str, params: tuple[Any, ...] = ()) -> list[aiosqlite.Row]:
        if self.conn is None:
            raise RuntimeError("Database is not connected")
        cursor = await self.conn.execute(query, params)
        return await cursor.fetchall()

    async def upsert_user(self, telegram_id: int, username: str | None) -> None:
        await self.execute(
            """
            INSERT INTO users (telegram_id, username)
            VALUES (?, ?)
            ON CONFLICT(telegram_id) DO UPDATE SET username = excluded.username;
            """,
            (telegram_id, username),
        )

    async def add_ticker(self, telegram_id: int, symbol: str) -> bool:
        cursor = await self.execute(
            """
            INSERT OR IGNORE INTO user_tickers (telegram_id, symbol)
            VALUES (?, ?);
            """,
            (telegram_id, symbol.upper()),
        )
        return cursor.rowcount > 0

    async def remove_ticker(self, telegram_id: int, symbol: str) -> bool:
        cursor = await self.execute(
            """
            DELETE FROM user_tickers
            WHERE telegram_id = ? AND symbol = ?;
            """,
            (telegram_id, symbol.upper()),
        )
        return cursor.rowcount > 0

    async def list_tickers(self, telegram_id: int) -> list[str]:
        rows = await self.fetchall(
            """
            SELECT symbol
            FROM user_tickers
            WHERE telegram_id = ?
            ORDER BY symbol;
            """,
            (telegram_id,),
        )
        return [row["symbol"] for row in rows]

    async def add_alert(
        self,
        telegram_id: int,
        symbol: str,
        direction: str,
        target_price: float,
    ) -> int:
        cursor = await self.execute(
            """
            INSERT INTO alerts (telegram_id, symbol, direction, target_price)
            VALUES (?, ?, ?, ?);
            """,
            (telegram_id, symbol.upper(), direction, target_price),
        )
        return int(cursor.lastrowid)

    async def list_alerts(self, telegram_id: int) -> list[dict[str, Any]]:
        rows = await self.fetchall(
            """
            SELECT id, symbol, direction, target_price, is_active, created_at
            FROM alerts
            WHERE telegram_id = ?
            ORDER BY id DESC;
            """,
            (telegram_id,),
        )
        return [dict(row) for row in rows]

    async def remove_alert(self, telegram_id: int, alert_id: int) -> bool:
        cursor = await self.execute(
            """
            DELETE FROM alerts
            WHERE telegram_id = ? AND id = ?;
            """,
            (telegram_id, alert_id),
        )
        return cursor.rowcount > 0

    async def get_active_alerts(self) -> list[dict[str, Any]]:
        rows = await self.fetchall(
            """
            SELECT id, telegram_id, symbol, direction, target_price
            FROM alerts
            WHERE is_active = 1
            ORDER BY id ASC;
            """
        )
        return [dict(row) for row in rows]

    async def deactivate_alert(self, alert_id: int, triggered_price: float) -> None:
        await self.execute(
            """
            UPDATE alerts
            SET is_active = 0, last_triggered_price = ?
            WHERE id = ?;
            """,
            (triggered_price, alert_id),
        )
