from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from app.database import Database
from app.keyboards.common import (
    ADD_TICKER_BUTTON,
    ALERTS_BUTTON,
    BACK_BUTTON,
    CREATE_ALERT_BUTTON,
    HELP_BUTTON,
    PRICE_BUTTON,
    TICKERS_BUTTON,
    alert_direction_keyboard,
    alert_remove_keyboard,
    back_keyboard,
    main_keyboard,
    price_result_keyboard,
    ticker_actions_keyboard,
)
from app.services.market_data import MarketAPIError, TwelveDataClient

router = Router()


class UserFlow(StatesGroup):
    waiting_price_symbol = State()
    waiting_ticker_symbol = State()
    waiting_alert_symbol = State()
    waiting_alert_price = State()


HELP_TEXT = (
    "<b>Что умеет бот</b>\n"
    "• Показывать текущую цену акции\n"
    "• Сохранять ваши тикеры\n"
    "• Присылать уведомления, когда цена выше или ниже нужного уровня\n\n"
    "<b>Основные команды</b>\n"
    "• <code>/price AAPL</code>\n"
    "• <code>/addticker AAPL</code>\n"
    "• <code>/mytickers</code>\n"
    "• <code>/setalert AAPL above 200</code>\n"
    "• <code>/alerts</code>\n\n"
    "Или просто используйте кнопки ниже."
)


WELCOME_TEXT = (
    "<b>Добро пожаловать</b>\n"
    "Этот бот помогает удобно следить за акциями.\n\n"
    "Вы можете:\n"
    "• узнать текущую цену акции\n"
    "• сохранить интересующие тикеры\n"
    "• создать алерт по цене\n\n"
    "Выберите действие в меню ниже."
)


async def send_price_card(
    target: Message | CallbackQuery,
    market_client: TwelveDataClient,
    symbol: str,
) -> None:
    quote = await market_client.get_quote(symbol)
    text = (
        f"<b>{quote['symbol']}</b> — {quote.get('name', quote['symbol'])}\n"
        f"Текущая цена: <b>{quote['price']:.2f} {quote['currency']}</b>\n"
        f"Источник времени/сессии: {quote['exchange']}"
    )

    if isinstance(target, CallbackQuery):
        await target.message.answer(
            text,
            parse_mode="HTML",
            reply_markup=price_result_keyboard(quote["symbol"]),
        )
    else:
        await target.answer(
            text,
            parse_mode="HTML",
            reply_markup=price_result_keyboard(quote["symbol"]),
        )


@router.message(Command("start"))
async def cmd_start(message: Message, db: Database) -> None:
    await db.upsert_user(message.from_user.id, message.from_user.username)
    await message.answer(
        WELCOME_TEXT,
        parse_mode="HTML",
        reply_markup=main_keyboard(),
    )


@router.message(Command("help"))
@router.message(F.text == HELP_BUTTON)
async def cmd_help(message: Message) -> None:
    await message.answer(HELP_TEXT, parse_mode="HTML", reply_markup=main_keyboard())


