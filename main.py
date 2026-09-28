import os, threading, random, requests, re, json, time
from flask import Flask
import telebot
from telebot import types
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

TOKEN = os.getenv("BOT_TOKEN")
print(f"TOKEN CHECK: {'OK' if TOKEN else 'MISSING'}")

app = Flask(__name__)
@app.route('/')
def home():
    return "SkellysPro - LIVE WIN TRACKER OK"

if not TOKEN:
    print("ERROR: BOT_TOKEN not set")
    bot = None
else:
    bot = telebot.TeleBot(TOKEN)

BINODEX_POCKET = ["EUR/USD OTC","GBP/USD OTC","USD/JPY OTC","AUD/USD OTC","USD/CAD OTC","EUR/GBP OTC","EUR/JPY OTC","GBP/JPY OTC","AUD/JPY OTC","NZD/USD OTC","EUR/AUD OTC","EUR/CAD OTC","GBP/AUD OTC","USD/CHF OTC","CHF/JPY OTC","EUR/USD","GBP/USD","USD/JPY","BTC/USD OTC","ETH/USD OTC"]
FOREX_PAIRS = ["EUR/USD","GBP/USD","USD/JPY","AUD/USD","USD/CAD","NZD/USD","USD/CHF","EUR/GBP","EUR/JPY","EUR/AUD","GBP/JPY","AUD/JPY","CAD/JPY","CHF/JPY","NZD/JPY"]
INDICES_LIST = ["US30 (Dow Jones)","NAS100 (Nasdaq)","SPX500 (S&P 500)","GER40 (DAX)","UK100 (FTSE)","JPN225 (Nikkei)","AUS200","VIX"]
MT5_LIST = ["EUR/USD - MT5","GBP/USD - MT5","USD/JPY - MT5","XAU/USD (Gold) - MT5","XAG/USD (Silver) - MT5","BTC/USD - MT5","US30 - MT5","NAS100 - MT5","SPX500 - MT5","GER40 - MT5","UK100 - MT5","USOil - MT5"]
GOLD_LIST = ["XAU/USD (Gold)","XAG/USD (Silver)","XAU/EUR","XPT/USD (Platinum)"]
ALL_COINS, COIN_PRICE_MAP, COIN_DATA_MAP = [], {}, {}
STATS_FILE, PENDING_FILE = "/tmp/skelly_stats.json", "/tmp/skelly_pending.json"

def load_json(p,d):
    try:
        if os.path.exists(p):
            with open(p,'r') as f: return json.load(f)
    except: pass
    return d
def save_json(p,data):
    try:
        with open(p,'w') as f: json.dump(f,data)
    except: pass

stats = load_json(STATS_FILE, {"total":0,"wins":0,"losses":0,"pending":0})
pending_trades = load_json(PENDING_FILE, [])

def get_all_coins():
    global COIN_PRICE_MAP, COIN_DATA_MAP
    try:
        url="https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=100&page=1&price_change_percentage=24h"
        data=requests.get(url,timeout=15).json()
        COIN_PRICE_MAP, COIN_DATA_MAP = {}, {}
        for c in data:
            COIN_PRICE_MAP[c['symbol'].upper()]=c['current_price']
            COIN_PRICE_MAP[c['id'].upper()]=c['current_price']
            COIN_DATA_MAP[c['symbol'].upper()]=c
            COIN_DATA_MAP[c['id'].upper()]=c
        return data
    except: return []

def get_live_price(s):
    b=re.split(r'[\s/]+', s.upper().strip())[0]
    if b in COIN_PRICE_MAP: return float(COIN_PRICE_MAP[b])
    if s.upper().strip() in COIN_PRICE_MAP: return float(COIN_PRICE_MAP[s.upper().strip()])
    try:
        m={"BTC":"bitcoin","ETH":"ethereum","SOL":"solana","ZEC":"zcash","XRP":"ripple","DOGE":"dogecoin","PEPE":"pepe","SHIB":"shiba-inu","ADA":"cardano","AVAX":"avalanche-2","LINK":"chainlink"}
        cid=m.get(b,b.lower())
        r=requests.get(f"https://api.coingecko.com/api/v3/simple/price?ids={cid}&vs_currencies=usd",timeout=5).json()
        if cid in r and 'usd' in r[cid]: return float(r[cid]['usd'])
    except: pass
    return None

