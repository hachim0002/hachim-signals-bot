import asyncio
import json
from datetime import datetime
from aiohttp import web
import httpx

TOKEN = "8701038867:AAG0ND3Ec3I00-ABs75Ybh9e4hlSQr8xfcw"
CHAT_ID = "6528713349"
API = f"https://api.telegram.org/bot{TOKEN}"

async def send_msg(text):
    async with httpx.AsyncClient() as client:
        await client.post(f"{API}/sendMessage", json={"chat_id": CHAT_ID, "text": text})

async def handle_webhook(request):
    try:
        data = await request.json()
        pair = data.get("pair", "EUR/USD OTC")
        direction = data.get("direction", "BUY")
        timeframe = data.get("timeframe", "1 MIN")
        strength = data.get("strength", "STRONG")
        now = datetime.now().strftime("%H:%M:%S")
        action = "CALL" if direction.upper() in ["BUY","CALL"] else "PUT"
        arrows = "⬆️⬆️⬆️ 📈" if action == "CALL" else "⬇️⬇️⬇️ 📉"
        emoji = "🟢" if action == "CALL" else "🔴"
        msg = f"🚀 {pair} {timeframe} SIGNAL 🤝\n{arrows} {strength} {action} SIGNAL {arrows}\n━━━━━━━━━━━━━━━━\n💹 الزوج: {pair}\n⏰ التوقيت: {now}\n🕐 مدة الصفقة: {timeframe}\n💪 القوة: {strength}\n{emoji} الاتجاه: {action}\n━━━━━━━━━━━━━━━━\n⚠️ إدارة المخاطر دائماً"
        await send_msg(msg)
        return web.Response(text="OK", status=200)
    except Exception as e:
        print(f"Error: {e}")
        return web.Response(text="Error", status=500)

async def handle_home(request):
    return web.Response(text="Bot Running!", status=200)

async def main():
    await send_msg("🚀 البوت شغال الآن!")
    app = web.Application()
    app.router.add_get("/", handle_home)
    app.router.add_post("/webhook", handle_webhook)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()
    print("Server running...")
    while True:
        await asyncio.sleep(3600)

asyncio.run(main())
