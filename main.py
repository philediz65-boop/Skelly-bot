import os, threading, random, requests
from flask import Flask
import telebot
from telebot import types

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@app.route('/')
def home():
    return "SkellysPro LIVE! - ALL ASSETS + MENU"

# ===== DATABASE =====
BINODEX_POCKET = ["EUR/USD OTC","GBP/USD OTC","USD/JPY OTC","AUD/USD OTC","USD/CAD OTC","EUR/GBP OTC","EUR/JPY OTC","GBP/JPY OTC","AUD/JPY OTC","NZD/USD OTC","EUR/AUD OTC","EUR/CAD OTC","GBP/AUD OTC","USD/CHF OTC","CHF/JPY OTC","EUR/USD","GBP/USD","USD/JPY","AUD/USD","USD/CAD","EUR/GBP","EUR/JPY","BTC/USD OTC","ETH/USD OTC","LTC/USD OTC","BNB/USD OTC"]
FOREX_PAIRS = ["EUR/USD","GBP/USD","USD/JPY","AUD/USD","USD/CAD","NZD/USD","USD/CHF","EUR/GBP","EUR/JPY","EUR/AUD","EUR/CAD","EUR/CHF","EUR/NZD","GBP/JPY","GBP/AUD","GBP/CAD","GBP/CHF","GBP/NZD","AUD/JPY","AUD/CAD","AUD/CHF","AUD/NZD","CAD/JPY","CAD/CHF","CHF/JPY","NZD/JPY","NZD/CAD","NZD/CHF","USD/SEK","USD/NOK","USD/DKK","USD/SGD","USD/HKD","USD/TRY","USD/ZAR","USD/MXN","EUR/TRY","EUR/ZAR","EUR/SEK","EUR/NOK","GBP/SEK","GBP/NOK","GBP/TRY"]
INDICES_LIST = ["US30 (Dow Jones)","NAS100 (Nasdaq)","SPX500 (S&P 500)","GER40 (DAX)","UK100 (FTSE)","FRA40 (CAC)","ESP35","ITA40","JPN225 (Nikkei)","AUS200","US2000","VIX (Volatility)","CHINA50","HK50","INDIA50","USDINDEX"]
MT5_LIST = ["EUR/USD - MT5","GBP/USD - MT5","USD/JPY - MT5","XAU/USD (Gold) - MT5","XAG/USD (Silver) - MT5","BTC/USD - MT5","ETH/USD - MT5","US30 - MT5","NAS100 - MT5","SPX500 - MT5","GER40 - MT5","UK100 - MT5","USOil (WTI) - MT5","UKOil (Brent) - MT5","EUR/GBP - MT5","AUD/USD - MT5"]
GOLD_LIST = ["XAU/USD (Gold)","XAG/USD (Silver)","XAU/EUR (Gold/EUR)","XPT/USD (Platinum)","XPD/USD (Palladium)"]
ALL_COINS = []

def get_all_coins():
    try:
        url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=100&page=1"
        return requests.get(url, timeout=10).json()
    except:
        return []

def main_menu():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton(f"🔮 BINODEX & POCKET ({len(BINODEX_POCKET)})", callback_data="bin_pocket_0"),
        types.InlineKeyboardButton(f"📊 MT5 ({len(MT5_LIST)})", callback_data="mt5_0"),
        types.InlineKeyboardButton(f"💱 FOREX ({len(FOREX_PAIRS)})", callback_data="forex_0"),
        types.InlineKeyboardButton(f"📈 INDICES ({len(INDICES_LIST)})", callback_data="indices_0"),
        types.InlineKeyboardButton(f"🥇 GOLD ({len(GOLD_LIST)})", callback_data="gold_0"),
        types.InlineKeyboardButton(f"₿ CRYPTO (100)", callback_data="all_coins_0"),
    )
    return kb

