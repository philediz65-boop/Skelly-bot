import os
import yfinance as yf
import pandas as pd
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

def get_rsi(close, period=14):
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Skelly-bot don wake! Use /trade BTCUSD or /trade EURUSD")

async def trade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Use like this: /trade BTCUSD")
        return
    symbol = context.args[0].upper()
    ticker = f"{symbol}-USD" if len(symbol) <= 6 and "=" not in symbol else symbol

    try:
        await update.message.reply_text(f"⏳ Checking {symbol}...")
        data = yf.download(ticker, period="5d", interval="1h", progress=False)
        if data.empty:
            await update.message.reply_text(f"❌ No data for {symbol}")
            return

        close = data['Close']
        rsi = get_rsi(close).iloc[-1]
        ema9 = close.ewm(span=9, adjust=False).mean().iloc[-1]
        ema21 = close.ewm(span=21, adjust=False).mean().iloc[-1]
        price = close.iloc[-1]

        if ema9 > ema21 and rsi > 50:
            trend = "BUY 🟢"
        elif ema9 < ema21 and rsi < 50:
            trend = "SELL 🔴"
        else:
            trend = "WAIT 🟡"

        msg = f"📊 *{symbol} Analysis*\nPrice: ${float(price):.2f}\n\nRSI: {float(rsi):.2f}\nEMA9: {float(ema9):.2f}\nEMA21: {float(ema21):.2f}\n\nSignal: *{trend}*"
        await update.message.reply_text(msg, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("trade", trade))
    app.run_polling()

if __name__ == "__main__":
    main()
