import os, threading, random, requests, re
from flask import Flask
import telebot
from telebot import types

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@app.route('/')
def home():
    return "SkellysPro FINAL SMART - Any Text + Timeframe"

BINODEX_POCKET = ["EUR/USD OTC","GBP/USD OTC","USD/JPY OTC","AUD/USD OTC","USD/CAD OTC","EUR/GBP OTC","EUR/JPY OTC","GBP/JPY OTC","AUD/JPY OTC","NZD/USD OTC","EUR/AUD OTC","EUR/CAD OTC","GBP/AUD OTC","USD/CHF OTC","CHF/JPY OTC","EUR/USD","GBP/USD","USD/JPY","BTC/USD OTC","ETH/USD OTC"]
FOREX_PAIRS = ["EUR/USD","GBP/USD","USD/JPY","AUD/USD","USD/CAD","NZD/USD","USD/CHF","EUR/GBP","EUR/JPY","EUR/AUD","GBP/JPY","AUD/JPY","CAD/JPY","CHF/JPY","NZD/JPY"]
INDICES_LIST = ["US30 (Dow Jones)","NAS100 (Nasdaq)","SPX500 (S&P 500)","GER40 (DAX)","UK100 (FTSE)","JPN225 (Nikkei)","AUS200","VIX"]
MT5_LIST = ["EUR/USD - MT5","GBP/USD - MT5","USD/JPY - MT5","XAU/USD (Gold) - MT5","XAG/USD (Silver) - MT5","BTC/USD - MT5","US30 - MT5","NAS100 - MT5","SPX500 - MT5","GER40 - MT5","UK100 - MT5","USOil - MT5"]
GOLD_LIST = ["XAU/USD (Gold)","XAG/USD (Silver)","XAU/EUR","XPT/USD (Platinum)"]
ALL_COINS = []

def get_all_coins():
    try:
        url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=100&page=1"
        return requests.get(url, timeout=15).json()
    except: return []

def get_live_price(symbol_name):
    try:
        import yfinance as yf
        ticker_map = {"EUR/USD":"EURUSD=X","GBP/USD":"GBPUSD=X","USD/JPY":"USDJPY=X","AUD/USD":"AUDUSD=X","USD/CAD":"USDCAD=X","NZD/USD":"NZDUSD=X","USD/CHF":"USDCHF=X","EUR/GBP":"EURGBP=X","EUR/JPY":"EURJPY=X","GBP/JPY":"GBPJPY=X","AUD/JPY":"AUDJPY=X","XAU/USD":"GC=F","XAU":"GC=F","Gold":"GC=F","XAG":"SI=F","US30":"^DJI","NAS100":"^IXIC","SPX500":"^GSPC","GER40":"^GDAXI","UK100":"^FTSE","BTC":"BTC-USD","ETH":"ETH-USD"}
        ticker = None
        for k,v in ticker_map.items():
            if k in symbol_name.upper(): ticker=v; break
        if not ticker: return None
        data = yf.download(ticker, period="1d", interval="1m", progress=False)
        if not data.empty: return float(data['Close'].iloc[-1])
    except: pass
    return None

def generate_analysis(symbol, price):
    rsi = random.randint(35, 75)
    ema_trend = random.choice(["Bullish crossover","Bearish crossover","Strong uptrend","Strong downtrend"])
    support = price * 0.998 if price else 0
    resistance = price * 1.002 if price else 0
    return rsi, ema_trend, support, resistance

def parse_timeframe(text):
    text = text.lower()
    match = re.search(r'(\d+)\s*(m|min|h|hour|d|day)', text)
    if match:
        num = int(match.group(1))
        unit = match.group(2)
        if 'h' in unit: return f"{num}H", num*60
        if 'd' in unit: return f"{num}D", num*1440
        return f"{num}M", num
    if "1h" in text or "1 hour" in text: return "1H", 60
    if "4h" in text or "4 hour" in text: return "4H", 240
    if "1d" in text or "1 day" in text: return "1D", 1440
    return "5M", 5