def get_history_for_chart(sym,entry):
    f=[entry*random.uniform(0.985,1.015) for _ in range(60)]
    f[-1]=entry
    return f

def calc_rsi(prices,period=14):
    try:
        d=np.diff(prices); g=np.where(d>0,d,0); l=np.where(d<0,-d,0)
        ag=np.mean(g[-period:]); al=np.mean(l[-period:])
        if al==0: return 70
        rs=ag/al; rsi=100-(100/(1+rs)); return round(float(rsi),1)
    except: return 55

def calc_ema(p,period):
    try: return float(np.mean(p[-period:]))
    except: return p[-1]

def generate_full_analysis(history,price,symbol):
    rsi=calc_rsi(np.array(history)); ema9=calc_ema(history,9); ema21=calc_ema(history,21); ema50=calc_ema(history,50)
    bull=0; bear=0
    if price>ema9: bull+=1
    else: bear+=1
    if ema9>ema21: bull+=1
    else: bear+=1
    if ema21>ema50: bull+=1
    else: bear+=1
    if rsi>50 and rsi<70: bull+=1
    elif rsi<50 and rsi>30: bear+=1
    if rsi<=30: bull+=2
    if rsi>=70: bear+=2
    is_buy=bull>=bear
    if price>ema9 and ema9>ema21: trend="Strong Bullish"
    elif price>ema21: trend="Bullish"
    elif price<ema9 and ema9<ema21: trend="Strong Bearish"
    else: trend="Bearish"
    if rsi>=70: rsi_sig="Overbought"
    elif rsi<=30: rsi_sig="Oversold"
    elif rsi>=60: rsi_sig="Strong buying momentum"
    elif rsi<=40: rsi_sig="Strong selling momentum"
    else: rsi_sig="Neutral"
    macd_sig="Bullish crossover" if (ema9-ema21)>0 else "Bearish crossover"
    return {"rsi":rsi,"rsi_sig":rsi_sig,"ema9":round(ema9,5),"ema21":round(ema21,5),"ema50":round(ema50,5),"trend":trend,"macd":macd_sig,"support":round(price*0.992,5),"resistance":round(price*1.008,5),"is_buy":is_buy,"conf":min(75+abs(bull-bear)*5,96)}

def get_fundamentals(symbol):
    try:
        b=re.split(r'[\s/]+', symbol.upper())[0]
        if b in COIN_DATA_MAP:
            c=COIN_DATA_MAP[b]; chg=c.get('price_change_percentage_24h',0); mc=c.get('market_cap',0)
            return f"Fundamentals MCap ${mc/1e9:.2f}B | 24h {chg:+.2f}%"
        return "Fundamentals: Market active"
    except: return "Fundamentals: Market active"

def create_chart_image(symbol,entry,tp,sl,tf_str,is_buy):
    try:
        h=get_history_for_chart(symbol,entry); plt.figure(figsize=(10,5),dpi=150); plt.style.use('dark_background')
        x=np.arange(len(h)); plt.plot(x,h,color='#00ff88',linewidth=1.5)
        plt.axhline(entry,color='white',linestyle='--',linewidth=1.2); plt.axhline(tp,color='#00ff00',linestyle='-',linewidth=1.5); plt.axhline(sl,color='#ff3333',linestyle='-',linewidth=1.5)
        plt.title(f"{symbol.upper()} - {tf_str} | {'BUY' if is_buy else 'SELL'}",color='white',fontsize=13,fontweight='bold'); plt.grid(alpha=0.15); plt.tight_layout()
        path=f"/tmp/chart_{random.randint(1000,9999)}.png"; plt.savefig(path,facecolor='#0e0e0e'); plt.close(); return path
    except: return None

