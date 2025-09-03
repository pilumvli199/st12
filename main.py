from login.angel_login import angel_login
from data.data_fetch import fetch_option_chain
from analysis.analyze_option_chain import analyze_option_chain
from utils.telegram_bot import send_telegram_message


def run_bot():
    # Login
    obj, jwt_token = angel_login()
    if not obj or not jwt_token:
        print("❌ Login failed, exiting...")
        return

    print("✅ Login success")

    # Symbols to scan
    symbols = ["NIFTY", "BANKNIFTY"]

    for symbol in symbols:
        try:
            print(f"🔍 Fetching option chain for {symbol}...")
            df = fetch_option_chain(obj, symbol)

            if df.empty:
                print(f"⚠️ Option chain empty for {symbol}")
                continue

            signal = analyze_option_chain(df)
            if signal:
                alert_msg = f"📊 {symbol} Option Chain Analysis\n{signal}"
                print(alert_msg)
                send_telegram_message(alert_msg)
            else:
                print(f"⚠️ No signal generated for {symbol}")

        except Exception as e:
            print(f"⚠️ Error processing {symbol}: {e}")


if __name__ == "__main__":
    run_bot()