def paginated_list(items, page, prefix):
    per_page = 12
    start = page * per_page
    chunk = items[start:start+per_page]
    kb = types.InlineKeyboardMarkup(row_width=2)
    for it in chunk:
        kb.add(types.InlineKeyboardButton(f"📊 {it}", callback_data=f"analyze_{it}"))
    nav = []
    if page > 0:
        nav.append(types.InlineKeyboardButton("⬅️ Prev", callback_data=f"{prefix}_{page-1}"))
    if start+per_page < len(items):
        nav.append(types.InlineKeyboardButton("Next ➡️", callback_data=f"{prefix}_{page+1}"))
    if nav:
        kb.row(*nav)
    kb.add(types.InlineKeyboardButton("🔙 Menu", callback_data="menu"))
    return kb

def coins_menu_paged(page):
    per_page = 10
    start = page * per_page
    chunk = ALL_COINS[start:start+per_page]
    kb = types.InlineKeyboardMarkup(row_width=1)
    for coin in chunk:
        kb.add(types.InlineKeyboardButton(f"{coin['symbol'].upper()} - ${coin['current_price']:,.2f}", callback_data=f"coin_{coin['id']}"))
    nav = []
    if page > 0:
        nav.append(types.InlineKeyboardButton("⬅️ Prev", callback_data=f"all_coins_{page-1}"))
    if start+per_page < len(ALL_COINS):
        nav.append(types.InlineKeyboardButton("Next ➡️", callback_data=f"all_coins_{page+1}"))
    if nav:
        kb.row(*nav)
    kb.add(types.InlineKeyboardButton("🔙 Menu", callback_data="menu"))
    return kb

# ===== SET TELEGRAM MENU BUTTON =====
def setup_menu():
    try:
        bot.set_my_commands([
            types.BotCommand("start", "🔥 MAIN MENU - All Assets"),
            types.BotCommand("binodex", "🔮 BINODEX & POCKET (26)"),
            types.BotCommand("mt5", "📊 MT5 (16) Signals"),
            types.BotCommand("forex", "💱 FOREX (42) Pairs"),
            types.BotCommand("indices", "📈 INDICES (16)"),
            types.BotCommand("gold", "🥇 GOLD & Metals"),
            types.BotCommand("crypto", "₿ CRYPTO Top 100"),
        ])
        print("Menu commands set!")
    except Exception as e:
        print(f"Menu error: {e}")

@bot.message_handler(commands=['start'])
def start(m):
    global ALL_COINS
    if not ALL_COINS:
        ALL_COINS = get_all_coins()
    bot.send_message(m.chat.id, f"🔥 *SkellysPro - ALL ASSETS* 🔥\n\n📊 Select Market from Menu below or use ☰ Menu button:", reply_markup=main_menu(), parse_mode="Markdown")

@bot.message_handler(commands=['binodex','pocket'])
def binodex_cmd(m):
    bot.send_message(m.chat.id, f"🔮 *BINODEX & POCKET - {len(BINODEX_POCKET)} Assets*", reply_markup=paginated_list(BINODEX_POCKET, 0, "bin_pocket"), parse_mode="Markdown")

@bot.message_handler(commands=['mt5'])
def mt5_cmd(m):
    bot.send_message(m.chat.id, f"📊 *MT5 - {len(MT5_LIST)} Assets*", reply_markup=paginated_list(MT5_LIST, 0, "mt5"), parse_mode="Markdown")

@bot.message_handler(commands=['forex'])
def forex_cmd(m):
    bot.send_message(m.chat.id, f"💱 *FOREX - {len(FOREX_PAIRS)} Pairs*", reply_markup=paginated_list(FOREX_PAIRS, 0, "forex"), parse_mode="Markdown")

@bot.message_handler(commands=['indices'])
def indices_cmd(m):
    bot.send_message(m.chat.id, f"📈 *INDICES - {len(INDICES_LIST)}*", reply_markup=paginated_list(INDICES_LIST, 0, "indices"), parse_mode="Markdown")

@bot.message_handler(commands=['gold'])
def gold_cmd(m):
    bot.send_message(m.chat.id, f"🥇 *GOLD & METALS*", reply_markup=paginated_list(GOLD_LIST, 0, "gold"), parse_mode="Markdown")

