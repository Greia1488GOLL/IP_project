from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.database import Database
from app.keyboards.common import main_keyboard, ticker_actions_keyboard
from app.services.market_data import MarketAPIError, TwelveDataClient

router = Router()


@router.message(Command("addticker"))
async def cmd_add_ticker(
    message: Message,
    db: Database,
    market_client: TwelveDataClient,
) -> None:
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer(
            "Ticker is missing.\nUse <code>/addticker AAPL</code>.",
            parse_mode="HTML",
            reply_markup=main_keyboard(),
        )
        return

    symbol = parts[1].strip().upper()
    await db.upsert_user(message.from_user.id, message.from_user.username)

    try:
        quote = await market_client.get_quote(symbol)
    except MarketAPIError as exc:
        await message.answer(
            f"Could not add <b>{symbol}</b>.\nReason: {exc}",
            parse_mode="HTML",
            reply_markup=main_keyboard(),
        )
        return

    created = await db.add_ticker(message.from_user.id, symbol)
    if created:
        await message.answer(
            f"<b>{symbol}</b> added.\n"
            f"Current price: <b>{quote['price']:.2f} {quote['currency']}</b>",
            parse_mode="HTML",
            reply_markup=ticker_actions_keyboard(symbol),
        )
    else:
        await message.answer(
            f"<b>{symbol}</b> is already in your list.",
            parse_mode="HTML",
            reply_markup=main_keyboard(),
        )


@router.message(Command("removeticker"))
async def cmd_remove_ticker(message: Message, db: Database) -> None:
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer(
            "Ticker is missing.\nUse <code>/removeticker AAPL</code>.",
            parse_mode="HTML",
            reply_markup=main_keyboard(),
        )
        return

    symbol = parts[1].strip().upper()
    removed = await db.remove_ticker(message.from_user.id, symbol)
    await message.answer(
        f"{symbol} removed from your list." if removed else f"{symbol} was not found in your list.",
        reply_markup=main_keyboard(),
    )


@router.message(Command("mytickers"))
async def cmd_my_tickers(message: Message, db: Database) -> None:
    tickers = await db.list_tickers(message.from_user.id)
    if not tickers:
        await message.answer(
            "Your ticker list is empty.",
            reply_markup=main_keyboard(),
        )
        return

    await message.answer("<b>Your tickers</b>", parse_mode="HTML", reply_markup=main_keyboard())
    for ticker in tickers:
        await message.answer(
            f"<b>{ticker}</b>",
            parse_mode="HTML",
            reply_markup=ticker_actions_keyboard(ticker),
        )