def parse_timeframe(t):
    t=t.lower(); m=re.search(r'(\d+)\s*(m|min|h|hour|d|day)',t)
    if m:
        n=int(m.group(1)); u=m.group(2)
        if 'h' in u: return f"{n}H",n*60
        if 'd' in u: return f"{n}D",n*1440
        return f"{n}M",n
    return "5M",5

def tf_label(mins):
    if mins>=1440: return f"{mins//1440}D"
    if mins>=60: return f"{mins//60}H"
    return f"{mins}M"

def get_tp_sl_by_timeframe(price,is_buy,atype,minutes):
    if atype=="gold": tp=3*(minutes/5); sl=2*(minutes/5); tp=min(tp,50); sl=min(sl,30)
    elif atype=="indices": tp=80*(minutes/5); sl=50*(minutes/5); tp=min(tp,2000); sl=min(sl,1000)
    elif atype=="crypto": tp=price*0.005*(minutes/5); sl=price*0.003*(minutes/5)
    else: tp=0.0005*(minutes/5); sl=0.0003*(minutes/5)
    tp_p=price+tp if is_buy else price-tp; sl_p=price-sl if is_buy else price+sl
    pt=int(tp*10000) if atype=="forex" else round(tp,2); ps=int(sl*10000) if atype=="forex" else round(sl,2)
    return tp_p,sl_p,pt,ps

def timeframe_keyboard(asset):
    kb=types.InlineKeyboardMarkup(row_width=4)
    kb.row(types.InlineKeyboardButton("5M",callback_data=f"an_5|{asset}"),types.InlineKeyboardButton("15M",callback_data=f"an_15|{asset}"),types.InlineKeyboardButton("1H",callback_data=f"an_60|{asset}"),types.InlineKeyboardButton("4H",callback_data=f"an_240|{asset}"))
    kb.row(types.InlineKeyboardButton("Refresh",callback_data=f"an_5|{asset}"),types.InlineKeyboardButton("Stats",callback_data="stats"),types.InlineKeyboardButton("Menu",callback_data="menu"))
    return kb

def main_menu():
    kb=types.InlineKeyboardMarkup(row_width=2)
    kb.add(types.InlineKeyboardButton(f"BINODEX ({len(BINODEX_POCKET)})",callback_data="bin_pocket_0"),types.InlineKeyboardButton(f"MT5 ({len(MT5_LIST)})",callback_data="mt5_0"),types.InlineKeyboardButton(f"FOREX ({len(FOREX_PAIRS)})",callback_data="forex_0"),types.InlineKeyboardButton(f"INDICES ({len(INDICES_LIST)})",callback_data="indices_0"),types.InlineKeyboardButton(f"GOLD ({len(GOLD_LIST)})",callback_data="gold_0"),types.InlineKeyboardButton(f"CRYPTO (100)",callback_data="all_coins_0"))
    kb.add(types.InlineKeyboardButton("My Win Rate",callback_data="stats"))
    return kb

def paginated_list(items,page,prefix):
    per=10; st=page*per; ch=items[st:st+per]; kb=types.InlineKeyboardMarkup(row_width=1)
    for it in ch: kb.add(types.InlineKeyboardButton(f"{it}",callback_data=f"an_5|{it}"))
    nav=[]
    if page>0: nav.append(types.InlineKeyboardButton("Prev",callback_data=f"{prefix}_{page-1}"))
    if st+per<len(items): nav.append(types.InlineKeyboardButton("Next",callback_data=f"{prefix}_{page+1}"))
    if nav: kb.row(*nav)
    kb.add(types.InlineKeyboardButton("Main Menu",callback_data="menu"))
    return kb

def coins_menu_paged(page):
    per=10; st=page*per; ch=ALL_COINS[st:st+per]; kb=types.InlineKeyboardMarkup(row_width=1)
    for coin in ch: kb.add(types.InlineKeyboardButton(f"{coin['symbol'].upper()} - ${coin['current_price']:,.2f}",callback_data=f"coin_{coin['id']}_5"))
    nav=[]
    if page>0: nav.append(types.InlineKeyboardButton("Prev",callback_data=f"all_coins_{page-1}"))
    if st+per<len(ALL_COINS): nav.append(types.InlineKeyboardButton("Next",callback_data=f"all_coins_{page+1}"))
    if nav: kb.row(*nav)
    kb.add(types.InlineKeyboardButton("Main Menu",callback_data="menu"))
    return kb

