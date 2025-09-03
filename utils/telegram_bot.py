import os
import requests


def send_telegram_message(message: str):
    try:
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        if not bot_token or not chat_id:
            print("⚠️ Telegram credentials missing in .env")
            return

        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {"chat_id": chat_id, "text": message}
        requests.post(url, data=payload)
        print("📩 Telegram Alert Sent")

    except Exception as e:
        print(f"⚠️ Telegram send error: {e}")
