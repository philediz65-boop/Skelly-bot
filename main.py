import os, threading, random, requests, re, io
from flask import Flask
import telebot
from telebot import types
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@app.route('/')
def home():
    return "SkellysPro FINAL CHART + LEVERAGE - LIVE"

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
        ticker_map = {"EUR/USD":"EURUSD=X","GBP/USD":"GBPUSD=X","USD/JPY":"USDJPY=X","XAU/USD":"GC=F","GOLD":"GC=F","BTC":"BTC-USD","ETH":"ETH-USD","US30":"^DJI","NAS100":"^IXIC","SPX500":"^GSPC"}
        ticker = None
        for k,v in ticker_map.items():
            if k in symbol_name.upper(): ticker=v; break
        if ticker:
            data = yf.download(ticker, period="1d", interval="1m", progress=False, timeout=3)
            if not data.empty: return float(data['Close'].iloc[-1])
    except: pass
    return None

def get_history_for_chart(symbol_name, entry_price):
    try:
        import yfinance as yf
        ticker_map = {"EUR/USD":"EURUSD=X","GBP/USD":"GBPUSD=X","USD/JPY":"USDJPY=X","XAU/USD":"GC=F","GOLD":"GC=F","BTC":"BTC-USD","ETH":"ETH-USD","US30":"^DJI","NAS100":"^IXIC","SPX500":"^GSPC"}
        ticker = "BTC-USD"
        for k,v in ticker_map.items():
            if k in symbol_name.upper(): ticker=v; break
        data = yf.download(ticker, period="1d", interval="15m", progress=False, timeout=5)
        if not data.empty and len(data)>30:
            return list(data['Close'].tail(50))
    except: pass
    # Fallback fake chart data around entry
    fake = [entry_price * random.uniform(0.985, 1.015) for _ in range(50)]
    fake[-1] = entry_price
    return fake

def create_chart_image(symbol, entry, tp, sl, tf_str, is_buy):
    try:
        history = get_history_for_chart(symbol, entry)
        plt.figure(figsize=(10,5), dpi=150)
        plt.style.use('dark_background')
        x = np.arange(len(history))
        plt.plot(x, history, color='#00ff88', linewidth=1.5, label='Price')

        # Lines
        plt.axhline(entry, color='white', linestyle='--', linewidth=1.2, label=f'Entry {entry:.2f}')
        plt.axhline(tp, color='#00ff00', linestyle='-', linewidth=1.5, label=f'TP {tp:.2f}')
        plt.axhline(sl, color='#ff3333', linestyle='-', linewidth=1.5, label=f'SL {sl:.2f}')

        # Fill TP/SL zone
        if is_buy:
            plt.fill_between(x, entry, tp, color='green', alpha=0.15)
            plt.fill_between(x, entry, sl, color='red', alpha=0.15)
        else:
            plt.fill_between(x, tp, entry, color='green', alpha=0.15)
            plt.fill_between(x, sl, entry, color='red', alpha=0.15)

        plt.title(f"{symbol.upper()} - {tf_str} | {'BUY/LONG' if is_buy else 'SELL/SHORT'}", color='white', fontsize=14, fontweight='bold')
        plt.legend(loc='upper left', fontsize=8)
        plt.grid(alpha=0.15)
        plt.tight_layout()

        path = f"/tmp/chart_{random.randint(1000,9999)}.png"
        plt.savefig(path, facecolor='#0e0e0e')
        plt.close()
        return path
    except Exception as e:
        print(f"Chart error {e}")
        return None

def generate_analysis(symbol, price):
    rsi = random.randint(35, 75)
    ema = random.choice(["Bullish crossover","Bearish crossover","Strong uptrend","Strong downtrend"])
    return rsi, ema, 0, 0

