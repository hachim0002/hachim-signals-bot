import asyncio
from datetime import datetime, timedelta
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
            await client.post(f"{API}/sendMessage", json={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"})
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

def calc_rsi(closes, period=7):
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

def get_support_resistance(closes, period=20):
    if len(closes) < period:
        return None, None
    recent = closes[-period:]
    resistance = max(recent)
    support = min(recent)
    return support, resistance

def get_trend(closes):
    if len(closes) < 50:
        return "NEUTRAL"
    ema20 = ema(closes, 20)
    ema50 = ema(closes, 50)
    if ema20 is None or ema50 is None:
        return "NEUTRAL"
    if ema20 > ema50:
        return "UP"
    elif ema20 < ema50:
        return "DOWN"
    return "NEUTRAL"

async def get_closes(symbol):
    headers_list = [
        {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36", "Accept": "application/json", "Referer": "https://finance.yahoo.com"},
        {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Safari/537.36", "Accept": "*/*"},
        {"User-Agent": "python-httpx/0.27.0", "Accept": "application/json"}
    ]
    urls = [
        f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1m&range=1d",
        f"https://query2.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1m&range=1d"
    ]
    for url in urls:
        for headers in headers_list:
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
            await asyncio.sleep(1)
    return []

def calc_signal(closes):
    if len(closes) < 50:
        return None, None, None

    price = closes[-1]
    ema7 = ema(closes, 7)
    ema21 = ema(closes, 21)
    prev_ema7 = ema(closes[:-1], 7)
    prev_ema21 = ema(closes[:-1], 21)

    if None in [ema7, ema21, prev_ema7, prev_ema21]:
        return None, None, None

    rsi = calc_rsi(closes, 7)
    bb_up, bb_mid, bb_dn = bollinger(closes)
    support, resistance = get_support_resistance(closes)
    trend = get_trend(closes)

    if bb_up is None or support is None:
        return None, None, None

    cross_up = prev_ema7 <= prev_ema21 and ema7 > ema21
    cross_dn = prev_ema7 >= prev_ema21 and ema7 < ema21
    near_support = price <= support * 1.003
    near_resistance = price >= resistance * 0.997
    bb_bounce_bull = price <= bb_dn * 1.002
    bb_bounce_bear = price >= bb_up * 0.998

    bull_score = 0
    bear_score = 0

    bull_score += 3 if cross_up else 0
    bear_score += 3 if cross_dn else 0
    bull_score += 2 if rsi < 30 else 1 if rsi < 45 else 0
    bear_score += 2 if rsi > 70 else 1 if rsi > 55 else 0
    bull_score += 2 if bb_bounce_bull else 0
    bear_score += 2 if bb_bounce_bear else 0
    bull_score += 2 if near_support else 0
    bear_score += 2 if near_resistance else 0
    bull_score += 1 if trend == "UP" else 0
    bear_score += 1 if trend == "DOWN" else 0
    bull_score += 1 if ema7 > ema21 else 0
    bear_score += 1 if ema7 < ema21 else 0

    total = bull_score + bear_score
    bull_pct = round(bull_score * 100 / total) if total > 0 else 50
    bear_pct = 100 - bull_pct

    if bull_pct >= 65 and trend != "DOWN":
        return "call", price, bull_pct
    if bear_pct >= 65 and trend != "UP":
        return "put", price, bear_pct

    return None, None, None

def get_entry_time():
    now = datetime.now()
    entry = now + timedelta(minutes=2)
    entry = entry.replace(second=0, microsecond=0)
    return now.strftime("%H:%M:00"), entry.strftime("%H:%M:00")

async def check_result(pair, signal, entry_price, symbol):
    await asyncio.sleep(65)
    closes = await get_closes(symbol)
    if not closes:
        return
    exit_price = closes[-1]
    won = exit_price > entry_price if signal == "call" else exit_price < entry_price
    diff = abs(exit_price - entry_price)
    result = "✅ WIN" if won else "❌ LOSE"
    text = (
        f"{result}\n\n"
        f"📊 {pair}\n"
        f"📈 Entry: {round(entry_price, 5)}\n"
        f"📉 Exit: {round(exit_price, 5)}\n"
        f"📏 Diff: {round(diff, 5)}"
    )
    await send_msg(text)

async def run():
    await send_msg(
        "🤖 <b>@HachimSignals2026_bot</b>\n"
        "🚀 البوت شغال!\n"
        "📊 يراقب السوق...\n\n"
        "⚙️ <b>الإعدادات:</b>\n"
        "📈 EMA 7 / EMA 21\n"
        "📊 RSI 7\n"
        "🎯 Bollinger Bands\n"
        "🔲 دعم ومقاومة\n"
        "🔍 فلتر الاتجاه العام"
    )

    sent = {}

    while True:
        try:
            now = datetime.now()
            minute_key = now.strftime("%Y%m%d%H%M")

            for pair, symbol in PAIRS.items():
                closes = await get_closes(symbol)
                if not closes:
                    continue

                signal, entry, strength = calc_signal(closes)
                key = f"{pair}_{minute_key}"

                if signal and key not in sent:
                    sent[key] = True

                    signal_time, entry_time = get_entry_time()
                    arrow = "🔼 CALL" if signal == "call" else "🔽 PUT"
                    trend = get_trend(closes)
                    rsi = calc_rsi(closes, 7)
                    bb_up, bb_mid, bb_dn = bollinger(closes)
                    support, resistance = get_support_resistance(closes)
                    ema7 = ema(closes, 7)
                    ema21 = ema(closes, 21)
                    trend_emoji = "📈" if trend == "UP" else "📉" if trend == "DOWN" else "➖"

                    msg = (
                        f"🤖 <b>@HachimSignals2026_bot</b>\n\n"
                        f"💼 <b>POCKET OPTION [M1]</b>\n\n"
                        f"📊 <b>{pair}</b>\n"
                        f"💎 M1\n\n"
                        f"🕐 <b>وقت الإشارة:</b> {signal_time}\n"
                        f"⏰ <b>وقت الدخول:</b> {entry_time}\n\n"
                        f"{arrow}\n\n"
                        f"📊 <b>التحليل:</b>\n"
                        f"• RSI: {round(rsi, 1)}\n"
                        f"• EMA7: {round(ema7, 5)}\n"
                        f"• EMA21: {round(ema21, 5)}\n"
                        f"• BB Up: {round(bb_up, 5) if bb_up else 'N/A'}\n"
                        f"• BB Dn: {round(bb_dn, 5) if bb_dn else 'N/A'}\n"
                        f"• دعم: {round(support, 5) if support else 'N/A'}\n"
                        f"• مقاومة: {round(resistance, 5) if resistance else 'N/A'}\n"
                        f"• الاتجاه: {trend_emoji} {trend}\n"
                        f"• القوة: {strength}%"
                    )

                    await send_msg(msg)
                    asyncio.create_task(check_result(pair, signal, entry, symbol))
                    await asyncio.sleep(2)

            if len(sent) > 300:
                sent.clear()

            await asyncio.sleep(50)

        except Exception as e:
            print("Main Error:", e)
            await asyncio.sleep(60)

asyncio.run(run())
