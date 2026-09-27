import os
from flask import Flask
from threading import Thread
import yfinance as yf
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BOT_TOKEN = os.environ.get("BOT_TOKEN")

if not BOT_TOKEN:
    print("ERROR: BOT_TOKEN not set!")
    
app = Flask(__name__)

@app.route('/')
def home():
    return "Skelly Bot is alive! 💀"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Skelly is live! 💀 Send me a stock symbol.")

def run_bot():
    print("Bot started polling...")
    app_bot = ApplicationBuilder().token(BOT_TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.run_polling()

if __name__ == "__main__":
    # Bot in background thread
    Thread(target=run_bot, daemon=True).start()
    
    # Flask in MAIN thread - Render will see port immediately
    port = int(os.environ.get("PORT", 10000))
    print(f"Starting Flask on port {port}")
    app.run(host='0.0.0.0', port=port)
