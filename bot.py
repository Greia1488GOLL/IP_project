import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters
)
from telegram.constants import ParseMode
import requests
import json

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Ваш токен от BotFather
BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"

# Популярные акции (только международные)
POPULAR_STOCKS = {
    "💻 Tech": ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "AMD", "INTC", "CSCO"],
    "🏦 Finance": ["JPM", "BAC", "WFC", "GS", "V", "MA", "PYPL", "AXP", "BLK", "SCHW"],
    "🏥 Healthcare": ["JNJ", "PFE", "MRK", "ABT", "TMO", "UNH", "LLY", "AMGN", "GILD", "BMY"],
    "⚡ Energy": ["XOM", "CVX", "COP", "SLB", "EOG", "PSX", "MPC", "VLO", "OXY", "DVN"],
    "🛒 Consumer": ["WMT", "PG", "KO", "PEP", "COST", "MCD", "NKE", "SBUX", "TGT", "HD"]
}

class StockAPI:
    """Простой класс для работы с API акций"""
    
    @staticmethod
    def get_stock_price(symbol):
        """Получает цену акции через Yahoo Finance API"""
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            data = response.json()
            
            if 'chart' in data and 'result' in data['chart'] and data['chart']['result']:
                result = data['chart']['result'][0]
                meta = result['meta']
                
                return {
                    'success': True,
                    'symbol': symbol,
                    'price': meta.get('regularMarketPrice', 0),
                    'change': meta.get('regularMarketChange', 0),
                    'change_percent': meta.get('regularMarketChangePercent', 0),
                    'high': meta.get('regularMarketDayHigh', 0),
                    'low': meta.get('regularMarketDayLow', 0),
                    'open': meta.get('regularMarketOpen', 0),
                    'volume': meta.get('regularMarketVolume', 0),
                    'currency': meta.get('currency', 'USD'),
                    'name': meta.get('shortName', symbol)
                }
            
            return {'success': False, 'error': 'No data found'}
            
        except Exception as e:
            logger.error(f"API Error: {e}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_multiple_prices(symbols):
        """Получает цены для нескольких акций"""
        results = {}
        for symbol in symbols:
            data = StockAPI.get_stock_price(symbol)
            if data['success']:
                results[symbol] = data
        return results

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    user = update.effective_user
    
    welcome_text = f"""
👋 Привет, {user.first_name}!

📈 *Stock Price Bot* - простой бот для отслеживания акций

*Как использовать:*
1. Отправьте тикер акции (например: `AAPL`, `TSLA`, `GOOGL`)
2. Используйте кнопки ниже для быстрого доступа
3. Или введите команду `/price <тикер>`

*Примеры:*
• `AAPL` - Apple
• `MSFT` - Microsoft
• `TSLA` - Tesla
• `AMZN` - Amazon

Для помощи введите `/help`
"""
    
    keyboard = [
        [InlineKeyboardButton("📊 Популярные акции", callback_data="popular")],
        [InlineKeyboardButton("🔍 Поиск", callback_data="search")],
        [InlineKeyboardButton("❓ Помощь", callback_data="help")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        welcome_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=reply_markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help"""
    help_text = """
*📚 Помощь по использованию*

*Основные команды:*
/start - Начало работы
/price <тикер> - Цена акции
/list - Список акций
/help - Эта справка

*Как использовать:*
Просто отправьте тикер акции:
• `AAPL` для Apple
• `MSFT` для Microsoft
• `TSLA` для Tesla
• `GOOGL` для Google
• `AMZN` для Amazon
• `META` для Facebook
• `NVDA` для NVIDIA

*Что показывается:*
• Текущая цена
• Изменение за день
• Максимум/минимум дня
• Объем торгов
• Валюта

*Источник данных:* Yahoo Finance
"""
    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /price"""
    if context.args:
        symbol = context.args[0].upper()
        await get_stock_price(update, context, symbol)
    else:
        await update.message.reply_text(
            "Введите тикер акции после команды. Пример: `/price AAPL`",
            parse_mode=ParseMode.MARKDOWN
        )

async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /list - показывает популярные акции"""
    await show_popular_stocks(update, context)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик обычных сообщений"""
    text = update.message.text.strip().upper()
    
    # Проверяем, похоже ли на тикер акции (1-5 букв)
    if 1 <= len(text) <= 5 and text.isalpha():
        await get_stock_price(update, context, text)
    else:
        await update.message.reply_text(
            "Отправьте тикер акции (например: AAPL, TSLA, MSFT) или используйте команду /help"
        )

async def get_stock_price(update: Update, context: ContextTypes.DEFAULT_TYPE, symbol: str):
    """Получает и отображает цену акции"""
    message = await update.message.reply_text(f"🔄 Запрашиваю данные для *{symbol}*...", 
                                             parse_mode=ParseMode.MARKDOWN)
    
    data = StockAPI.get_stock_price(symbol)
    
    if not data['success']:
        await message.edit_text(f"❌ Не удалось получить данные для *{symbol}*\n\nПроверьте правильность тикера.")
        return
    
    # Форматируем сообщение
    price = data['price']
    change = data['change']
    change_percent = data['change_percent']
    
    # Выбираем эмодзи для изменения цены
    if change > 0:
        trend = "📈"
        change_text = f"🟢 +${abs(change):.2f} (+{abs(change_percent):.2f}%)"
    elif change < 0:
        trend = "📉"
        change_text = f"🔴 -${abs(change):.2f} (-{abs(change_percent):.2f}%)"
    else:
        trend = "➡️"
        change_text = f"⚪ ${change:.2f} ({change_percent:.2f}%)"
    
    message_text = f"""
{trend} *{data['name']}* ({symbol})

💰 *Цена:* ${price:.2f} {data['currency']}
📊 *Изменение:* {change_text}

📈 *Дневной диапазон:*
• Макс: ${data['high']:.2f}
• Мин: ${data['low']:.2f}
• Открытие: ${data['open']:.2f}

📊 *Объем:* {data['volume']:,}

⏰ *Время:* {datetime.now().strftime('%H:%M:%S')}
"""
    
    # Создаем кнопки
    keyboard = [
        [InlineKeyboardButton("🔄 Обновить", callback_data=f"refresh_{symbol}")],
        [InlineKeyboardButton("📋 Другие акции", callback_data="popular")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await message.edit_text(message_text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)

async def show_popular_stocks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает популярные акции"""
    text = "📊 *Популярные акции*\n\nВыберите категорию:"
    
    keyboard = []
    for category, stocks in POPULAR_STOCKS.items():
        keyboard.append([InlineKeyboardButton(category, callback_data=f"cat_{category}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
    else:
        await update.callback_query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)

async def show_category_stocks(query, category):
    """Показывает акции в категории"""
    stocks = POPULAR_STOCKS.get(category, [])
    
    if not stocks:
        await query.edit_message_text("Категория не найдена")
        return
    
    # Получаем цены для всех акций в категории
    prices_data = StockAPI.get_multiple_prices(stocks[:6])  # Берем первые 6
    
    text = f"📊 *{category}*\n\n"
    
    for symbol, data in prices_data.items():
        if data['success']:
            change_emoji = "🟢" if data['change'] > 0 else "🔴" if data['change'] < 0 else "⚪"
            text += f"{change_emoji} *{symbol}*: ${data['price']:.2f} ({data['change']:+.2f})\n"
    
    # Кнопки для выбора акций
    keyboard = []
    row = []
    for i, symbol in enumerate(stocks[:6], 1):
        row.append(InlineKeyboardButton(symbol, callback_data=f"price_{symbol}"))
        if i % 3 == 0:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="popular")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатий на кнопки"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "popular":
        await show_popular_stocks(update, context)
    
    elif data == "search":
        await query.edit_message_text("Введите тикер акции для поиска (например: AAPL, TSLA):")
    
    elif data == "help":
        await help_command(update, context)
    
    elif data.startswith("cat_"):
        category = data[4:]
        await show_category_stocks(query, category)
    
    elif data.startswith("price_"):
        symbol = data[6:]
        await show_single_stock(query, symbol)
    
    elif data.startswith("refresh_"):
        symbol = data[8:]
        await refresh_stock_price(query, symbol)

async def show_single_stock(query, symbol):
    """Показывает информацию об одной акции"""
    message = await query.edit_message_text(f"🔄 Загружаю {symbol}...")
    
    data = StockAPI.get_stock_price(symbol)
    
    if not data['success']:
        await query.edit_message_text(f"❌ Ошибка загрузки {symbol}")
        return
    
    # Форматируем как в get_stock_price
    price = data['price']
    change = data['change']
    change_percent = data['change_percent']
    
    if change > 0:
        trend = "📈"
        change_text = f"🟢 +${abs(change):.2f} (+{abs(change_percent):.2f}%)"
    elif change < 0:
        trend = "📉"
        change_text = f"🔴 -${abs(change):.2f} (-{abs(change_percent):.2f}%)"
    else:
        trend = "➡️"
        change_text = f"⚪ ${change:.2f} ({change_percent:.2f}%)"
    
    message_text = f"""
{trend} *{data['name']}* ({symbol})

💰 *Цена:* ${price:.2f} {data['currency']}
📊 *Изменение:* {change_text}

📈 *Дневной диапазон:*
• Макс: ${data['high']:.2f}
• Мин: ${data['low']:.2f}
• Открытие: ${data['open']:.2f}

📊 *Объем:* {data['volume']:,}

⏰ *Время:* {datetime.now().strftime('%H:%M:%S')}
"""
    
    keyboard = [
        [InlineKeyboardButton("🔄 Обновить", callback_data=f"refresh_{symbol}")],
        [InlineKeyboardButton("📋 Другие акции", callback_data="popular")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(message_text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)

async def refresh_stock_price(query, symbol):
    """Обновляет цену акции"""
    await show_single_stock(query, symbol)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error(f"Ошибка: {context.error}")
    
    if update and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "❌ Произошла ошибка. Пожалуйста, попробуйте позже."
            )
        except:
            pass

def main():
    """Запуск бота"""
    # Создаем приложение
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Добавляем обработчики команд
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("price", price_command))
    app.add_handler(CommandHandler("list", list_command))
    
    # Обработчик кнопок
    app.add_handler(CallbackQueryHandler(button_handler))
    
    # Обработчик текстовых сообщений
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Обработчик ошибок
    app.add_error_handler(error_handler)
    
    # Запускаем бота
    print("🤖 Бот запущен...")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()