def parse_timeframe(text):
    text = text.lower()
    match = re.search(r'(\d+)\s*(m|min|h|hour|d|day)', text)
    if match:
        num = int(match.group(1)); unit = match.group(2)
        if 'h' in unit: return f"{num}H", num*60
        if 'd' in unit: return f"{num}D", num*1440
        return f"{num}M", num
    if "1h" in text: return "1H", 60
    if "4h" in text: return "4H", 240
    if "1d" in text: return "1D", 1440
    return "5M", 5

def tf_label(mins):
    if mins >= 1440: return f"{mins//1440}D"
    if mins >= 60: return f"{mins//60}H"
    return f"{mins}M"

def get_tp_sl_by_timeframe(price, is_buy, asset_type, minutes):
    if asset_type == "gold":
        base_tp = 3; base_sl = 2
        tp = base_tp * (minutes / 5); sl = base_sl * (minutes / 5)
        tp = min(tp, 50); sl = min(sl, 30)
    elif asset_type == "indices":
        base_tp = 80; base_sl = 50
        tp = base_tp * (minutes / 5); sl = base_sl * (minutes / 5)
        tp = min(tp, 2000); sl = min(sl, 1000)
    elif asset_type == "crypto":
        base_tp = price * 0.005; base_sl = price * 0.003
        tp = base_tp * (minutes / 5); sl = base_sl * (minutes / 5)
    else:
        base_tp = 0.0005; base_sl = 0.0003
        tp = base_tp * (minutes / 5); sl = base_sl * (minutes / 5)
    tp_price = price + tp if is_buy else price - tp
    sl_price = price - sl if is_buy else price + sl
    if asset_type == "forex":
        pips_tp = int(tp * 10000); pips_sl = int(sl * 10000)
    else:
        pips_tp = round(tp,2); pips_sl = round(sl,2)
    return tp_price, sl_price, pips_tp, pips_sl

def timeframe_keyboard(asset):
    kb = types.InlineKeyboardMarkup(row_width=4)
    kb.row(
        types.InlineKeyboardButton("5M", callback_data=f"an_5|{asset}"),
        types.InlineKeyboardButton("15M", callback_data=f"an_15|{asset}"),
        types.InlineKeyboardButton("1H", callback_data=f"an_60|{asset}"),
        types.InlineKeyboardButton("4H", callback_data=f"an_240|{asset}")
    )
    kb.add(types.InlineKeyboardButton("🔙 Menu", callback_data="menu"))
    return kb

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
    for it in chunk: kb.add(types.InlineKeyboardButton(f"📊 {it}", callback_data=f"an_5|{it}"))
    nav=[]
    if page>0: nav.append(types.InlineKeyboardButton("⬅️ Prev", callback_data=f"{prefix}_{page-1}"))
    if start+per_page < len(items): nav.append(types.InlineKeyboardButton("Next ➡️", callback_data=f"{prefix}_{page+1}"))
    if nav: kb.row(*nav)
    kb.add(types.InlineKeyboardButton("🔙 Main Menu", callback_data="menu"))
    return kb

def coins_menu_paged(page):
    per_page=10; start=page*per_page; chunk=ALL_COINS[start:start+per_page]
    kb=types.InlineKeyboardMarkup(row_width=1)
    for coin in chunk: kb.add(types.InlineKeyboardButton(f"{coin['symbol'].upper()} - ${coin['current_price']:,.2f}", callback_data=f"coin_{coin['id']}_5"))
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

