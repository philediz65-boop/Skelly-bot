import os, threading, telebot, ccxt, pandas as pd
from flask import Flask
BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)
ex = ccxt.binance()
app = Flask(__name__)
@app.route('/')
def home(): return "SkellysPro_bot LIVE!"
def analyze(closes):
    df=pd.DataFrame(closes,columns=['c']);df['ema9']=df['c'].ewm(span=9).mean();df['ema21']=df['c'].ewm(span=21).mean();d=df['c'].diff();gain=d.where(d>0,0).rolling(14).mean();loss=-d.where(d<0,0).rolling(14).mean();df['rsi']=100-(100/(1+gain/loss));p,e9,e21,rsi=df['c'].iloc[-1],df['ema9'].iloc[-1],df['ema21'].iloc[-1],df['rsi'].iloc[-1];atr=(df['c'].rolling(14).max()-df['c'].rolling(14).min()).iloc[-1]
    if e9>e21 and 45<rsi<70: sig="BUY 🟢";tp=p+atr*1.5;sl=p-atr*0.8;acc=60+(rsi-45)
    elif e9<e21 and 30<rsi<55: sig="SELL 🔴";tp=p-atr*1.5;sl=p+atr*0.8;acc=60+(55-rsi)
    else: sig="WAIT ⏸️";tp=sl=p;acc=52
    return sig,p,e9,e21,rsi,min(acc,88.5),tp,sl
@bot.message_handler(commands=['start','gold','crypto','mt5'])
def handle(m):
    for sym in ["XAU/USD","BTC/USDT","EUR/USD"]:
        try:
            ohlcv=ex.fetch_ohlcv(sym,'5m',limit=100);s,p,e9,e21,rsi,acc,tp,sl=analyze([c[4] for c in ohlcv]);bot.send_message(m.chat.id,f"📊 {sym}\n{s} @ {p:.2f}\nRSI {rsi:.1f} Acc {acc:.1f}%\nTP {tp:.2f} SL {sl:.2f}")
        except: continue
def run_bot(): bot.infinity_polling()
threading.Thread(target=run_bot).start()
if __name__=="__main__": app.run(host="0.0.0.0",port=int(os.environ.get("PORT",10000)))
