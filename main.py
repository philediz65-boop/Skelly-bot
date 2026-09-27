import os
from flask import Flask
from threading import Thread
import yfinance as yf
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BOT_TOKEN = os.environ.get("BOT_TOKEN")

app = Flask('')
@app.route('/')
def home():
    return "Bot is alive!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Skelly Bot is online! Use /price BTC")

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Use: /price BTC or /price AAPL")
        return
    symbol = context.args[0].upper()
    try:
        # Add -USD for crypto if needed
        ticker = symbol if "-" in symbol or symbol in ["BTC", "ETH", "SOL"] else symbol
        if ticker in ["BTC", "ETH", "SOL"]:
            ticker = f"{ticker}-USD"
        data = yf.Ticker(ticker)
        price_val = data.history(period="1d")['Close'].iloc[-1]
        await update.message.reply_text(f"{symbol}: ${price_val:.2f}")
    except Exception as e:
        await update.message.reply_text(f"Could not get price for {symbol}")

def main():
    Thread(target=run_flask).start()
    app_bot = ApplicationBuilder().token(BOT_TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("price", price))
    print("Bot started...")
    app_bot.run_polling()

if __name__ == "__main__":
    main()
