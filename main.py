import asyncio
from datetime import datetime
import httpx
import math

TOKEN = "8701038867:AAHcexuGG30003Z87Iyx_LDGpfI5XoD9N3w"
CHAT_ID = "6141369575"
API = f"https://api.telegram.org/bot{TOKEN}"

PAIRS = {
    "EURGBP-OTC": "EURGBP=X",
    "EURUSD-OTC": "EURUSD=X",
    "GBPUSD-OTC": "GBPUSD=X",
    "AUDUSD-OTC": "AUDUSD=X",
    "CADCHF-OTC": "CADCHF=X",
    "USDJPY-OTC": "USDJPY=X"
}

async def send_msg(text):
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            await client.post(f"{API}/sendMessage", json={"chat_id": CHAT_ID, "text": text})
    except Exception as e:
        print("Telegram Error:", e)

def ema(data, period):
    if len(data) < period:
        return None
    k = 2 / (period + 1)
    value = sum(data[:period]) / period
    for price in data[period:]:
        value = price * k + value * (1 - k)
    return value

def calc_rsi(closes, period=14):
    if len(closes) < period + 1:
        return 50
    gains = []
    losses = []
    for i in range(-period, 0):
        diff = closes[i] - closes[i-1]
        if diff > 0:
            gains.append(diff)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(diff))
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def bollinger(closes, period=20):
    if len(closes) < period:
        return None, None, None
    mid = sum(closes[-period:]) / period
    variance = sum((c - mid)**2 for c in closes[-period:]) / period
    std = math.sqrt(variance)
    return mid + 2*std, mid, mid - 2*std

async def get_closes(symbol):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1m&range=2d"
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            data = r.json()
            closes = data["chart"]["result"][0]["indicators"]["quote"][0]["close"]
            return [x for x in closes if x is not None]
    except Exception as e:
        print("Price Error:", e)
        return []

def calc_signal(closes):
    if len(closes) < 50:
        return None, None
    price = closes[-1]
    ema9 = ema(closes, 9)
    ema21 = ema(closes, 21)
    ema50 = ema(closes, 50)
    prev_ema9 = ema(closes[:-1], 9)
    prev_ema21 = ema(closes[:-1], 21)
    if None in [ema9, ema21, ema50]:
        return None, None
    rsi = calc_rsi(closes)
    bb_up, bb_mid, bb_dn = bollinger(closes)
    if bb_up is None:
        return None, None
    trend_bull = ema9 > ema50
    trend_bear = ema9 < ema50
    cross_up = prev_ema9 <= prev_ema21 and ema9 > ema21
    cross_dn = prev_ema9 >= prev_ema21 and ema9 < ema21
    near_support = price <= bb_dn * 1.001
    near_resistance = price >= bb_up * 0.999
    ema_distance = abs(ema9 - ema21)
    if ema_distance < price * 0.00005:
        return None, None
    bull_rsi = rsi < 40
    bear_rsi = rsi > 60
    bull_rejection = closes[-1] > closes[-2] and closes[-2] < closes[-3]
    bear_rejection = closes[-1] < closes[-2] and closes[-2] > closes[-3]
    if cross_up and trend_bull and bull_rsi and near_support and bull_rejection:
        return "call", price
    if cross_dn and trend_bear and bear_rsi and near_resistance and bear_rejection:
        return "put", price
    return None, None

async def check_result(pair, signal, entry_price, symbol):
    await asyncio.sleep(65)
    closes = await get_closes(symbol)
    if not closes:
        return
    exit_price = closes[-1]
    won = exit_price > entry_price if signal == "call" else exit_price < entry_price
    diff = abs(exit_price - entry_price)
    text = (
        f"{'✅ WIN' if won else '❌ LOSE'}\n\n"
        f"📊 {pair}\n"
        f"📈 Entry: {round(entry_price, 5)}\n"
        f"📉 Exit: {round(exit_price, 5)}\n"
        f"📏 Diff: {round(diff, 5)}"
    )
    await send_msg(text)

async def run():
    await send_msg("🤖 @HachimSignals2026_bot\n🚀 البوت شغال!\n📊 يراقب السوق...")
    sent = {}
    while True:
        try:
            now = datetime.now()
            minute_key = now.strftime("%Y%m%d%H%M")
            for pair, symbol in PAIRS.items():
                closes = await get_closes(symbol)
                signal, entry = calc_signal(closes)
                key = f"{pair}_{minute_key}"
                if signal and key not in sent:
                    sent[key] = True
                    arrow = "🔼 CALL" if signal == "call" else "🔽 PUT"
                    msg = (
                        f"🤖 @HachimSignals2026_bot\n\n"
                        f"💼 POCKET OPTION [M1]\n\n"
                        f"📊 {pair}\n"
                        f"💎 M1\n"
                        f"⌚ {now.strftime('%H:%M:00')}\n"
                        f"{arrow}"
                    )
                    await send_msg(msg)
                    asyncio.create_task(check_result(pair, signal, entry, symbol))
                await asyncio.sleep(1)
            if len(sent) > 300:
                sent.clear()
            await asyncio.sleep(55)
        except Exception as e:
            print("Main Error:", e)
            await asyncio.sleep(60)

asyncio.run(run())