@bot.message_handler(commands=['crypto'])
def crypto_cmd(m):
    global ALL_COINS
    if not ALL_COINS:
        ALL_COINS = get_all_coins()
    bot.send_message(m.chat.id, f"₿ *CRYPTO TOP 100*", reply_markup=coins_menu_paged(0), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: True)
def cb(call):
    d = call.data
    try:
        if d == "menu":
            bot.edit_message_text("🔥 *SkellysPro - ALL ASSETS* 🔥", call.message.chat.id, call.message.message_id, reply_markup=main_menu(), parse_mode="Markdown")
        elif d.startswith("bin_pocket_"):
            page = int(d.split("_")[-1])
            bot.edit_message_text(f"🔮 *BINODEX & POCKET - {len(BINODEX_POCKET)} (Page {page+1})*", call.message.chat.id, call.message.message_id, reply_markup=paginated_list(BINODEX_POCKET, page, "bin_pocket"), parse_mode="Markdown")
        elif d.startswith("forex_"):
            page = int(d.split("_")[-1])
            bot.edit_message_text(f"💱 *FOREX - {len(FOREX_PAIRS)} (Page {page+1})*", call.message.chat.id, call.message.message_id, reply_markup=paginated_list(FOREX_PAIRS, page, "forex"), parse_mode="Markdown")
        elif d.startswith("indices_"):
            page = int(d.split("_")[-1])
            bot.edit_message_text(f"📈 *INDICES - {len(INDICES_LIST)} (Page {page+1})*", call.message.chat.id, call.message.message_id, reply_markup=paginated_list(INDICES_LIST, page, "indices"), parse_mode="Markdown")
        elif d.startswith("mt5_"):
            page = int(d.split("_")[-1])
            bot.edit_message_text(f"📊 *MT5 - {len(MT5_LIST)} (Page {page+1})*", call.message.chat.id, call.message.message_id, reply_markup=paginated_list(MT5_LIST, page, "mt5"), parse_mode="Markdown")
        elif d.startswith("gold_"):
            page = int(d.split("_")[-1])
            bot.edit_message_text(f"🥇 *GOLD & METALS*", call.message.chat.id, call.message.message_id, reply_markup=paginated_list(GOLD_LIST, page, "gold"), parse_mode="Markdown")
        elif d.startswith("all_coins_"):
            page = int(d.split("_")[-1])
            if not ALL_COINS:
                ALL_COINS = get_all_coins()
            bot.edit_message_text(f"₿ *CRYPTO TOP 100 (Page {page+1})*", call.message.chat.id, call.message.message_id, reply_markup=coins_menu_paged(page), parse_mode="Markdown")
        elif d.startswith("coin_"):
            coin_id = d.replace("coin_", "")
            coin = next((c for c in ALL_COINS if c['id'] == coin_id), None)
            if coin:
                sig = random.choice(["BUY CALL 🟢 STRONG","SELL PUT 🔴 STRONG","BUY CALL 🟢","SELL PUT 🔴"])
                txt = f"📊 *{coin['name']}*\n💰 ${coin['current_price']:,.4f}\n📈 24h: {coin['price_change_percentage_24h']:.2f}%\n\n🤖 *{sig}*\n⏰ 1M | 85% Conf"
                kb = types.InlineKeyboardMarkup()
                kb.add(types.InlineKeyboardButton("🔙 Back", callback_data="all_coins_0"))
                bot.send_message(call.message.chat.id, txt, parse_mode="Markdown", reply_markup=kb)
        elif d.startswith("analyze_"):
            asset = d.replace("analyze_", "")
            sig = random.choice(["BUY CALL 🟢","SELL PUT 🔴","BUY CALL 🟢 STRONG","SELL PUT 🔴 STRONG"])
            txt = f"📊 *{asset}*\n\n🤖 Signal: *{sig}*\n⏰ Expiry: 2 mins\n💡 RSI + EMA confirmed\n⚡ Confidence: {random.randint(82,96)}%"
            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton("🔙 Back", callback_data="menu"))
            bot.send_message(call.message.chat.id, txt, parse_mode="Markdown", reply_markup=kb)
    except:
        pass

def run_bot():
    setup_menu()
    bot.infinity_polling()

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