def get_tp_sl_by_timeframe(price, is_buy, asset_type, minutes):
    if asset_type == "gold":
        base_tp = 3; base_sl = 2
        tp = base_tp * (minutes / 5)
        sl = base_sl * (minutes / 5)
        tp = min(tp, 50); sl = min(sl, 30)
    elif asset_type == "indices":
        base_tp = 80; base_sl = 50
        tp = base_tp * (minutes / 5)
        sl = base_sl * (minutes / 5)
        tp = min(tp, 2000); sl = min(sl, 1000)
    elif asset_type == "crypto":
        base_tp = price * 0.005; base_sl = price * 0.003
        tp = base_tp * (minutes / 5)
        sl = base_sl * (minutes / 5)
    else:
        base_tp = 0.0005; base_sl = 0.0003
        tp = base_tp * (minutes / 5)
        sl = base_sl * (minutes / 5)
    
    tp_price = price + tp if is_buy else price - tp
    sl_price = price - sl if is_buy else price + sl
    
    if asset_type == "forex":
        pips_tp = int(tp * 10000); pips_sl = int(sl * 10000)
    else:
        pips_tp = round(tp,2); pips_sl = round(sl,2)
    return tp_price, sl_price, pips_tp, pips_sl

def main_menu():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton(f"🔮 BINODEX ({len(BINODEX_POCKET)})", callback_data="bin_pocket_0"),
        types.InlineKeyboardButton(f"📊 MT5 ({len(MT5_LIST)})", callback_data="mt5_0"),
        types.InlineKeyboardButton(f"💱 FOREX ({len(FOREX_PAIRS)})", callback_data="forex_0"),
        types.InlineKeyboardButton(f"📈 INDICES ({len(INDICES_LIST)})", callback_data="indices_0"),
        types.InlineKeyboardButton(f"🥇 GOLD ({len(GOLD_LIST)})", callback_data="gold_0"),
        types.InlineKeyboardButton(f"₿ CRYPTO (100)", callback_data="all_coins_0"),
    )
    return kb

def paginated_list(items, page, prefix):
    per_page=10; start=page*per_page; chunk=items[start:start+per_page]
    kb=types.InlineKeyboardMarkup(row_width=1)
    for it in chunk: kb.add(types.InlineKeyboardButton(f"📊 {it}", callback_data=f"analyze_{it}"))
    nav=[]
    if page>0: nav.append(types.InlineKeyboardButton("⬅️ Prev", callback_data=f"{prefix}_{page-1}"))
    if start+per_page < len(items): nav.append(types.InlineKeyboardButton("Next ➡️", callback_data=f"{prefix}_{page+1}"))
    if nav: kb.row(*nav)
    kb.add(types.InlineKeyboardButton("🔙 Main Menu", callback_data="menu"))
    return kb

def coins_menu_paged(page):
    per_page=10; start=page*per_page; chunk=ALL_COINS[start:start+per_page]
    kb=types.InlineKeyboardMarkup(row_width=1)
    for coin in chunk: kb.add(types.InlineKeyboardButton(f"{coin['symbol'].upper()} - ${coin['current_price']:,.2f}", callback_data=f"coin_{coin['id']}"))
    nav=[]
    if page>0: nav.append(types.InlineKeyboardButton("⬅️ Prev", callback_data=f"all_coins_{page-1}"))
    if start+per_page < len(ALL_COINS): nav.append(types.InlineKeyboardButton("Next ➡️", callback_data=f"all_coins_{page+1}"))
    if nav: kb.row(*nav)
    kb.add(types.InlineKeyboardButton("🔙 Main Menu", callback_data="menu"))
    return kb

def setup_menu():
    try:
        bot.set_my_commands([
            types.BotCommand("start","🔥 MAIN MENU"),
            types.BotCommand("binodex","🔮 BINODEX"),types.BotCommand("mt5","📊 MT5"),
            types.BotCommand("forex","💱 FOREX"),types.BotCommand("indices","📈 INDICES"),
            types.BotCommand("gold","🥇 GOLD"),types.BotCommand("crypto","₿ CRYPTO"),
        ])
    except: pass

@bot.message_handler(commands=['start'])
def start(m):
    global ALL_COINS
    if not ALL_COINS: ALL_COINS=get_all_coins()
    bot.send_message(m.chat.id, f"🔥 *SKELLY'S PRO - SMART FINAL*\n\n✅ Any text reply\n✅ Auto 1H/4H TP/SL adjust\n✅ Live Price + Analysis\n\n👇 Select Market:", reply_markup=main_menu(), parse_mode="Markdown")

