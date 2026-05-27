from flask import Flask, request
import requests
import json

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

@app.route("/", methods=["GET"])
def home():
    return "✅ Bot is running!", 200

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json(force=True)
        if not data:
            raw = request.data.decode("utf-8")
            msg = f"📊 <b>إشارة جديدة</b>\n\n{raw}"
            send_message(msg)
            return "ok", 200

        direction = data.get("direction", "")
        symbol = data.get("symbol", "")
        price = data.get("price", "")
        strength = data.get("strength", "")
        pattern = data.get("pattern", "")
        timeframe = data.get("timeframe", "1m")

        if direction == "CALL":
            emoji = "🟢"
            action = "CALL ▲ شراء"
        elif direction == "PUT":
            emoji = "🔴"
            action = "PUT ▼ بيع"
        else:
            emoji = "⚪"
            action = direction

        msg = f"""
{emoji} <b>{action}</b>

📌 <b>الزوج:</b> {symbol}
💰 <b>السعر:</b> {price}
⏱ <b>الفريم:</b> {timeframe}
💪 <b>القوة:</b> {strength}
🕯️ <b>النمط:</b> {pattern}

🤖 <b>HachimSignals2026</b>
"""
        send_message(msg)
        return "ok", 200

    except Exception as e:
        send_message(f"❌ خطأ: {str(e)}")
        return "error", 500

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
