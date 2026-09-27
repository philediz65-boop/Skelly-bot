import os
import yfinance as yf
import pandas_ta as ta
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Skelly-bot don wake! Use /trade BTCUSD or /trade EURUSD")

async def trade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Use like this: /trade BTCUSD")
        return

    symbol = context.args[0].upper()
    # add -USD for crypto
    ticker = symbol if "=" in symbol else f"{symbol}-USD" if len(symbol) <= 6 else symbol

    try:
        await update.message.reply_text(f"⏳ Checking {symbol}...")
        data = yf.download(ticker, period="2d", interval="15m", progress=False)
        if data.empty:
            data = yf.download(symbol, period="2d", interval="1h", progress=False)

        if data.empty:
            await update.message.reply_text(f"❌ No data for {symbol}")
            return

        close = data['Close']
        rsi = ta.rsi(close, length=14).iloc[-1]
        ema_fast = ta.ema(close, length=9).iloc[-1]
        ema_slow = ta.ema(close, length=21).iloc[-1]

        price = close.iloc[-1]
        trend = "BUY 🟢" if ema_fast > ema_slow and rsi > 50 else "SELL 🔴" if ema_fast < ema_slow and rsi < 50 else "WAIT 🟡"

        msg = f"""📊 *{symbol} Analysis*
Price: ${float
