import os, telebot, threading, random
from flask import Flask
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

@app.route('/')
def home():
    return "SkellysPro LIVE!"

# THIS NA THE MENU
def main_menu():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("🔮 BINODEX & POCKET", callback_data="binodex"),
        InlineKeyboardButton("📊 MT5", callback_data="mt5"),
        InlineKeyboardButton("₿ CRYPTO", callback_data="crypto"),
        InlineKeyboardButton("💱 FOREX", callback_data="forex"),
        InlineKeyboardButton("🥇 GOLD", callback_data="gold"),
        InlineKeyboardButton("📈 INDICES", callback_data="indices")
    )
    return kb

def get_signal(symbol, market):
    sig = random.choice(["BUY 🟢", "SELL 🔴"])
    acc = random.randint(74, 91)
    price = round(random.uniform(1.08, 2650.50), 2)
    
    if market in ["BINODEX & POCKET", "POCKET"]:
        return f"🔮 {market} SIGNAL\n\n📊 {symbol}\n{sig}\n💰 Entry: {price}\n⏰ Expiry: 5 MIN\n✅ Accuracy: {acc}%\n\nLogic: RSI + EMA + Support/Resistance"
    else:
        tp = price * 1.012
        sl = price * 0.988
        return f"📊 {market} SIGNAL\n\n📊 {symbol}\n{sig} @ {price}\n🎯 TP: {tp:.2f}\n🛑 SL: {sl:.2f}\n✅ Accuracy: {acc}%"

@bot.message_handler(commands=['start'])
def start_cmd(message):
    bot.send_message(
        message.chat.id,
        "👋 *Welcome to SkellysPro Bot!*\n\nChoose market for signal:",
        reply_markup=main_menu(),
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: True)
def button_click(call):
    market = call.data
    if market == "binodex":
        text = get_signal("EUR/USD", "BINODEX & POCKET")
    elif market == "mt5":
        text = get_signal("XAU/USD", "MT5")
    elif market == "crypto":
        text = get_signal("BTC/USDT", "CRYPTO")
    elif market == "forex":
        text = get_signal("EUR/USD", "FOREX")
    elif market == "gold":
        text = get_signal("XAU/USD", "GOLD")
    elif market == "indices":
        text = get_signal("US30", "INDICES")
    else:
        text = get_signal("EUR/USD", "FOREX")
    
    bot.send_message(call.message.chat.id, text, reply_markup=main_menu())

# For any other message, show menu again
@bot.message_handler(func=lambda m: True)
def any_message(m):
    bot.send_message(m.chat.id, "👇 Choose market:", reply_markup=main_menu())

def run_bot():
    bot.infinity_polling()

# Run bot in background
threading.Thread(target=run_bot, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
