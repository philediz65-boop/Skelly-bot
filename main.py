import os, threading, random, requests, re, json, time
from flask import Flask
import telebot
from telebot import types
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

TOKEN = os.getenv("BOT_TOKEN")
print(f"BOT_TOKEN check: {'OK' if TOKEN else 'MISSING - Add in Render Environment!'}")

app = Flask(__name__)

@app.route('/')
def home():
    return "SkellysPro - LIVE with Win Rate Tracker"

if not TOKEN:
    print("ERROR: BOT_TOKEN not set! Set it in Render -> Environment")
    bot = None
else:
    bot = telebot.TeleBot(TOKEN)

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
            with open(path,'r') as f: return json.load(f)
    except: pass
    return default

def save_json(path, data):
    try:
        with open(path,'w') as f: json.dump(f,data)
    except: pass

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
    except: return []

def get_live_price(symbol_name):
    sym = symbol_name.upper().strip()
    base = re.split(r'[\s/]+', sym)[0]
    if base in COIN_PRICE_MAP: return float(COIN_PRICE_MAP[base])
    if sym in COIN_PRICE_MAP: return float(COIN_PRICE_MAP[sym])
    try:
        id_map = {"BTC":"bitcoin","ETH":"ethereum","SOL":"solana","ZEC":"zcash","XRP":"ripple","DOGE":"dogecoin","PEPE":"pepe","SHIB":"shiba-inu","ADA":"cardano","AVAX":"avalanche-2","LINK":"chainlink"}
        coin_id = id_map.get(base, base.lower())
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
        r = requests.get(url, timeout=5).json()
        if coin_id in r and 'usd' in r[coin_id]:
            price = float(r[coin_id]['usd'])
            COIN_PRICE_MAP[base] = price
            return price
    except: pass
    return None

def get_history_for_chart(symbol_name, entry_price):
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
        if avg_loss == 0: return 70
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return round(float(rsi),1)
    except: return 55

def calc_ema(prices, period):
    try: return float(np.mean(prices[-period:]))
    except: return prices[-1]

def generate_full_analysis(history, price, symbol):
    rsi = calc_rsi(np.array(history))
    ema9 = calc_ema(history, 9)
    ema21 = calc_ema(history, 21)
    ema50 = calc_ema(history, 50)
    bullish_points = 0; bearish_points = 0
    if price > ema9: bullish_points+=1
    else: bearish_points+=1
    if ema9 > ema21: bullish_points+=1
    else: bearish_points+=1
    if ema21 > ema
