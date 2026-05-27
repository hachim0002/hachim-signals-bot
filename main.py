from flask import Flask, request
import requests
import time
import threading

app = Flask(__name__)

BOT_TOKEN = "8701038867:AAG0ND3Ec3I00-ABs75Ybh9e4hlSQr8xfcw"
CHAT_ID = "6528713349"
TELEGRAM_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

def send_message(text):
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    requests.post(TELEGRAM_URL, json=payload)

def get_price(symbol):
    try:
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1m&limit=50"
        r = requests.get(url, timeout=5)
        data = r.json()
        closes = [float(k[4]) for k in data]
        highs = [float(k[2]) for k in data]
        lows = [float(k[3]) for k in data]
        volumes = [float(k[5]) for k in data]
        return closes, highs, lows, volumes
    except:
        return None, None, None, None

def calc_rsi(closes, period=7):
    gains, losses = [], []
    for i in range(1, len(closes)):
        diff = closes[i] - closes[i-1]
        gains.append(max(diff, 0))
        losses.append(max(-diff, 0))
    if len(gains) < period:
        return 50
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def calc_ema(closes, period):
    if len(closes) < period:
        return closes[-1]
    k = 2 / (period + 1)
    ema = sum(closes[:period]) / period
    for price in closes[period:]:
        ema = price * k + ema * (1 - k)
    return ema

def calc_macd(closes):
    ema12 = calc_ema(closes, 12)
    ema26 = calc_ema(closes, 26)
    return ema12 - ema26

def calc_bb(closes, period=20):
    if len(closes) < period:
        return closes[-1], closes[-1], closes[-1]
    recent = closes[-period:]
    mid = sum(recent) / period
    std = (sum((x - mid) ** 2 for x in recent) / period) ** 0.5
    return mid + 2 * std, mid, mid - 2 * std

def analyze(symbol, display_name):
    closes, highs, lows, volumes = get_price(symbol)
    if not closes:
        return None

    close = closes[-1]
    rsi = calc_rsi(closes)
    ema5 = calc_ema(closes, 5)
    ema13 = calc_ema(closes, 13)
    ema21 = calc_ema(closes, 21)
    macd = calc_macd(closes)
    bb_up, bb_mid, bb_dn = calc_bb(closes)

    bull = 0
    bear = 0

    bull += 2 if rsi < 30 else 1 if rsi < 50 else 0
    bear += 2 if rsi > 70 else 1 if rsi > 50 else 0

    bull += 2 if ema5 > ema13 else 0
    bear += 2 if ema5 < ema13 else 0

    bull += 1 if ema13 > ema21 else 0
    bear += 1 if ema13 < ema21 else 0

    bull += 2 if macd > 0 else 0
    bear += 2 if macd < 0 else 0

    bull += 3 if close <= bb_dn else 0
    bear += 3 if close >= bb_up else 0

    bull += 1 if close > bb_mid else 0
    bear += 1 if close < bb_mid else 0

    vol_avg = sum(volumes[-20:]) / 20
    bull += 1 if volumes[-1] > vol_avg * 1.2 and closes[-1] > closes[-2] else 0
    bear += 1 if volumes[-1] > vol_avg * 1.2 and closes[-1] < closes[-2] else 0

    total = bull + bear
    bull_pct = round(bull * 100 / total) if total > 0 else 50
    bear_pct = 100 - bull_pct

    if bull_pct >= 65:
        direction = "CALL"
        emoji = "🟢"
        action = "CALL ▲ شراء"
    elif bear_pct >= 65:
        direction = "PUT"
        emoji = "🔴"
        action = "PUT ▼ بيع"
    else:
        return None

    strength = "💎 مثالي" if bull_pct >= 80 or bear_pct >= 80 else "🔥 قوي" if bull_pct >= 70 or bear_pct >= 70 else "✅ جيد"

    msg = f"""
{emoji} <b>{action}</b>

📌 <b>الزوج:</b> {display_name}
💰 <b>السعر:</b> {round(close, 5)}
📊 <b>RSI:</b> {round(rsi, 1)}
💪 <b>القوة:</b> {strength}
📈 <b>CALL:</b> {bull_pct}% | <b>PUT:</b> {bear_pct}%
⏱ <b>الفريم:</b> 1 دقيقة

🤖 <b>HachimSignals2026</b>
"""
    return msg

PAIRS = [
    ("EURUSDT", "EUR/USD"),
    ("GBPUSDT", "GBP/USD"),
    ("GBPJPY", "GBP/JPY"),
    ("USDJPY", "USD/JPY"),
    ("AUDUSD", "AUD/USD"),
]

def run_analysis():
    send_message("🤖 <b>HachimSignals2026 شغال!</b>\n\nسأرسل إشارات كل دقيقة 🚀")
    while True:
        for symbol, name in PAIRS:
            msg = analyze(symbol, name)
            if msg:
                send_message(msg)
                time.sleep(2)
        time.sleep(60)

@app.route("/", methods=["GET"])
def home():
    return "✅ HachimSignals2026 Bot is running!", 200

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json(force=True)
        raw = str(data) if data else request.data.decode("utf-8")
        send_message(f"📊 <b>إشارة من TradingView</b>\n\n{raw}")
        return "ok", 200
    except Exception as e:
        return "error", 500

if __name__ == "__main__":
    import os
    t = threading.Thread(target=run_analysis)
    t.daemon = True
    t.start()
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
