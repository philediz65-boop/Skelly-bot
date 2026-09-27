from flask import Flask
import os
import threading
import yfinance as yf
import pandas as pd
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

app = Flask(__name__)
@app.route('/')
def home():
    return "Skelly Bot is Alive - 24/7"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

threading.Thread(target=run_web, daemon=True).start()

def get_rsi(close, period=14):
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Yo! Skelly-bot Live 24/7 🤖\nSend ticker: BTC-USD, AAPL")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ticker = update.message.text.strip().upper()
    try:
        data = yf.download(ticker, period="3mo", interval="1d", progress=False)
        if data.empty:
            await update.message.reply_text(f"No data for {ticker}")
            return
        close = data['Close']
        last_rsi = get_rsi(close).iloc[-1]
        price = close.iloc[-1]
        signal = "🔴 OVERBOUGHT" if last_rsi > 70 else "🟢 OVERSOLD" if last_rsi < 30 else "🟡 NEUTRAL"
        await update.message.reply_text(f"📊 {ticker}\nPrice: ${float(price):.2f}\nRSI: {float(last_rsi):.2f}\n{signal}")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling()

if __name__ == "__main__":
    main()
