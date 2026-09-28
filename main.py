import os, threading, random, requests, re, json, time
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
    return "SkellysPro WIN-TRACKER FIXED - LIVE"

BINODEX_POCKET = ["EUR/USD OTC","GBP/USD OTC","USD/JPY OTC","AUD/USD OTC","USD/CAD OTC","EUR/GBP OTC","EUR/JPY OTC","GBP/JPY OTC","AUD/JPY OTC","NZD/USD OTC","EUR/AUD OTC","EUR/CAD OTC","GBP/AUD OTC","USD/CHF OTC","CHF/JPY OTC","EUR/USD","GBP/USD","USD/JPY","BTC/USD OTC","ETH/USD OTC"]
FOREX_PAIRS = ["EUR/USD","GBP/USD","USD/JPY","AUD/USD","USD/CAD","NZD/USD","USD/CHF","EUR/GBP","EUR/JPY","EUR/AUD","GBP/JPY","AUD/JPY","CAD/JPY","CHF/JPY","NZD/JPY"]
INDICES_LIST = ["US30 (Dow Jones)","NAS100 (Nasdaq)","SPX500 (S&P 500)","GER40 (DAX)","UK100 (FTSE)","JPN225 (Nikkei)","AUS200","VIX"]
MT5_LIST = ["EUR/USD - MT5","GBP/USD - MT5","USD/JPY - MT5","XAU/USD (Gold) - MT5","XAG/USD (Silver) - MT5","BTC/USD - MT5","US30 - MT5","NAS100 - MT5","SPX500 - MT5","GER40 - MT5","UK100 - MT5","USOil - MT5"]
GOLD_LIST = ["XAU/USD (Gold)","XAG/USD (Silver)","XAU/EUR","XPT/USD (Platinum)"]
ALL_COINS = []
COIN_PRICE_MAP = {}
COIN_DATA_MAP = {}

STATS_FILE = "/tmp/skelly_stats.json"
PENDING_FILE = "/tmp/skelly_pending.json"

def load_json(path, default):
    try:
        if os.path.exists(path):
            with open(path,'r') as f:
                return json.load(f)
    except:
        pass
    return default

def save_json(path, data):
    try:
        with open(path,'w') as f:
            json.dump(f,data)
    except:
        pass

stats = load_json(STATS_FILE, {"total":0,"wins":0,"losses":0,"pending":0})
pending_trades = load_json(PENDING_FILE, [])

def get_all_coins():
    global COIN_PRICE_MAP, COIN_DATA_MAP
    try:
        url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=100&page=1&price_change_percentage=24h"
        data = requests.get(url, timeout=15).json()
        COIN_PRICE_MAP = {}
        COIN_DATA_MAP = {}
        for c in data:
            COIN_PRICE_MAP[c['symbol'].upper()] = c['current_price']
            COIN_PRICE_MAP[c['id'].upper()] = c['current_price']
            COIN_DATA_MAP[c['symbol'].upper()] = c
            COIN_DATA_MAP[c['id'].upper()] = c
        return data
    except:
        return []

def get_live_price(symbol_name):
    sym = symbol_name.upper().strip()
    base = re.split(r'[\s/]+', sym)[0]
    if base in COIN_PRICE_MAP:
        return float(COIN_PRICE_MAP[base])
    if sym in COIN_PRICE_MAP:
        return float(COIN_PRICE_MAP[sym])
    try:
        id_map = {"BTC":"bitcoin","ETH":"ethereum","SOL":"solana","ZEC":"zcash","XRP":"ripple","DOGE":"dogecoin","PEPE":"pepe","SHIB":"shiba-inu","ADA":"cardano","AVAX":"avalanche-2","LINK":"chainlink"}
        coin_id = id_map.get(base, base.lower())
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
        r = requests.get(url, timeout=5).json()
        if coin_id in r and 'usd' in r[coin_id]:
            price = float(r[coin_id]['usd'])
            COIN_PRICE_MAP[base] = price
            return price
    except:
        pass
    try:
        import yfinance as yf
        ticker_map = {"EUR/USD":"EURUSD=X","GBP/USD":"GBPUSD=X","USD/JPY":"USDJPY=X","XAU/USD":"GC=F","GOLD":"GC=F","US30":"^DJI","NAS100":"^IXIC","SPX500":"^GSPC"}
        ticker = None
        for k,v in ticker_map.items():
            if k in sym:
                ticker=v
                break
        if ticker:
            data = yf.download(ticker, period="1d", interval="1m", progress=False, timeout=3)
            if not data.empty:
                return float(data['Close'].iloc[-1])
    except:
        pass
    return None

def get_history_for_chart(symbol_name, entry_price):
    try:
        import yfinance as yf
        ticker_map = {"EUR/USD":"EURUSD=X","GBP/USD":"GBPUSD=X","USD/JPY":"USDJPY=X","XAU/USD":"GC=F","GOLD":"GC=F","BTC":"BTC-USD","ETH":"ETH-USD","ZEC":"ZEC-USD","US30":"^DJI","NAS100":"^IXIC","SPX500":"^GSPC"}
        ticker = "BTC-USD"
        for k,v in ticker_map.items():
            if k in symbol_name.upper():
                ticker=v
                break
        data = yf.download(ticker, period="1d", interval="15m", progress=False, timeout=5)
        if not data.empty and len(data)>30:
            return list(data['Close'].tail(60))
    except:
        pass
    fake = [entry_price * random.uniform(0.985, 1.015) for _ in range(60)]
    fake[-1] = entry_price
    return fake

