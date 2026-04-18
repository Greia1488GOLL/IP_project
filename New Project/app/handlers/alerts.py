from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from app.database import Database
from app.keyboards.common import alert_remove_keyboard, main_keyboard
from app.services.market_data import MarketAPIError, TwelveDataClient

router = Router()


@router.message(Command("setalert"))
async def cmd_set_alert(
    message: Message,
    db: Database,
    market_client: TwelveDataClient,
) -> None:
    parts = message.text.split()
    if len(parts) != 4:
        await message.answer(
            "Use format <code>/setalert AAPL above 200</code>.",
            parse_mode="HTML",
            reply_markup=main_keyboard(),
        )
        return

    _, symbol, direction, price_raw = parts
    symbol = symbol.upper()
    direction = direction.lower()

    if direction not in {"above", "below"}:
        await message.answer(
            "Direction must be <code>above</code> or <code>below</code>.",
            parse_mode="HTML",
            reply_markup=main_keyboard(),
        )
        return

    try:
        target_price = float(price_raw)
    except ValueError:
        await message.answer(
            "Price must be numeric.",
            parse_mode="HTML",
            reply_markup=main_keyboard(),
        )
        return

    await db.upsert_user(message.from_user.id, message.from_user.username)
    try:
        quote = await market_client.get_quote(symbol)
    except MarketAPIError as exc:
        await message.answer(
            f"Could not create alert for <b>{symbol}</b>.\nReason: {exc}",
            parse_mode="HTML",
            reply_markup=main_keyboard(),
        )
        return

    alert_id = await db.add_alert(message.from_user.id, symbol, direction, target_price)
    await message.answer(
        f"<b>Alert created</b>\n"
        f"ID: <b>#{alert_id}</b>\n"
        f"{symbol} — {direction} <b>{target_price:.2f}</b>\n"
        f"Current price: <b>{quote['price']:.2f} {quote['currency']}</b>",
        parse_mode="HTML",
        reply_markup=alert_remove_keyboard(alert_id),
    )


@router.message(Command("alerts"))
async def cmd_alerts(message: Message, db: Database) -> None:
    alerts = await db.list_alerts(message.from_user.id)
    if not alerts:
        await message.answer(
            "You do not have alerts yet.",
            reply_markup=main_keyboard(),
        )
        return

    await message.answer("<b>Your alerts</b>", parse_mode="HTML", reply_markup=main_keyboard())
    for alert in alerts:
        status = "active" if alert["is_active"] else "triggered"
        await message.answer(
            f"<b>#{alert['id']}</b> {alert['symbol']}\n"
            f"Condition: {alert['direction']} <b>{alert['target_price']:.2f}</b>\n"
            f"Status: <i>{status}</i>",
            parse_mode="HTML",
            reply_markup=alert_remove_keyboard(alert["id"]),
        )


@router.message(Command("removealert"))
async def cmd_remove_alert(message: Message, db: Database) -> None:
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer(
            "Use <code>/removealert 1</code>.",
            parse_mode="HTML",
            reply_markup=main_keyboard(),
        )
        return

    try:
        alert_id = int(parts[1].strip())
    except ValueError:
        await message.answer(
            "Alert ID must be numeric.",
            parse_mode="HTML",
            reply_markup=main_keyboard(),
        )
        return

    removed = await db.remove_alert(message.from_user.id, alert_id)
    await message.answer(
        f"Alert #{alert_id} removed." if removed else f"Alert #{alert_id} was not found.",
        reply_markup=main_keyboard(),
    )


@router.callback_query(F.data.startswith("alert:remove:"))
async def cb_remove_alert(callback: CallbackQuery, db: Database) -> None:
    alert_id = int(callback.data.split(":")[-1])
    removed = await db.remove_alert(callback.from_user.id, alert_id)
    await callback.answer("Removed" if removed else "Not found")
    await callback.message.edit_text(
        f"Alert #{alert_id} removed." if removed else f"Alert #{alert_id} was already removed."
    )
