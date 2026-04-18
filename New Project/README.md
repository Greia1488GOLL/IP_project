# Finance Telegram Bot

Простой, но масштабируемый Telegram-бот на `aiogram` для:

- получения текущих цен акций;
- отслеживания пользовательских тикеров;
- создания и удаления price alerts;
- хранения данных в SQLite.

Для получения котировок используется публичный endpoint Stooq, поэтому отдельный ключ рыночного API не нужен.

## Краткий план архитектуры

1. `main.py`
   Точка входа: инициализация бота, роутеров, базы данных и фоновой проверки алертов.
2. `app/config.py`
   Загрузка настроек из `.env`.
3. `app/database.py`
   Работа с SQLite: пользователи, тикеры, алерты.
4. `app/services/market_data.py`
   Клиент внешнего API котировок.
5. `app/services/alerts.py`
   Фоновая проверка price alerts и отправка уведомлений.
6. `app/handlers/*.py`
   Команды Telegram.
7. `app/keyboards/common.py`
   Базовая клавиатура с быстрыми действиями.

## Структура проекта

```text
.
├── .env
├── .env.example
├── README.md
├── main.py
├── requirements.txt
└── app
    ├── __init__.py
    ├── config.py
    ├── database.py
    ├── keyboards
    │   ├── __init__.py
    │   └── common.py
    ├── handlers
    │   ├── __init__.py
    │   ├── alerts.py
    │   ├── common.py
    │   └── tickers.py
    └── services
        ├── __init__.py
        ├── alerts.py
        └── market_data.py
```

## Установка

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Настройка

В проект уже добавлен файл `.env`. Нужно только заменить значение:

```env
BOT_TOKEN=paste_your_bot_token_here
```

Остальные параметры уже готовы:

```env
DATABASE_PATH=bot.db
ALERT_CHECK_INTERVAL=60
```

## Запуск

```bash
python main.py
```

## Команды бота

- `/start` - приветствие и список команд
- `/help` - помощь
- `/price AAPL` - текущая цена
- `/addticker AAPL` - добавить тикер в отслеживание
- `/removeticker AAPL` - удалить тикер
- `/mytickers` - показать отслеживаемые тикеры
- `/setalert AAPL above 200` - создать алерт
- `/setalert AAPL below 180` - создать алерт
- `/alerts` - список алертов
- `/removealert 1` - удалить алерт по ID

## Что осталось сделать

1. Получить токен у BotFather.
2. Вставить его в `.env`.
3. Установить зависимости.
4. Запустить `python main.py`.

## Идеи для расширения

- inline-кнопки и меню;
- FSM для пошагового создания алертов;
- кэширование цен;
- поддержка нескольких провайдеров рынка;
- переход на PostgreSQL для production.