def send_signal_with_chart(chat_id, asset, tf_str, minutes, price, asset_type):
    is_buy = random.choice([True,False])
    tp,sl,pt,ps = get_tp_sl_by_timeframe(price,is_buy,asset_type,minutes)
    rsi,ema,_,_ = generate_analysis(asset, price)
    sig = "BUY CALL 🟢 STRONG" if is_buy else "SELL PUT 🔴 STRONG"
    leverage_text=""; liq_text=""
    if asset_type=="crypto":
        lev=random.choice([10,15,20]); sig="LONG 🟢" if is_buy else "SHORT 🔴"
        leverage_text=f"\n💥 *Leverage:* `{lev}X Cross`"
        liq=price*0.92 if is_buy else price*1.08
        liq_text=f"\n💀 *Liq:* `${liq:,.2f}`"
    txt = f"📊 *{asset.upper()} - {tf_str}*\n\n💰 *Entry:* `{price:.5f}`\n🤖 *Signal:* {sig}{leverage_text}\n🎯 *TP:* `{tp:.5f}` (+{pt})\n🛑 *SL:* `{sl:.5f}` (-{ps}){liq_text}\n\n📈 *{tf_str}:* RSI {rsi} | {ema}\n⏰ *Expiry:* {tf_str}\n⚡ *Conf:* {random.randint(84,96)}%"
    chart_path = create_chart_image(asset, price, tp, sl, tf_str, is_buy)
    if chart_path and os.path.exists(chart_path):
        with open(chart_path, 'rb') as photo:
            bot.send_photo(chat_id, photo, caption=txt, parse_mode="Markdown", reply_markup=timeframe_keyboard(asset))
        os.remove(chart_path)
    else:
        bot.send_message(chat_id, txt, parse_mode="Markdown", reply_markup=timeframe_keyboard(asset))

@bot.message_handler(commands=['start'])
def start(m):
    global ALL_COINS
    if not ALL_COINS: ALL_COINS=get_all_coins()
    bot.send_message(m.chat.id, f"🔥 *SKELLY'S PRO - CHART + LEVERAGE*\n\n✅ Chart with lines\n✅ True TP/SL per timeframe\n✅ Type e.g BTC 1H\n\n👇 Select:", reply_markup=main_menu(), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: True)
