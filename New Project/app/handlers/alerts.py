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
            "Используйте формат <code>/setalert AAPL above 200</code>.",
            parse_mode="HTML",
            reply_markup=main_keyboard(),
        )
        return

    _, symbol, direction, price_raw = parts
    symbol = symbol.upper()
    direction = direction.lower()

    if direction not in {"above", "below"}:
        await message.answer(
            "Направление должно быть <code>above</code> или <code>below</code>.",
            parse_mode="HTML",
            reply_markup=main_keyboard(),
        )
        return

    try:
        target_price = float(price_raw)
    except ValueError:
        await message.answer(
            "Цена должна быть числом.",
            parse_mode="HTML",
            reply_markup=main_keyboard(),
        )
        return

    await db.upsert_user(message.from_user.id, message.from_user.username)
    try:
        quote = await market_client.get_quote(symbol)
    except MarketAPIError as exc:
        await message.answer(
            f"Не удалось создать алерт для <b>{symbol}</b>.\nПричина: {exc}",
            parse_mode="HTML",
            reply_markup=main_keyboard(),
        )
        return

    alert_id = await db.add_alert(message.from_user.id, symbol, direction, target_price)
    direction_text = "выше" if direction == "above" else "ниже"
    await message.answer(
        f"<b>Алерт создан</b>\n"
        f"ID: <b>#{alert_id}</b>\n"
        f"{symbol} — цена {direction_text} <b>{target_price:.2f}</b>\n"
        f"Текущая цена: <b>{quote['price']:.2f} {quote['currency']}</b>",
        parse_mode="HTML",
        reply_markup=alert_remove_keyboard(alert_id),
    )


@router.message(Command("alerts"))
async def cmd_alerts(message: Message, db: Database) -> None:
    alerts = await db.list_alerts(message.from_user.id)
    if not alerts:
        await message.answer(
            "У вас пока нет алертов.",
            reply_markup=main_keyboard(),
        )
        return

    await message.answer("<b>Ваши алерты</b>", parse_mode="HTML", reply_markup=main_keyboard())
    for alert in alerts:
        direction = "выше" if alert["direction"] == "above" else "ниже"
        status = "активен" if alert["is_active"] else "сработал"
        await message.answer(
            f"<b>#{alert['id']}</b> {alert['symbol']}\n"
            f"Условие: цена {direction} <b>{alert['target_price']:.2f}</b>\n"
            f"Статус: <i>{status}</i>",
            parse_mode="HTML",
            reply_markup=alert_remove_keyboard(alert["id"]),
        )


@router.message(Command("removealert"))
async def cmd_remove_alert(message: Message, db: Database) -> None:
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer(
            "Используйте <code>/removealert 1</code>.",
            parse_mode="HTML",
            reply_markup=main_keyboard(),
        )
        return

    try:
        alert_id = int(parts[1].strip())
    except ValueError:
        await message.answer(
            "ID алерта должен быть числом.",
            parse_mode="HTML",
            reply_markup=main_keyboard(),
        )
        return

    removed = await db.remove_alert(message.from_user.id, alert_id)
    await message.answer(
        f"Алерт #{alert_id} удален." if removed else f"Алерт #{alert_id} не найден.",
        reply_markup=main_keyboard(),
    )


@router.callback_query(F.data.startswith("alert:remove:"))
async def cb_remove_alert(callback: CallbackQuery, db: Database) -> None:
    alert_id = int(callback.data.split(":")[-1])
    removed = await db.remove_alert(callback.from_user.id, alert_id)
    await callback.answer("Удалено" if removed else "Не найдено")
    await callback.message.edit_text(
        f"Алерт #{alert_id} удален." if removed else f"Алерт #{alert_id} уже отсутствует."
    )
