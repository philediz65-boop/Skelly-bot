import os, requests, pandas as pd, time
from datetime import datetime

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID", "7536056057")

def send(m):
    try:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id":CHAT_ID,"text":m}, timeout=10)
    except: pass

def get_price():
    try:
        r = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=PAXGUSDT", timeout=10).json()
        return float(r['price'])
    except: return 0.0

def get_klines(interval, limit=100):
    try:
        url = f"https://api.binance.com/api/v3/klines?symbol=PAXGUSDT&interval={interval}&limit={limit}"
        data = requests.get(url, timeout=10).json()
        df = pd.DataFrame(data, columns=['time','Open','High','Low','Close','Vol','ct','qa','trades','tb','tq','i'])
        for c in ['Open','High','Low','Close']:
            df[c] = df[c].astype(float)
        return df
    except: return pd.DataFrame()

def analyze(interval):
    df = get_klines(interval, 100)
    if df.empty or len(df) < 60: return None,0,0,0,0,0,0,0
    close = df['Close']; high = df['High']; low = df['Low']
    ema20 = float(close.ewm(span=20).mean().iloc[-1])
    ema50 = float(close.ewm(span=50).mean().iloc[-1])
    delta = close.diff()
    gain = delta.where(delta>0,0).rolling(14).mean()
    loss = (-delta.where(delta<0,0)).rolling(14).mean()
    rsi = 100 - (100/(1+gain/loss))
    rsi_val = float(rsi.iloc[-1])
    tr = pd.concat([high-low, (high-close.shift()).abs(), (low-close.shift()).abs()], axis=1).max(axis=1)
    atr = float(tr.rolling(14).mean().iloc[-1])
    if ema20>ema50 and rsi_val>55: trend="BUY"
    elif ema20<ema50 and rsi_val<45: trend="SELL"
    else: trend="WAIT"
    return trend, float(close.iloc[-1]), ema20, ema50, rsi_val, atr, float(low.iloc[-2]), float(high.iloc[-2])

send(f"✅ Skelly Pro v3 LIVE - XAUUSD Fixed Price {get_price():.2f} - Binance PAXG = MT5 Gold")

last_signal=""
while True:
    try:
        curr = get_price()
        t30,p30,e20_30,e50_30,rsi30,atr30,low30,high30 = analyze("30m")
        t60,p60,e20_60,e50_60,rsi60,atr60,low60,high60 = analyze("1h")
        print(f"{datetime.now().strftime('%H:%M')} 30M:{t30} 1H:{t60} Price:{curr}")

        if t30 and t30!="WAIT" and t30==t60 and t30!=last_signal:
            entry = round((p30 + e20_30)/2, 2)
            if t30=="BUY":
                risk = 8
                sl = round(entry - risk, 2)
                tp1 = round(entry + risk*1.5, 2)
                tp2 = round(entry + risk*2.5, 2)
            else:
                risk = 8
                sl = round(entry + risk, 2)
                tp1 = round(entry - risk*1.5, 2)
                tp2 = round(entry - risk*2.5, 2)

            msg = f"""🔥 XAUUSD {t30} SIGNAL 🔥
30M={t30} | 1H={t60}
Now: {curr:.2f}
ENTRY: {entry:.2f}
TP1: {tp1:.2f}
TP2: {tp2:.2f}
SL: {sl:.2f}
Risk: 1:2.5"""
            send(msg)
            last_signal=t30
        time.sleep(180)
    except Exception as e:
        print(f"error {e}")
        time.sleep(60)
