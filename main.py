import yfinance as yf
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = "ВСТАВЬ_СЮДА_ТОКЕН_БОТА"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📈 Привет! Отправь тикер акции.\nПример: AAPL или TSLA"
    )


async def get_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ticker = update.message.text.upper()

    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period="1d")

        if data.empty:
            await update.message.reply_text("❌ Тикер не найден")
            return

        price = data["Close"].iloc[-1]
        open_price = data["Open"].iloc[-1]
        change = price - open_price
        percent = (change / open_price) * 100

        message = (
            f"📊 {ticker}\n"
            f"Цена: ${price:.2f}\n"
            f"Изменение: {change:+.2f} ({percent:+.2f}%)"
        )

        await update.message.reply_text(message)

    except Exception as e:
        await update.message.reply_text("⚠ Ошибка получения данных")


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, get_stock))

    print("✅ Бот запущен...")
    app.run_polling()


if __name__ == "__main__":
    main()