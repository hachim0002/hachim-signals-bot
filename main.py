import asyncio
from datetime import datetime
from aiohttp import web
import httpx

TOKEN = "8701038867:AAG0ND3Ec3I00-ABs75Ybh9e4hlSQr8xfcw"
CHAT_ID = "6528713349"
API = f"https://api.telegram.org/bot{TOKEN}"

PAIRS = [
    "EUR/USD OTC",
    "GBP/USD OTC",
    "AUD/USD OTC",
    "USD/JPY OTC",
    "EUR/GBP OTC"
]

def get_signal(closes):
    if len(closes) < 14:
        return None
    ema9 = closes[-1]
    for p in closes[-9:]:
        ema9 = ema9 * 0.2 + p * 0.8
    ema21 = closes[-1]
    for p in closes[-21:]:
        ema21 = ema21 * 0.1 + p * 0.9
    gains = [max(closes[i]-closes[i-1],0) for i in range(1,15)]
    losses = [max(closes[i-1]-closes[i],0) for i in range(1,15)]
    avg_gain = sum(gains)/14
    avg_loss = sum(losses)/14
    rsi = 100 - (100/(1+(avg_gain/avg_loss+0.0001)))
    if ema9 > ema21 and rsi < 60 and rsi > 40:
        return "CALL"
    if ema9 < ema21 and rsi > 40 and rsi < 60:
        return "PUT"
    return None

async def send_msg(text):
    async with httpx.AsyncClient() as client:
        await client.post(f"{API}/sendMessage", json={"chat_id": CHAT_ID, "text": text})

async def get_price_data(pair):
    symbols = {
        "EUR/USD OTC": "EURUSD=X",
        "GBP/USD OTC": "GBPUSD=X",
        "AUD/USD OTC": "AUDUSD=X",
        "USD/JPY OTC": "USDJPY=X",
        "EUR/GBP OTC": "EURGBP=X"
    }
    symbol = symbols.get(pair, "EURUSD=X")
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1m&range=1d"
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            data = r.json()
            closes = data["chart"]["result"][0]["indicators"]["quote"][0]["close"]
            closes = [c for c in closes if c is not None]
            return closes
    except:
        return []

async def check_signals():
    while True:
        try:
            now = datetime.now().strftime("%H:%M:%S")
            for pair in PAIRS:
                closes = await get_price_data(pair)
                signal = get_signal(closes)
                if signal:
                    arrows = "⬆️⬆️⬆️ 📈" if signal == "CALL" else "⬇️⬇️⬇️ 📉"
                    emoji = "🟢" if signal == "CALL" else "🔴"
                    msg = (
                        f"🚀 {pair} 1 MIN SIGNAL 🤝\n"
                        f"{arrows} STRONG {signal} SIGNAL {arrows}\n"
                        f"━━━━━━━━━━━━━━━━\n"
                        f"💹 الزوج: {pair}\n"
                        f"⏰ التوقيت: {now}\n"
                        f"🕐 مدة الصفقة: 1 MIN\n"
                        f"💪 القوة: STRONG\n"
                        f"{emoji} الاتجاه: {signal}\n"
                        f"━━━━━━━━━━━━━━━━\n"
                        f"⚠️ إدارة المخاطر دائماً"
                    )
                    await send_msg(msg)
                    print(f"✅ {pair}: {signal}")
            await asyncio.sleep(60)
        except Exception as e:
            print(f"Error: {e}")
            await asyncio.sleep(60)

async def main():
    await send_msg("🚀 البوت شغال الآن!\n📊 يراقب السوق كل دقيقة...")
    await check_signals()

asyncio.run(main())
