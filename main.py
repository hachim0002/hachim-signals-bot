import asyncio
import json
from datetime import datetime
from aiohttp import web
from telegram import Bot

TOKEN = "8701038867:AAG0ND3Ec3I00-ABs75Ybh9e4hlSQr8xfcw"
CHAT_ID = "6528713349"

bot = Bot(token=TOKEN)

async def send_signal(pair, direction, timeframe, strength):
    now = datetime.now().strftime("%H:%M:%S")
    if direction.upper() in ["BUY", "CALL"]:
        arrows = "⬆️⬆️⬆️"
        chart = "📈"
        emoji = "🟢"
        action = "CALL"
    else:
        arrows = "⬇️⬇️⬇️"
        chart = "📉"
        emoji = "🔴"
        action = "PUT"
    msg = (
        f"🚀 {pair} {timeframe} SIGNAL 🤝\n"
        f"{arrows} {chart} {strength} {action} SIGNAL {chart}{arrows}\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"💹 الزوج: {pair}\n"
        f"⏰ التوقيت: {now}\n"
        f"🕐 مدة الصفقة: {timeframe}\n"
        f"💪 القوة: {strength}\n"
        f"{emoji} الاتجاه: {action}\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"⚠️ إدارة المخاطر دائماً"
    )
    await bot.send_message(chat_id=CHAT_ID, text=msg)
    print(f"✅ إشارة أرسلت: {pair} {action} {now}")

async def handle_webhook(request):
    try:
        data = await request.json()
        pair = data.get("pair", "EUR/USD OTC")
        direction = data.get("direction", "BUY")
        timeframe = data.get("timeframe", "1 MIN")
        strength = data.get("strength", "STRONG")
        await send_signal(pair, direction, timeframe, strength)
        return web.Response(text="OK", status=200)
    except Exception as e:
        print(f"❌ خطأ: {e}")
        return web.Response(text="Error", status=500)

async def handle_home(request):
    return web.Response(text="البوت شغال!", status=200)

async def main():
    await bot.send_message(
        chat_id=CHAT_ID,
        text="🚀 بوت الإشارات شغال!\n📊 في انتظار إشارات TradingView..."
    )
    app = web.Application()
    app.router.add_get("/", handle_home)
    app.router.add_post("/webhook", handle_webhook)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()
    print("السيرفر شغال على port 8080")
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
