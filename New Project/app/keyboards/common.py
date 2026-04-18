from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

PRICE_BUTTON = "Узнать цену"
TICKERS_BUTTON = "Мои тикеры"
ADD_TICKER_BUTTON = "Добавить тикер"
ALERTS_BUTTON = "Мои алерты"
CREATE_ALERT_BUTTON = "Создать алерт"
HELP_BUTTON = "Помощь"
BACK_BUTTON = "Назад"


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
        input_field_placeholder="Выберите действие",
    )


def back_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=BACK_BUTTON)]],
        resize_keyboard=True,
        input_field_placeholder="Введите значение или нажмите Назад",
    )


def price_result_keyboard(symbol: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Добавить в тикеры",
                    callback_data=f"ticker:add:{symbol}",
                ),
                InlineKeyboardButton(
                    text="Создать алерт",
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
                    text="Показать цену",
                    callback_data=f"price:show:{symbol}",
                ),
                InlineKeyboardButton(
                    text="Создать алерт",
                    callback_data=f"alert:create:{symbol}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Удалить тикер",
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
                    text="Когда выше",
                    callback_data=f"alertdir:{symbol}:above",
                ),
                InlineKeyboardButton(
                    text="Когда ниже",
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
                    text="Удалить алерт",
                    callback_data=f"alert:remove:{alert_id}",
                ),
            ]
        ]
    )