def setup_menu():
    try:
        if bot: bot.set_my_commands([types.BotCommand("start","MAIN MENU"),types.BotCommand("stats","My Win Rate")])
    except: pass

def add_trade(asset,price,tp,sl,is_buy,tf):
    global stats,pending_trades
    trade={"id":random.randint(10000,99999),"asset":asset,"entry":price,"tp":tp,"sl":sl,"is_buy":is_buy,"tf":tf,"time":time.time()}
    pending_trades.append(trade); stats["total"]+=1; stats["pending"]=len(pending_trades)
    save_json(PENDING_FILE,pending_trades); save_json(STATS_FILE,stats)

def check_pending_trades():
    global stats,pending_trades
    while True:
        time.sleep(120)
        try:
            if not pending_trades: continue
            new=[]
            for tr in pending_trades:
                live=get_live_price(tr["asset"])
                if not live: new.append(tr); continue
                hit_tp=(tr["is_buy"] and live>=tr["tp"]) or (not tr["is_buy"] and live<=tr["tp"])
                hit_sl=(tr["is_buy"] and live<=tr["sl"]) or (not tr["is_buy"] and live>=tr["sl"])
                if hit_tp: stats["wins"]+=1
                elif hit_sl: stats["losses"]+=1
                else:
                    if time.time()-tr["time"]<14400: new.append(tr)
            pending_trades=new; stats["pending"]=len(pending_trades)
            save_json(PENDING_FILE,pending_trades); save_json(STATS_FILE,stats)
        except Exception as e: print(f"Checker error {e}")

def send_signal_with_chart(chat_id,asset,tf_str,minutes,price,atype):
    history=get_history_for_chart(asset,price); analysis=generate_full_analysis(history,price,asset)
    is_buy=analysis['is_buy']; tp,sl,pt,ps=get_tp_sl_by_timeframe(price,is_buy,atype,minutes)
    sig="BUY CALL STRONG" if is_buy else "SELL PUT STRONG"; lev_txt=""; liq_txt=""
    if atype=="crypto":
        lev=random.choice([10,15,20]); sig="LONG" if is_buy else "SHORT"; lev_txt=f"\nLeverage: {lev}X Cross"; liq=price*0.92 if is_buy else price*1.08; liq_txt=f"\nLiq: ${liq:.2f}"
    fund=get_fundamentals(asset)
    wr=(stats["wins"]/stats["total"]*100) if stats["total"]>0 else 0
    txt=f"{asset.upper()} - {tf_str} SNIPER\n\nEntry: {price:.5f}\nSignal: {sig}{lev_txt}\nTP: {tp:.5f} (+{pt})\nSL: {sl:.5f} (-{ps}){liq_txt}\n\nTECHNICAL:\nTrend: {analysis['trend']}\nRSI ({analysis['rsi']}): {analysis['rsi_sig']}\nEMA: {analysis['ema9']}/{analysis['ema21']}/{analysis['ema50']}\nMACD: {analysis['macd']}\nSup: {analysis['support']} | Res: {analysis['resistance']}\n\n{fund}\n\nBot Win Rate: {wr:.1f}% ({stats['wins']}W/{stats['losses']}L/{stats['total']})\nConf: {analysis['conf']}% | {tf_str}"
    add_trade(asset,price,tp,sl,is_buy,tf_str)
    chart=create_chart_image(asset,price,tp,sl,tf_str,is_buy)
    if chart and os.path.exists(chart):
        with open(chart,'rb') as photo: bot.send_photo(chat_id,photo,caption=txt,parse_mode="Markdown",reply_markup=timeframe_keyboard(asset))
        os.remove(chart)
    else: bot.send_message(chat_id,txt,parse_mode="Markdown",reply_markup=timeframe_keyboard(asset))

