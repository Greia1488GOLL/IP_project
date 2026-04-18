from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

PRICE_BUTTON = "Price"
TICKERS_BUTTON = "My tickers"
ADD_TICKER_BUTTON = "Add ticker"
ALERTS_BUTTON = "My alerts"
CREATE_ALERT_BUTTON = "Create alert"
HELP_BUTTON = "Help"
BACK_BUTTON = "Back"


def main_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=PRICE_BUTTON),
                KeyboardButton(text=TICKERS_BUTTON),
            ],
            [
                KeyboardButton(text=ADD_TICKER_BUTTON),
                KeyboardButton(text=ALERTS_BUTTON),
            ],
            [
                KeyboardButton(text=CREATE_ALERT_BUTTON),
                KeyboardButton(text=HELP_BUTTON),
            ],
        ],
        resize_keyboard=True,
        input_field_placeholder="Choose an action",
    )


def back_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=BACK_BUTTON)]],
        resize_keyboard=True,
        input_field_placeholder="Enter value or press Back",
    )


def price_result_keyboard(symbol: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Add to tickers",
                    callback_data=f"ticker:add:{symbol}",
                ),
                InlineKeyboardButton(
                    text="Create alert",
                    callback_data=f"alert:create:{symbol}",
                ),
            ]
        ]
    )


def ticker_actions_keyboard(symbol: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Show price",
                    callback_data=f"price:show:{symbol}",
                ),
                InlineKeyboardButton(
                    text="Create alert",
                    callback_data=f"alert:create:{symbol}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Remove ticker",
                    callback_data=f"ticker:remove:{symbol}",
                ),
            ],
        ]
    )


def alert_direction_keyboard(symbol: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="When above",
                    callback_data=f"alertdir:{symbol}:above",
                ),
                InlineKeyboardButton(
                    text="When below",
                    callback_data=f"alertdir:{symbol}:below",
                ),
            ]
        ]
    )


def alert_remove_keyboard(alert_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Remove alert",
                    callback_data=f"alert:remove:{alert_id}",
                ),
            ]
        ]
    )
