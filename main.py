import asyncio
from datetime import datetime
import httpx
import yfinance as yf
import pandas_ta as ta

TOKEN = "8701038867:AAG0ND3Ec3I00-ABs75Ybh9e4hlSQr8xfcw"
CHAT_ID = "6528713349"
API = f"https://api.telegram.org/bot{TOKEN}"

PAIRS = {
    "EUR/USD OTC": "EURUSD=X",
    "GBP/USD OTC": "GBPUSD=X",
    "AUD/USD OTC": "AUDUSD=X",
    "USD/JPY OTC": "USDJPY=X",
    "EUR/GBP OTC": "EURGBP=X"
}

async def send_msg(text):
    async with httpx.AsyncClient() as client:
        await client.post(f"{API}/sendMessage", json={"chat_id": CHAT_ID, "text": text})

def get_signal(symbol):
    df = yf.download(symbol, period="1d", interval="1m", progress=False)
    if df is None or len(df) < 20:
        return None
    df["ema9"] = ta.ema(df["Close"], length=9)
    df["ema21"] = ta.ema(df["Close"], length=21)
    df["rsi"] = ta.rsi(df["Close"], length=7)
    psar = ta.psar(df["High"], df["Low"], df["Close"])
    df["psar"] = psar["PSARl_0.02_0.2"] if "PSARl_0.02_0.2" in psar.columns else None
    last = df.iloc[-1]
    prev = df.iloc[-2]
    call = (
        last["ema9"] > last["ema21"] and
        last["rsi"] < 60 and
        last["rsi"] > 40 and
        last["Close"] > last["psar"] and
        prev["Close"] < prev["psar"]
    )
    put = (
        last["ema9"] < last["ema21"] and
        last["rsi"] > 40 and
        last["rsi"] < 60 and
        last["Close"] < last["psar"] and
        prev["Close"] > prev["psar"]
    )
    return "CALL" if call else "PUT" if put else None

async def check_signals():
    while True:
        try:
            now = datetime.now().strftime("%H:%M:%S")
            for pair_name, symbol in PAIRS.items():
                signal = get_signal(symbol)
                if signal:
                    arrows = "⬆️⬆️⬆️ 📈" if signal == "CALL" else "⬇️⬇️⬇️ 📉"
                    emoji = "🟢" if signal == "CALL" else "🔴"
                    msg = (
                        f"🚀 {pair_name} 1 MIN SIGNAL 🤝\n"
                        f"{arrows} STRONG {signal} SIGNAL {arrows}\n"
                        f"━━━━━━━━━━━━━━━━\n"
                        f"💹 الزوج: {pair_name}\n"
                        f"⏰ التوقيت: {now}\n"
                        f"🕐 مدة الصفقة: 1 MIN\n"
                        f"💪 القوة: STRONG\n"
                        f"{emoji} الاتجاه: {signal}\n"
                        f"━━━━━━━━━━━━━━━━\n"
                        f"⚠️ إدارة المخاطر دائماً"
                    )
                    await send_msg(msg)
                    print(f"✅ {pair_name}: {signal}")
            await asyncio.sleep(60)
        except Exception as e:
            print(f"Error: {e}")
            await asyncio.sleep(60)

async def main():
    await send_msg("🚀 البوت شغال الآن!\n📊 يراقب السوق كل دقيقة...")
    await check_signals()

asyncio.run(main())