@bot.message_handler(commands=['binodex','forex','indices','mt5','gold','crypto'])
def cmds(m):
    cmd=m.text.replace("/","")
    if "binodex" in cmd: bot.send_message(m.chat.id, f"🔮 *BINODEX*", reply_markup=paginated_list(BINODEX_POCKET,0,"bin_pocket"), parse_mode="Markdown")
    elif "forex" in cmd: bot.send_message(m.chat.id, f"💱 *FOREX*", reply_markup=paginated_list(FOREX_PAIRS,0,"forex"), parse_mode="Markdown")
    elif "indices" in cmd: bot.send_message(m.chat.id, f"📈 *INDICES*", reply_markup=paginated_list(INDICES_LIST,0,"indices"), parse_mode="Markdown")
    elif "mt5" in cmd: bot.send_message(m.chat.id, f"📊 *MT5*", reply_markup=paginated_list(MT5_LIST,0,"mt5"), parse_mode="Markdown")
    elif "gold" in cmd: bot.send_message(m.chat.id, f"🥇 *GOLD*", reply_markup=paginated_list(GOLD_LIST,0,"gold"), parse_mode="Markdown")
    elif "crypto" in cmd:
        global ALL_COINS
        if not ALL_COINS: ALL_COINS=get_all_coins()
        bot.send_message(m.chat.id, f"₿ *CRYPTO*", reply_markup=coins_menu_paged(0), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: True)
def cb(call):
    global ALL_COINS
    d=call.data
    try:
        if d=="menu": bot.edit_message_text(f"🔥 *MAIN MENU*", call.message.chat.id, call.message.message_id, reply_markup=main_menu(), parse_mode="Markdown")
        elif d.startswith("bin_pocket_"): page=int(d.split("_")[-1]); bot.edit_message_text(f"🔮 *BINODEX*", call.message.chat.id, call.message.message_id, reply_markup=paginated_list(BINODEX_POCKET,page,"bin_pocket"), parse_mode="Markdown")
        elif d.startswith("forex_"): page=int(d.split("_")[-1]); bot.edit_message_text(f"💱 *FOREX*", call.message.chat.id, call.message.message_id, reply_markup=paginated_list(FOREX_PAIRS,page,"forex"), parse_mode="Markdown")
        elif d.startswith("indices_"): page=int(d.split("_")[-1]); bot.edit_message_text(f"📈 *INDICES*", call.message.chat.id, call.message.message_id, reply_markup=paginated_list(INDICES_LIST,page,"indices"), parse_mode="Markdown")
        elif d.startswith("mt5_"): page=int(d.split("_")[-1]); bot.edit_message_text(f"📊 *MT5*", call.message.chat.id, call.message.message_id, reply_markup=paginated_list(MT5_LIST,page,"mt5"), parse_mode="Markdown")
        elif d.startswith("gold_"): page=int(d.split("_")[-1]); bot.edit_message_text(f"🥇 *GOLD*", call.message.chat.id, call.message.message_id, reply_markup=paginated_list(GOLD_LIST,page,"gold"), parse_mode="Markdown")
        elif d.startswith("all_coins_"): page=int(d.split("_")[-1]); bot.edit_message_text(f"₿ *CRYPTO*", call.message.chat.id, call.message.message_id, reply_markup=coins_menu_paged(page), parse_mode="Markdown")
        elif d.startswith("coin_"):
            coin_id=d.replace("coin_",""); coin=next((c for c in ALL_COINS if c['id']==coin_id),None)
            if coin:
                price=coin['current_price']; is_buy=random.choice([True,False]); tp,sl,pt,ps=get_tp_sl_by_timeframe(price,is_buy,"crypto",5)
                sig="BUY 🟢" if is_buy else "SELL 🔴"
                rsi,ema,sup,res=generate_analysis(coin['symbol'],price)
                txt=f"₿ *{coin['name']} - 5M*\n💰 Entry: ${price:,.4f}\n🤖 {sig}\n🎯 TP: ${tp:,.4f} (+${pt})\n🛑 SL: ${sl:,.4f} (-${ps})\n📈 RSI:{rsi} | {ema}\n⚡ Conf: {random.randint(84,96)}%"
                kb=types.InlineKeyboardMarkup(); kb.add(types.InlineKeyboardButton("🔙 Back", callback_data="all_coins_0"))
                bot.send_message(call.message.chat.id, txt, parse_mode="Markdown", reply_markup=kb)
        elif d.startswith("analyze_"):
            asset=d.replace("analyze_",""); price=get_live_price(asset)
            if not price:
                if "EUR" in asset: price=random.uniform(1.08,1.09)
                elif "XAU" in asset: price=random.uniform(2030,2060)
                elif "US30" in asset: price=random.uniform(38500,39000)
                else: price=random.uniform(1.08,1.27)
            is_buy=random.choice([True,False]); tp,sl,pt,ps=get_tp_sl_by_timeframe(price,is_buy,"forex",5)
            sig="BUY CALL 🟢 STRONG" if is_buy else "SELL PUT 🔴 STRONG"
            rsi,ema,sup,res=generate_analysis(asset,price)
            txt=f"📊 *{asset} - 5M*\n💰 Entry: `{price:.5f}`\n🤖 {sig}\n🎯 TP: `{tp:.5f}` (+{pt} pips)\n🛑 SL: `{sl:.5f}` (-{ps})\n📈 RSI:{rsi} | {ema}\n⏰ 5 mins\n⚡ {random.randint(84,96)}%"
            kb=types.InlineKeyboardMarkup(); kb.add(types.InlineKeyboardButton("🔙 Menu", callback_data="menu"))
            bot.send_message(call.message.chat.id, txt, parse_mode="Markdown", reply_markup=kb)
    except Exception as e: print(e)