@router.message(F.text == BACK_BUTTON)
async def go_back(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Возвращаемся в главное меню.", reply_markup=main_keyboard())


@router.message(F.text == PRICE_BUTTON)
async def ask_price_symbol(message: Message, state: FSMContext) -> None:
    await state.set_state(UserFlow.waiting_price_symbol)
    await message.answer(
        "Введите тикер, например <code>AAPL</code>.",
        parse_mode="HTML",
        reply_markup=back_keyboard(),
    )


@router.message(F.text == ADD_TICKER_BUTTON)
async def ask_ticker_to_add(message: Message, state: FSMContext) -> None:
    await state.set_state(UserFlow.waiting_ticker_symbol)
    await message.answer(
        "Введите тикер, который хотите добавить, например <code>NVDA</code>.",
        parse_mode="HTML",
        reply_markup=back_keyboard(),
    )


@router.message(F.text == CREATE_ALERT_BUTTON)
async def ask_alert_symbol(message: Message, state: FSMContext) -> None:
    await state.set_state(UserFlow.waiting_alert_symbol)
    await message.answer(
        "Введите тикер для алерта, например <code>TSLA</code>.",
        parse_mode="HTML",
        reply_markup=back_keyboard(),
    )


@router.message(F.text == TICKERS_BUTTON)
async def show_tickers(message: Message, db: Database) -> None:
    tickers = await db.list_tickers(message.from_user.id)
    if not tickers:
        await message.answer(
            "Список тикеров пока пуст.\nНажмите <b>Добавить тикер</b>, чтобы сохранить первый.",
            parse_mode="HTML",
            reply_markup=main_keyboard(),
        )
        return

    await message.answer("<b>Ваши тикеры</b>", parse_mode="HTML", reply_markup=main_keyboard())
    for ticker in tickers:
        await message.answer(
            f"<b>{ticker}</b>",
            parse_mode="HTML",
            reply_markup=ticker_actions_keyboard(ticker),
        )


@router.message(F.text == ALERTS_BUTTON)
async def show_alerts(message: Message, db: Database) -> None:
    alerts = await db.list_alerts(message.from_user.id)
    if not alerts:
        await message.answer(
            "У вас пока нет алертов.\nНажмите <b>Создать алерт</b>, чтобы добавить первый.",
            parse_mode="HTML",
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


@router.message(UserFlow.waiting_price_symbol, F.text)
async def handle_price_symbol(
    message: Message,
    state: FSMContext,
    market_client: TwelveDataClient,
) -> None:
    symbol = message.text.strip().upper()
    try:
        await send_price_card(message, market_client, symbol)
    except MarketAPIError as exc:
        await message.answer(
            f"Не удалось получить цену для <b>{symbol}</b>.\nПричина: {exc}",
            parse_mode="HTML",
            reply_markup=back_keyboard(),
        )
        return

    await state.clear()
    await message.answer("Готово.", reply_markup=main_keyboard())


@router.message(UserFlow.waiting_ticker_symbol, F.text)
async def handle_ticker_symbol(
    message: Message,
    state: FSMContext,
    db: Database,
    market_client: TwelveDataClient,
) -> None:
    symbol = message.text.strip().upper()
    await db.upsert_user(message.from_user.id, message.from_user.username)
    try:
        quote = await market_client.get_quote(symbol)
    except MarketAPIError as exc:
        await message.answer(
            f"Не удалось добавить <b>{symbol}</b>.\nПричина: {exc}",
            parse_mode="HTML",
            reply_markup=back_keyboard(),
        )
        return

    created = await db.add_ticker(message.from_user.id, symbol)
    await state.clear()
    if created:
        await message.answer(
            f"<b>{symbol}</b> добавлен.\n"
            f"Текущая цена: <b>{quote['price']:.2f} {quote['currency']}</b>",
            parse_mode="HTML",
            reply_markup=ticker_actions_keyboard(symbol),
        )
    else:
        await message.answer(
            f"<b>{symbol}</b> уже есть в вашем списке.",
            parse_mode="HTML",
            reply_markup=main_keyboard(),
        )


@router.message(UserFlow.waiting_alert_symbol, F.text)
async def handle_alert_symbol(
    message: Message,
    state: FSMContext,
    market_client: TwelveDataClient,
) -> None:
    symbol = message.text.strip().upper()
    try:
        quote = await market_client.get_quote(symbol)
    except MarketAPIError as exc:
        await message.answer(
            f"Не удалось найти <b>{symbol}</b>.\nПричина: {exc}",
            parse_mode="HTML",
            reply_markup=back_keyboard(),
        )
        return

    await state.update_data(symbol=symbol, current_price=quote["price"])
    await message.answer(
        f"<b>{symbol}</b>\n"
        f"Текущая цена: <b>{quote['price']:.2f} {quote['currency']}</b>\n\n"
        f"Выберите направление алерта:",
        parse_mode="HTML",
        reply_markup=alert_direction_keyboard(symbol),
    )


@router.message(UserFlow.waiting_alert_price, F.text)
async def handle_alert_price(
    message: Message,
    state: FSMContext,
    db: Database,
) -> None:
    try:
        target_price = float(message.text.replace(",", ".").strip())
    except ValueError:
        await message.answer(
            "Введите цену числом, например <code>200</code> или <code>150.5</code>.",
            parse_mode="HTML",
            reply_markup=back_keyboard(),
        )
        return

    data = await state.get_data()
    symbol = data.get("symbol")
    direction = data.get("direction")
    if not symbol or not direction:
        await state.clear()
        await message.answer(
            "Создание алерта было сброшено. Попробуйте еще раз.",
            reply_markup=main_keyboard(),
        )
        return

    await db.upsert_user(message.from_user.id, message.from_user.username)
    alert_id = await db.add_alert(message.from_user.id, symbol, direction, target_price)
    await state.clear()
    direction_text = "выше" if direction == "above" else "ниже"
    await message.answer(
        f"<b>Алерт создан</b>\n"
        f"ID: <b>#{alert_id}</b>\n"
        f"{symbol} — цена {direction_text} <b>{target_price:.2f}</b>",
        parse_mode="HTML",
        reply_markup=main_keyboard(),
    )


@router.callback_query(F.data.startswith("price:show:"))
async def cb_show_price(callback: CallbackQuery, market_client: TwelveDataClient) -> None:
    symbol = callback.data.split(":")[-1].upper()
    try:
        await send_price_card(callback, market_client, symbol)
    except MarketAPIError as exc:
        await callback.message.answer(f"Не удалось получить цену для {symbol}: {exc}")
    await callback.answer()


@router.callback_query(F.data.startswith("ticker:add:"))
async def cb_add_ticker(callback: CallbackQuery, db: Database) -> None:
    symbol = callback.data.split(":")[-1].upper()
    await db.upsert_user(callback.from_user.id, callback.from_user.username)
    created = await db.add_ticker(callback.from_user.id, symbol)
    await callback.answer("Добавлено" if created else "Уже есть")
    await callback.message.answer(
        f"{symbol} добавлен в ваши тикеры." if created else f"{symbol} уже есть в ваших тикерах.",
        reply_markup=main_keyboard(),
    )


@router.callback_query(F.data.startswith("ticker:remove:"))
async def cb_remove_ticker(callback: CallbackQuery, db: Database) -> None:
    symbol = callback.data.split(":")[-1].upper()
    removed = await db.remove_ticker(callback.from_user.id, symbol)
    await callback.answer("Удалено" if removed else "Не найдено")
    await callback.message.edit_text(
        f"{symbol}\nУдален из вашего списка." if removed else f"{symbol}\nУже отсутствует в вашем списке."
    )


@router.callback_query(F.data.startswith("alert:create:"))
async def cb_start_alert(callback: CallbackQuery, state: FSMContext) -> None:
    symbol = callback.data.split(":")[-1].upper()
    await state.set_state(UserFlow.waiting_alert_price)
    await state.update_data(symbol=symbol)
    await callback.message.answer(
        f"Выберите направление алерта для <b>{symbol}</b>:",
        parse_mode="HTML",
        reply_markup=alert_direction_keyboard(symbol),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("alertdir:"))
async def cb_choose_alert_direction(callback: CallbackQuery, state: FSMContext) -> None:
    _, symbol, direction = callback.data.split(":")
    await state.set_state(UserFlow.waiting_alert_price)
    await state.update_data(symbol=symbol.upper(), direction=direction)
    await callback.message.answer(
        f"Введите целевую цену для <b>{symbol.upper()}</b>.",
        parse_mode="HTML",
        reply_markup=back_keyboard(),
    )
    await callback.answer()


@router.message(Command("price"))
async def cmd_price(message: Message, market_client: TwelveDataClient) -> None:
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer(
            "Не указан тикер.\nИспользуйте <code>/price AAPL</code>.",
            parse_mode="HTML",
            reply_markup=main_keyboard(),
        )
        return

    symbol = parts[1].strip().upper()
    try:
        await send_price_card(message, market_client, symbol)
    except MarketAPIError as exc:
        await message.answer(
            f"Не удалось получить цену для <b>{symbol}</b>.\nПричина: {exc}",
            parse_mode="HTML",
            reply_markup=main_keyboard(),
        )