def calc_rsi(prices, period=14):
    try:
        deltas = np.diff(prices)
        gains = np.where(deltas>0, deltas, 0)
        losses = np.where(deltas<0, -deltas, 0)
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        if avg_loss == 0:
            return 70
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return round(float(rsi),1)
    except:
        return 55

def calc_ema(prices, period):
    try:
        return float(np.mean(prices[-period:]))
    except:
        return prices[-1]

def generate_full_analysis(history, price, symbol):
    rsi = calc_rsi(np.array(history))
    ema9 = calc_ema(history, 9)
    ema21 = calc_ema(history, 21)
    ema50 = calc_ema(history, 50)
    bullish_points = 0
    bearish_points = 0
    if price > ema9:
        bullish_points+=1
    else:
        bearish_points+=1
    if ema9 > ema21:
        bullish_points+=1
    else:
        bearish_points+=1
    if ema21 > ema50:
        bullish_points+=1
    else:
        bearish_points+=1
    if rsi > 50 and rsi < 70:
        bullish_points+=1
    elif rsi < 50 and rsi > 30:
        bearish_points+=1
    if rsi <= 30:
        bullish_points+=2
    if rsi >= 70:
        bearish_points+=2
    is_buy = bullish_points >= bearish_points
    if price > ema9 > ema21:
        trend = "Strong Bullish"
    elif price > ema21:
        trend = "Bullish"
    elif price < ema9 < ema21:
        trend = "Strong Bearish"
    else:
        trend = "Bearish"
    if rsi >= 70:
        rsi_sig = "Overbought"
    elif rsi <= 30:
        rsi_sig = "Oversold"
    elif rsi >= 60:
        rsi_sig = "Strong buy momentum"
    elif rsi <= 40:
        rsi_sig = "Strong sell momentum"
    else:
        rsi_sig = "Neutral"
    macd_line = ema9 - ema21
    if macd_line > 0:
        macd_sig = "Bullish crossover"
    else:
        macd_sig = "Bearish crossover"
    try:
        support = round(float(min(history[-20:])), 5)
        resistance = round(float(max(history[-20:])), 5)
    except:
        support = round(price*0.992,5)
        resistance = round(price*1.008,5)
    confidence = 75 + min(abs(bullish_points - bearish_points)*5, 21)
    return {"rsi":rsi,"rsi_sig":rsi_sig,"ema9":round(ema9,5),"ema21":round(ema21,5),"ema50":round(ema50,5),"trend":trend,"macd":macd_sig,"support":support,"resistance":resistance,"is_buy":is_buy,"conf":min(confidence,96)}

def get_fundamentals(symbol):
    try:
        base = re.split(r'[\s/]+', symbol.upper())[0]
        if base in COIN_DATA_MAP:
            c = COIN_DATA_MAP[base]
            chg = c.get('price_change_percentage_24h',0)
            mc = c.get('market_cap',0)
            vol = c.get('total_volume',0)
            senti = "Greedy" if chg>2 else "Fearful" if chg<-2 else "Neutral"
            return "Fundamentals: MCap ${:.2f}B | Vol ${:.2f}B | 24h {:+.2f}% | {}".format(mc/1e9, vol/1e9, chg, senti)
        return "Fundamentals: Market active - Volatility normal"
    except:
        return "Fundamentals: Market active"

def create_chart_image(symbol, entry, tp, sl, tf_str, is_buy):
    try:
        history = get_history_for_chart(symbol, entry)
        plt.figure(figsize=(10,5), dpi=150)
        plt.style.use('dark_background')
        x = np.arange(len(history))
        plt.plot(x, history, color='#00ff88', linewidth=1.5)
        plt.axhline(entry, color='white', linestyle='--', linewidth=1.2)
        plt.axhline(tp, color='#00ff00', linestyle='-', linewidth=1.5)
        plt.axhline(sl, color='#ff3333', linestyle='-', linewidth=1.5)
        title = "{} - {} | {}".format(symbol.upper(), tf_str, 'BUY/LONG' if is_buy else 'SELL/SHORT')
        plt.title(title, color='white', fontsize=13, fontweight='bold')
        plt.grid(alpha=0.15)
        plt.tight_layout()
        path = f"/tmp/chart_{random.randint(1000,9999)}.png"
        plt.savefig(path, facecolor='#0e0e0e')
        plt.close()
        return path
    except:
        return None

def parse_timeframe(text):
    text=text.lower()
    match=re.search(r'(\d+)\s*(m|min|h|hour|d|day)', text)
    if match:
        num=int(match.group(1))
        unit=match.group(2)
        if 'h' in unit:
            return f"{num}H", num*60
        if 'd' in unit:
            return f"{num}D", num*1440
        return f"{num}M", num
    if "1h" in text:
        return "1H",60
