
from flask import Flask, request
import requests
import time
import threading
import random

app = Flask(__name__)

BOT_TOKEN = "8701038867:AAG0ND3Ec3I00-ABs75Ybh9e4hlSQr8xfcw"
CHAT_ID = "6528713349"
TELEGRAM_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
EDIT_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

def send_message(text):
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    r = requests.post(TELEGRAM_URL, json=payload)
    return r.json().get("result", {}).get("message_id")

def get_forex_price(pair):
    try:
        # استخدام Finage API مجاني للفوركس
        symbols = {
            "EURUSD": ("EUR", "USD"),
            "GBPUSD": ("GBP", "USD"),
            "USDJPY": ("USD", "JPY"),
            "AUDUSD": ("AUD", "USD"),
            "NZDUSD": ("NZD", "USD"),
            "USDCAD": ("USD", "CAD"),
            "GBPJPY": ("GBP", "JPY"),
        }
        from_cur, to_cur = symbols.get(pair, ("EUR", "USD"))
        url = f"https://api.frankfurter.app/latest?from={from_cur}&to={to_cur}"
        r = requests.get(url, timeout=5)
        data = r.json()
        price = data["rates"][to_cur]
        return price
    except:
        return None

def get_candles(pair):
    try:
        symbols = {
            "EURUSD": "EUR",
            "GBPUSD": "GBP",
            "USDJPY": "USD",
            "AUDUSD": "AUD",
            "NZDUSD": "NZD",
        }
        base = symbols.get(pair, "EUR")
        url = f"https://api.frankfurter.app/2024-01-01..?from={base}&to=USD"
        r = requests.get(url, timeout=5)
        data = r.json()
        rates = list(data["rates"].values())
        closes = [list(r.values())[0] for r in rates[-50:]]
        return closes
    except:
        return None

def calc_rsi(closes, period=7):
    if len(closes) < period + 1:
        return 50
    gains, losses = [], []
    for i in range(1, len(closes)):
        diff = closes[i] - closes[i-1]
        gains.append(max(diff, 0))
        losses.append(max(-diff, 0))
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

def analyze_pair(pair):
    closes = get_candles(pair)
    if not closes or len(closes) < 10:
        return None, None, None

    rsi = calc_rsi(closes)
    ema5 = calc_ema(closes, 5)
    ema13 = calc_ema(closes, 13)
    close = closes[-1]

    bull = 0
    bear = 0

    bull += 2 if rsi < 30 else 1 if rsi < 50 else 0
    bear += 2 if rsi > 70 else 1 if rsi > 50 else 0
    bull += 2 if ema5 > ema13 else 0
    bear += 2 if ema5 < ema13 else 0
    bull += 1 if close > ema13 else 0
    bear += 1 if close < ema13 else 0

    total = bull + bear
    bull_pct = round(bull * 100 / total) if total > 0 else 50
    bear_pct = 100 - bull_pct

    if bull_pct >= 65:
        return "call", bull_pct, close
    elif bear_pct >= 65:
        return "put", bear_pct, close
    return None, None, close

PAIRS = [
    "EURUSD-OTC",
    "GBPUSD-OTC",
    "USDJPY-OTC",
    "AUDUSD-OTC",
    "NZDUSD-OTC",
]

PAIR_KEYS = {
    "EURUSD-OTC": "EURUSD",
    "GBPUSD-OTC": "GBPUSD",
    "USDJPY-OTC": "USDJPY",
    "AUDUSD-OTC": "AUDUSD",
    "NZDUSD-OTC": "NZDUSD",
}

win_count = 0
loss_count = 0
total_count = 0

def track_result(direction, entry_price, pair_key, signal_msg_id):
    global win_count, loss_count, total_count
    time.sleep(62)
    exit_price = get_forex_price(pair_key)
    if not exit_price:
        return
    if direction == "call":
        won = exit_price > entry_price
    else:
        won = exit_price < entry_price
    total_count += 1
    if won:
        win_count += 1
        wr = round(win_count * 100 / total_count)
        send_message(f"WIN ✅\n\n📊 Win Rate: {wr}%\n🏆 {win_count}W / {loss_count}L")
    else:
        loss_count += 1
        wr = round(win_count * 100 / total_count) if total_count > 0 else 0
        send_message(f"❌ Loss\n\n📊 Win Rate: {wr}%\n🏆 {win_count}W / {loss_count}L")

def run_signals():
    global win_count, loss_count, total_count
    time.sleep(5)
    send_message("🤖 <b>HachimSignals2026 Bot</b>\n\n✅ البوت شغال ويرسل إشارات Pocket Option!\n\n💎 M1 - OTC Pairs\n🕐 24/7")

    while True:
        try:
            now = time.localtime()
            current_time = f"{now.tm_hour:02d}:{now.tm_min:02d}:00"

            for pair in PAIRS:
                pair_key = PAIR_KEYS[pair]
                direction, strength, entry_price = analyze_pair(pair_key)

                if direction and entry_price:
                    action = "call" if direction == "call" else "put"
                    emoji = "🔼" if action == "call" else "🔽"
                    wr = round(win_count * 100 / total_count) if total_count > 0 else 0

                    msg = f"""🎯 <b>POCKET OPTION [M1]</b>

🏳 <b>{pair}</b>
💎 M1
🕐 {current_time}
{emoji} <b>{action}</b>

📊 Win Rate: {wr}%
🤖 HachimSignals2026"""

                    msg_id = send_message(msg)
                    time.sleep(2)

                    t = threading.Thread(
                        target=track_result,
                        args=(direction, entry_price, pair_key, msg_id)
                    )
                    t.daemon = True
                    t.start()

            time.sleep(60)

        except Exception as e:
            send_message(f"❌ خطأ: {str(e)}")
            time.sleep(30)

@app.route("/", methods=["GET"])
def home():
    return "✅ HachimSignals2026 is running!", 200

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json(force=True)
        raw = str(data) if data else request.data.decode("utf-8")
        send_message(f"📊 TradingView Signal\n\n{raw}")
        return "ok", 200
    except:
        return "error", 500

if __name__ == "__main__":
    import os
    t = threading.Thread(target=run_signals)
    t.daemon = True
    t.start()
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
