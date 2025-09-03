import os
from SmartApi import SmartConnect
import pyotp


def angel_login():
    try:
        api_key = os.getenv("ANGEL_API_KEY")
        client_code = os.getenv("ANGEL_CLIENT_CODE")
        totp_secret = os.getenv("ANGEL_TOTP_SECRET")

        obj = SmartConnect(api_key=api_key)
        totp = pyotp.TOTP(totp_secret).now()
        data = obj.generateSession(client_code, totp)

        if not data or "data" not in data:
            print("⚠️ Login Error")
            return None, None

        jwt_token = data["data"]["jwtToken"]
        print("✅ AngelOne Login Success")
        return obj, jwt_token

    except Exception as e:
        print(f"⚠️ Login Error: {e}")
        return None, None