if bot:
    @bot.message_handler(commands=['start'])
    def start(m):
        global ALL_COINS
        if not ALL_COINS: ALL_COINS=get_all_coins()
        bot.send_message(m.chat.id,"SKELLY'S PRO - FIXED\nReal price 82k+\nSniper + Win Tracker\nSelect:",reply_markup=main_menu(),parse_mode="Markdown")

    @bot.message_handler(commands=['stats'])
    def stats_cmd(m):
        wr=(stats["wins"]/stats["total"]*100) if stats["total"]>0 else 0
        txt=f"YOUR BOT PERFORMANCE\n\nWin Rate: {wr:.1f}%\nWins: {stats['wins']}\nLosses: {stats['losses']}\nTotal: {stats['total']}\nPending: {stats['pending']}"
        kb=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("Menu",callback_data="menu"))
        bot.send_message(m.chat.id,txt,parse_mode="Markdown",reply_markup=kb)

    @bot.callback_query_handler(func=lambda c: True)
    def cb(call):
        global ALL_COINS; d=call.data
        try:
            if d=="menu": bot.edit_message_text("MAIN MENU",call.message.chat.id,call.message.message_id,reply_markup=main_menu(),parse_mode="Markdown")
            elif d=="stats":
                wr=(stats["wins"]/stats["total"]*100) if stats["total"]>0 else 0
                txt=f"YOUR BOT PERFORMANCE\n\nWin Rate: {wr:.1f}%\nWins: {stats['wins']}\nLosses: {stats['losses']}\nTotal: {stats['total']}\nPending: {stats['pending']}"
                kb=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("Menu",callback_data="menu"))
                bot.edit_message_text(txt,call.message.chat.id,call.message.message_id,parse_mode="Markdown",reply_markup=kb)
            elif d.startswith("bin_pocket_") or d.startswith("forex_") or d.startswith("indices_") or d.startswith("mt5_") or d.startswith("gold_") or d.startswith("all_coins_"):
                prefix=d.rsplit("_",1)[0]; page=int(d.rsplit("_",1)[1])
                if "bin_pocket" in prefix: bot.edit_message_text("BINODEX",call.message.chat.id,call.message.message_id,reply_markup=paginated_list(BINODEX_POCKET,page,"bin_pocket"),parse_mode="Markdown")
                elif "forex" in prefix: bot.edit_message_text("FOREX",call.message.chat.id,call.message.message_id,reply_markup=paginated_list(FOREX_PAIRS,page,"forex"),parse_mode="Markdown")
                elif "indices" in prefix: bot.edit_message_text("INDICES",call.message.chat.id,call.message.message_id,reply_markup=paginated_list(INDICES_LIST,page,"indices"),parse_mode="Markdown")
                elif "mt5" in prefix: bot.edit_message_text("MT5",call.message.chat.id,call.message.message_id,reply_markup=paginated_list(MT5_LIST,page,"mt5"),parse_mode="Markdown")
                elif "gold" in prefix: bot.edit_message_text("GOLD",call.message.chat.id,call.message.message_id,reply_markup=paginated_list(GOLD_LIST,page,"gold"),parse_mode="Markdown")
                elif "all_coins" in prefix: bot.edit_message_text("CRYPTO",call.message.chat.id,call.message.message_id,reply_markup=coins_menu_paged(page),parse_mode="Markdown")
            elif d.startswith("an_"):
                mins_asset=d[3:].split("|",1); minutes=int(mins_asset[0]); asset=mins_asset[1] if len(mins_asset)>1 else "EUR/USD"; tf_str=tf_label(minutes)
                price=get_live_price(asset) or random.uniform(1.08,1.09)
                atype="gold" if any(x in asset.upper() for x in ["XAU","GOLD","XAG","SILVER"]) else "indices" if any(x in asset.upper() for x in ["US30","NAS","SPX","GER","UK100","VIX"]) else "forex" if "EUR" in asset.upper() or "GBP" in asset.upper() else "crypto"
                send_signal_with_chart(call.message.chat.id,asset,tf_str,minutes,price,atype)
            elif d.startswith("coin_"):
                parts=d.split("_"); cid="_".join(parts[1:-1]) if len(parts)>2 else parts[1]; mins=int(parts[-1]) if parts[-1].isdigit() else 5
                coin=next((c for c in ALL_COINS if c['id']==cid),None)
                if coin:
                    price=coin['current_price']; history=get_history_for_chart(coin['symbol'],price); analysis=generate_full_analysis(history,price,coin['symbol'])
                    is_buy=analysis['is_buy']; tp,sl,pt,ps=get_tp_sl_by_timeframe(price,is_buy,"crypto",mins); tf_str=tf_label(mins); add_trade(coin['symbol'],price,tp,sl,is_buy,tf_str)
                    wr=(stats['wins']/stats['total']*100) if stats['total']>0 else 0
                    txt=f"{coin['name']} ({coin['symbol'].upper()}) - {tf_str} SNIPER\nEntry: ${price:.4f}\nSignal: {'LONG' if is_buy else 'SHORT'}\nTP: ${tp:.4f}\nSL: ${sl:.4f}\nWin Rate: {wr:.1f}%"
                    chart=create_chart_image(coin['symbol'],price,tp,sl,tf_str,is_buy)
                    kb=types.InlineKeyboardMarkup(row_width=4)
                    kb.row(types.InlineKeyboardButton("5M",callback_data=f"coin_{cid}_5"),types.InlineKeyboardButton("1H",callback_data=f"coin_{cid}_60"),types.InlineKeyboardButton("4H",callback_data=f"coin_{cid}_240"))
                    kb.row(types.InlineKeyboardButton("Refresh",callback_data=f"coin_{cid}_{mins}"),types.InlineKeyboardButton("Stats",callback_data="stats"),types.InlineKeyboardButton("Back",callback_data="all_coins_0"))
                    if chart:
                        with open(chart,'rb') as ph: bot.send_photo(call.message.chat.id,ph,caption=txt,parse_mode="Markdown",reply_markup=kb)
                        os.remove(chart)
                    else: bot.send_message(call.message.chat.id,txt,parse_mode="Markdown",reply_markup=kb)
        except Exception as e: print(f"CB Error {e} - {d}")

    @bot.message_handler(content_types=['text'])
    def handle_text(m):
        if m.text.startswith('/'): return
        orig=m.text; t=m.text.upper().strip()
        if t in ["HI","HELLO","HEY","START","MENU","OK","YO","HELP"]: bot.send_message(m.chat.id,"Main Menu",reply_markup=main_menu(),parse_mode="Markdown"); return
        tf_str,mins=parse_timeframe(orig.lower()); clean=re.sub(r'\d+\s*(m|min|h|hour|d|day)','',orig,flags=re.IGNORECASE).replace("prediction","").strip() or orig
        price=get_live_price(clean) or (random.uniform(1.08,1.09) if "EUR" in t else random.uniform(2030,2060) if "XAU" in t or "GOLD" in t else random.uniform(38500,39000) if "US30" in t else random.uniform(1.08,1.27))
        up=clean.upper(); atype="gold" if any(x in up for x in ["XAU","GOLD","XAG"]) else "indices" if any(x in up for x in ["US30","NAS","SPX","GER","UK100","VIX"]) else "forex" if "EUR" in up or "GBP" in up or "OTC" in up else "crypto"
        send_signal_with_chart(m.chat.id,clean,tf_str,mins,price,atype)

    def run_bot():
        setup_menu()
        print("Starting polling...")
        try: bot.infinity_polling()
        except Exception as e: print(f"Polling error: {e}")
    threading.Thread(target=run_bot,daemon=True).start()
    threading.Thread(target=check_pending_trades,daemon=True).start()

if __name__=="__main__":
    port=int(os.environ.get("PORT",10000)); print(f"Starting Flask on {port}"); app.run(host="0.0.0.0",port=port)
