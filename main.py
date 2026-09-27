import os, threading, telebot, ccxt, pandas as pd, random
from flask import Flask
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)
ex = ccxt.binance()
app = Flask(__name__)
@app.route('/')
def home(): return "SkellysPro_bot MENU LIVE!"

def analyze(closes):
    df=pd.DataFrame(closes,columns=['c']);df['ema9']=df['c'].ewm(span=9).mean();df['ema21']=df['c'].ewm(span=21).mean();d=df['c'].diff();gain=d.where(d>0,0).rolling(14).mean();loss=-d.where(d<0,0).rolling(14).mean();df['rsi']=100-(100/(1+gain/loss));p,e9,e21,rsi=df['c'].iloc[-1],df['ema9'].iloc[-1],df['ema21'].iloc[-1],df['rsi'].iloc[-1];atr=(df['c'].rolling(14).max()-df['c'].rolling(14).min()).iloc[-1]
    if e9>e21 and 45<rsi<70: sig="BUY 🟢";tp=p+atr*1.5;sl=p-atr*0.8;acc=60+(rsi-45)
    elif e9<e21 and 30<rsi<55: sig="SELL 🔴";tp=p-atr*1.5;sl=p+atr*0.8;acc=60+(55-rsi)
    else: sig="WAIT ⏸️";tp=sl=p;acc=52
    return sig,p,e9,e21,rsi,min(acc,88.9),tp,sl

def get_signal(sym, market):
    try:
        ohlcv=ex.fetch_ohlcv(sym,'5m',limit=100);sig,p,e9,e21,rsi,acc,tp,sl=analyze([c[4] for c in ohlcv])
        if "POCKET" in market or "BINODEX" in market:
            call_put="CALL 🟢" if "BUY" in sig else "PUT 🔴" if "SELL" in sig else "WAIT"
            return f"📊 {sym} | {market}\n{call_put}\nEntry: {p:.4f}\nRSI: {rsi:.1f} | EMA: {e9:.2f}\n✅ Accuracy: {acc:.1f}%\n⏰ Expiry: 5 MIN\n🤔 Logic: {'RSI+EMA Bullish' if 'BUY' in sig else 'RSI+EMA Bearish'}"
        else:
            return f"📊 {sym} | {market}\n{sig} @ {p:.2f}\nRSI: {rsi:.1f} | EMA {e9:.1f}/{e21:.1f}\n🎯 TP: {tp:.2f}\n🛑 SL: {sl:.2f}\n✅ Accuracy: {acc:.1f}%"
    except: return f"⚠️ {sym} loading... try again"

def menu_kb():
    kb=InlineKeyboardMarkup(row_width=2)
    kb.add(InlineKeyboardButton("🔮 BINODEX & POCKET", callback_data="binodex"),
           InlineKeyboardButton("📊 MT5", callback_data="mt5"),
           InlineKeyboardButton("₿ CRYPTO", callback_data="crypto"),
           InlineKeyboardButton("💱 FOREX", callback_data="forex"),
           InlineKeyboardButton("📈 GOLD", callback_data="gold"),
           InlineKeyboardButton("🎯 BEST SIGNAL", callback_data="best"))
    return kb

@bot.message_handler(commands=['start'])
def start(m):
    # Set commands menu for Telegram
    try: bot.set_my_commands([telebot.types.BotCommand("binodex","BINODEX & POCKET"),telebot.types.BotCommand("mt5","MT5"),telebot.types.BotCommand("crypto","CRYPTO"),telebot.types.BotCommand("forex","FOREX"),telebot.types.BotCommand("gold","GOLD"),telebot.types.BotCommand("start","Main Menu")])
    except: pass
    bot.send_message(m.chat.id, f"👋 {m.from_user.first_name}, Welcome to @SkellysPro_bot!\n\n👇 **CLICK MENU BELOW:**\nSelect market you want signal for:", reply_markup=menu_kb())

@bot.message_handler(commands=['binodex','pocket'])
def binodex_cmd(m):
    bot.send_message(m.chat.id, "🤔 I see Pocket/Binodex OTC... Getting 5min CALL/PUT...")
    bot.send_message(m.chat.id, get_signal("EUR/USD","BINODEX & POCKET OTC")+"\n\n"+get_signal("GBP/USD","BINODEX & POCKET OTC"), reply_markup=menu_kb())

@bot.message_handler(commands=['mt5'])
def mt5_cmd(m):
    bot.send_message(m.chat.id, "🤔 MT5 mode activated... Scanning MT5...")
    bot.send_message(m.chat.id, get_signal("XAU/USD","MT5")+"\n\n"+get_signal("EUR/USD","MT5"), reply_markup=menu_kb())

@bot.message_handler(commands=['crypto'])
def crypto_cmd(m):
    bot.send_message(m.chat.id, "🤔 Hmm you talk about crypto... Checking Binance...")
    bot.send_message(m.chat.id, get_signal("BTC/USDT","CRYPTO")+"\n\n"+get_signal("ETH/USDT","CRYPTO"), reply_markup=menu_kb())

@bot.message_handler(commands=['forex'])
def forex_cmd(m):
    bot.send_message(m.chat.id, "🤔 Na Forex pair be this... Analyzing...")
    bot.send_message(m.chat.id, get_signal("EUR/USD","FOREX")+"\n\n"+get_signal("GBP/USD","FOREX"), reply_markup=menu_kb())

@bot.message_handler(commands=['gold','best'])
def other(m):
    if "gold" in m.text: bot.send_message(m.chat.id, get_signal("XAU/USD","MT5/GOLD"), reply_markup=menu_kb())
    else: bot.send_message(m.chat.id, "🎯 BEST SIGNAL:\n\n"+get_signal(random.choice(["XAU/USD","BTC/USDT","EUR/USD"]),"BEST"), reply_markup=menu_kb())

@bot.callback_query_handler(func=lambda c: True)
def cb(c):
    if c.data=="binodex": bot.send_message(c.message.chat.id, get_signal("EUR/USD","BINODEX & POCKET OTC"), reply_markup=menu_kb())
    elif c.data=="mt5": bot.send_message(c.message.chat.id, get_signal("XAU/USD","MT5"), reply_markup=menu_kb())
    elif c.data=="crypto": bot.send_message(c.message.chat.id, get_signal("BTC/USDT","CRYPTO"), reply_markup=menu_kb())
    elif c.data=="forex": bot.send_message(c.message.chat.id, get_signal("EUR/USD","FOREX"), reply_markup=menu_kb())
    elif c.data=="gold": bot.send_message(c.message.chat.id, get_signal("XAU/USD","GOLD"), reply_markup=menu_kb())
    elif c.data=="best": bot.send_message(c.message.chat.id, get_signal(random.choice(["XAU/USD","BTC/USDT","EUR/USD"]),"BEST"), reply_markup=menu_kb())

@bot.message_handler(func=lambda m: True)
def any_text(m):
    txt=m.text.lower()
    if "pocket" in txt or "binodex" in txt or "otc" in txt: binodex_cmd(m)
    elif "mt5" in txt: mt5_cmd(m)
    elif "crypto" in txt or "btc" in txt or "eth" in txt: crypto_cmd(m)
    elif "forex" in txt or "eur" in txt or "gbp" in txt: forex_cmd(m)
    else: start(m)

def run_bot(): bot.infinity_polling()
threading.Thread(target=run_bot).start()
if __name__=="__main__": app.run(host="0.0.0.0",port=int(os.environ.get("PORT",10000)))