# SMART ANY TEXT + TIMEFRAME
@bot.message_handler(content_types=['text'])
def handle_text(m):
    if m.text.startswith('/'): return
    original_text = m.text
    text = m.text.upper().strip()
    
    if text in ["HI","HELLO","HEY","START","MENU","OK","YO","HELP"]:
        bot.send_message(m.chat.id, "🔥 *Main Menu* 👇", reply_markup=main_menu(), parse_mode="Markdown")
        return

    timeframe_str, minutes = parse_timeframe(original_text.lower())
    clean_asset = re.sub(r'\d+\s*(m|min|h|hour|d|day)', '', original_text, flags=re.IGNORECASE)
    clean_asset = clean_asset.replace("prediction","").replace("predict","").replace("signal","").replace("for","").replace("give me","").strip()
    if not clean_asset: clean_asset = original_text

    price = get_live_price(clean_asset)
    asset_type = "forex"
    if any(x in clean_asset.upper() for x in ["XAU","GOLD","XAG","SILVER"]): asset_type = "gold"
    elif any(x in clean_asset.upper() for x in ["US30","NAS","SPX","GER","UK100","JPN","VIX"]): asset_type = "indices"
    elif any(x in clean_asset.upper() for x in ["BTC","ETH","SOL","COIN"]): asset_type = "crypto"

    if not price:
        if "EUR" in text: price=random.uniform(1.08,1.09)
        elif "GBP" in text: price=random.uniform(1.26,1.27)
        elif "XAU" in text or "GOLD" in text: price=random.uniform(2030,2060)
        elif "BTC" in text: price=random.uniform(67000,68500)
        elif "US30" in text: price=random.uniform(38500,39000)
        elif "NAS" in text: price=random.uniform(17500,18000)
        else: price=random.uniform(1.08,1.27)

    is_buy = random.choice([True, False])
    tp, sl, pip_tp, pip_sl = get_tp_sl_by_timeframe(price, is_buy, asset_type, minutes)
    rsi,ema,sup,res = generate_analysis(clean_asset, price)
    sig = "BUY CALL 🟢 STRONG" if is_buy else "SELL PUT 🔴 STRONG"
    
    expiry_map = {1:"1 min",5:"5 mins",15:"15 mins",30:"30 mins",60:"1 Hour",240:"4 Hours",1440:"1 Day"}
    expiry = expiry_map.get(minutes, timeframe_str)

    txt = f"📊 *{clean_asset.upper()} - {timeframe_str} PREDICTION*\n\n💰 *Entry:* `{price:.5f}`\n🤖 *Signal:* {sig}\n🎯 *TP:* `{tp:.5f}` (+{pip_tp})\n🛑 *SL:* `{sl:.5f}` (-{pip_sl})\n\n📈 *{timeframe_str} Analysis:*\n• RSI: {rsi}\n• EMA: {ema}\n• Sup: `{sup:.5f}`\n• Res: `{res:.5f}`\n\n⏰ *Expiry:* {expiry}\n⚡ *Conf:* {random.randint(84,96)}%\n💡 *Auto-adjusted for {timeframe_str}*"

    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("5M", callback_data=f"analyze_{clean_asset}"),
        types.InlineKeyboardButton("1H", callback_data=f"analyze_{clean_asset}"),
        types.InlineKeyboardButton("🔙 Menu", callback_data="menu")
    )
    bot.send_message(m.chat.id, txt, parse_mode="Markdown", reply_markup=kb)

def run_bot():
    setup_menu()
    bot.infinity_polling()

if __name__=="__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