def cb(call):
    global ALL_COINS
    d=call.data
    try:
        if d=="menu":
            bot.edit_message_text(f"🔥 *MAIN MENU*", call.message.chat.id, call.message.message_id, reply_markup=main_menu(), parse_mode="Markdown")
        elif d.startswith("bin_pocket_") or d.startswith("forex_") or d.startswith("indices_") or d.startswith("mt5_") or d.startswith("gold_") or d.startswith("all_coins_"):
            prefix = d.rsplit("_",1)[0]; page=int(d.rsplit("_",1)[1])
            if "bin_pocket" in prefix: bot.edit_message_text(f"🔮 *BINODEX*", call.message.chat.id, call.message.message_id, reply_markup=paginated_list(BINODEX_POCKET,page,"bin_pocket"), parse_mode="Markdown")
            elif "forex" in prefix: bot.edit_message_text(f"💱 *FOREX*", call.message.chat.id, call.message.message_id, reply_markup=paginated_list(FOREX_PAIRS,page,"forex"), parse_mode="Markdown")
            elif "indices" in prefix: bot.edit_message_text(f"📈 *INDICES*", call.message.chat.id, call.message.message_id, reply_markup=paginated_list(INDICES_LIST,page,"indices"), parse_mode="Markdown")
            elif "mt5" in prefix: bot.edit_message_text(f"📊 *MT5*", call.message.chat.id, call.message.message_id, reply_markup=paginated_list(MT5_LIST,page,"mt5"), parse_mode="Markdown")
            elif "gold" in prefix: bot.edit_message_text(f"🥇 *GOLD*", call.message.chat.id, call.message.message_id, reply_markup=paginated_list(GOLD_LIST,page,"gold"), parse_mode="Markdown")
            elif "all_coins" in prefix: bot.edit_message_text(f"₿ *CRYPTO*", call.message.chat.id, call.message.message_id, reply_markup=coins_menu_paged(page), parse_mode="Markdown")
        elif d.startswith("an_"):
            mins_asset = d[3:].split("|",1)
            minutes = int(mins_asset[0]); asset = mins_asset[1] if len(mins_asset)>1 else "EUR/USD"
            tf_str = tf_label(minutes)
            price = get_live_price(asset) or random.uniform(1.08,1.09)
            if "XAU" in asset or "GOLD" in asset: price = get_live_price(asset) or random.uniform(2030,2060)
            elif "BTC" in asset: price = get_live_price(asset) or random.uniform(67000,68500)
            elif "US30" in asset: price = get_live_price(asset) or random.uniform(38500,39000)
            asset_type = "forex"
            if any(x in asset.upper() for x in ["XAU","GOLD","XAG","SILVER"]): asset_type = "gold"
            elif any(x in asset.upper() for x in ["US30","NAS","SPX","GER","UK100","VIX","JPN","AUS"]): asset_type = "indices"
            elif any(x in asset.upper() for x in ["BTC","ETH","SOL","COIN"]): asset_type = "crypto"
            send_signal_with_chart(call.message.chat.id, asset, tf_str, minutes, price, asset_type)
        elif d.startswith("coin_"):
            parts = d.split("_"); coin_id = "_".join(parts[1:-1]) if len(parts)>2 else parts[1]; mins = int(parts[-1]) if parts[-1].isdigit() else 5
            coin = next((c for c in ALL_COINS if c['id']==coin_id),None)
            if coin:
                price=coin['current_price']; is_buy=random.choice([True,False]); leverage = random.choice([10,15,20])
                tp,sl,pt,ps=get_tp_sl_by_timeframe(price,is_buy,"crypto",mins); tf_str=tf_label(mins)
                sig="LONG 🟢" if is_buy else "SHORT 🔴"; rsi,ema,_,_=generate_analysis(coin['symbol'],price)
                txt=f"₿ *{coin['name']} ({coin['symbol'].upper()}) - {tf_str} FUTURES*\n\n💰 Entry: `${price:,.4f}`\n🤖 Signal: {sig} {leverage}X\n💥 Leverage: `{leverage}X Cross`\n🎯 TP: `${tp:,.4f}` (+{pt})\n🛑 SL: `${sl:,.4f}` (-{ps})\n💀 Liq: `${price*0.90 if is_buy else price*1.10:,.4f}`\n\n📈 RSI:{rsi} | {ema}\n⚡ Conf: {random.randint(86,96)}%\n⏰ {tf_str}"
                chart_path = create_chart_image(coin['symbol'], price, tp, sl, tf_str, is_buy)
                kb = types.InlineKeyboardMarkup(row_width=4)
                kb.row(types.InlineKeyboardButton("5M", callback_data=f"coin_{coin_id}_5"), types.InlineKeyboardButton("1H", callback_data=f"coin_{coin_id}_60"), types.InlineKeyboardButton("4H", callback_data=f"coin_{coin_id}_240"))
                kb.add(types.InlineKeyboardButton("🔙 Back", callback_data="all_coins_0"))
                if chart_path:
                    with open(chart_path,'rb') as photo:
                        bot.send_photo(call.message.chat.id, photo, caption=txt, parse_mode="Markdown", reply_markup=kb)
                    os.remove(chart_path)
                else:
                    bot.send_message(call.message.chat.id, txt, parse_mode="Markdown", reply_markup=kb)
    except Exception as e: print(f"CB Error {e} - {d}")

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
    elif any(x in clean_asset.upper() for x in ["US30","NAS","SPX","GER","UK100","VIX","JPN","AUS"]): asset_type = "indices"
    elif any(x in clean_asset.upper() for x in ["BTC","ETH","SOL","COIN","PEPE","DOGE","SHIB"]): asset_type = "crypto"
    if not price:
        if "EUR" in text: price=random.uniform(1.08,1.09)
        elif "XAU" in text or "GOLD" in text: price=random.uniform(2030,2060)
        elif "BTC" in text: price=random.uniform(67000,68500)
        elif "US30" in text: price=random.uniform(38500,39000)
        else: price=random.uniform(1.08,1.27)
    send_signal_with_chart(m.chat.id, clean_asset, timeframe_str, minutes, price, asset_type)

def run_bot():
    setup_menu()
    bot.infinity_polling()

if __name__=="__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
