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
    urls = [
        f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1m&range=2d",
        f"https://query2.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1m&range=2d"
    ]
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
        "Referer": "https://finance.yahoo.com"
    }
    for url in urls:
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                r = await client.get(url, headers=headers)
                if r.status_code == 200:
                    data = r.json()
                    closes = data["chart"]["result"][0]["indicators"]["quote"][0]["close"]
                    result = [x for x in closes if x is not None]
                    if len(result) > 10:
                        return result
        except Exception as e:
            print("Price Error:", e)
    return []

def calc_signal(closes):
    if len(closes) < 30:
        return None, None
    price = closes[-1]
    ema21 = ema(closes, 21)
    prev_ema21 = ema(closes[:-1], 21)
    ema7 = ema(closes, 7)
    prev_ema7 = ema(closes[:-1], 7)
    if None in [ema9, ema21, prev_ema9, prev_ema21]:
        return None, None
    rsi = calc_rsi(closes, 7)
    bb_up, bb_mid, bb_dn = bollinger(closes)
    if bb_up is None:
        return None, None
    cross_up = prev_ema7 <= prev_ema21 and ema7 > ema21
    cross_dn = prev_ema7 >= prev_ema21 and ema7 < ema21
    near_support = price <= bb_dn * 1.003
    near_resistance = price >= bb_up * 0.997
    if cross_up and rsi < 55 and near_support:
        return "call", price
    if cross_dn and rsi > 45 and near_resistance:
        return "put", price
    if cross_up and rsi < 45:
        return "call", price
    if cross_dn and rsi > 55:
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
