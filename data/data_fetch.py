import requests
import pandas as pd

ANGEL_INSTRUMENTS_URL = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"


def fetch_instruments():
    try:
        res = requests.get(ANGEL_INSTRUMENTS_URL, timeout=15)
        res.raise_for_status()
        data = res.json()
        return pd.DataFrame(data)
    except Exception as e:
        print(f"⚠️ Instruments fetch error: {e}")
        return pd.DataFrame()


def normalize_expiry(expiry_str):
    """Try multiple formats to parse expiry string into datetime."""
    for fmt in ("%Y-%m-%d", "%d-%b-%Y", "%d-%b-%y"):
        try:
            return pd.to_datetime(expiry_str, format=fmt)
        except Exception:
            continue
    # fallback: let pandas try automatically
    try:
        return pd.to_datetime(expiry_str, errors="coerce")
    except Exception:
        return pd.NaT


def fetch_option_chain(obj, symbol):
    """
    Build option chain manually using instruments master + Quote API.
    Auto-picks nearest upcoming expiry for given symbol (e.g., NIFTY, BANKNIFTY).
    """
    try:
        instruments = fetch_instruments()
        if instruments.empty:
            print("⚠️ Instruments not available")
            return pd.DataFrame()

        # Filter only option contracts for given symbol
        options = instruments[
            (instruments["name"].str.upper() == symbol.upper()) &
            (instruments["instrumenttype"].isin(["OPTIDX", "OPTSTK"]))
        ].copy()

        if options.empty:
            print(f"⚠️ No option contracts found for {symbol}")
            return pd.DataFrame()

        # Normalize expiry column
        options["expiry_parsed"] = options["expiry"].apply(normalize_expiry)

        # Pick nearest valid expiry (>= today)
        expiry_dates = sorted([e for e in options["expiry_parsed"].unique() if pd.notna(e) and e >= pd.Timestamp.today()])
        if not expiry_dates:
            print(f"⚠️ No valid upcoming expiries for {symbol}")
            return pd.DataFrame()
        nearest_expiry = expiry_dates[0]

        options = options[options["expiry_parsed"] == nearest_expiry]

        chain_data = []
        for _, row in options.iterrows():
            try:
                # tradingsymbol / symbol fallback
                tsymbol = (
                    row["tradingsymbol"]
                    if "tradingsymbol" in options.columns and pd.notna(row.get("tradingsymbol"))
                    else row["symbol"]
                )

                # option type fallback
                if "optiontype" in options.columns and pd.notna(row.get("optiontype")):
                    opt_type = row["optiontype"]
                elif "opttype" in options.columns and pd.notna(row.get("opttype")):
                    opt_type = row["opttype"]
                elif isinstance(tsymbol, str) and tsymbol[-2:] in ["CE", "PE"]:
                    opt_type = tsymbol[-2:]
                else:
                    opt_type = None

                # ✅ Use Quote API to fetch LTP + OI safely
                quote = obj.getQuote("NFO", tsymbol, row["token"])
                if "data" in quote and quote["data"] is not None:
                    ltp = quote["data"].get("ltp", None)
                    oi = quote["data"].get("openInterest", 0)  # safe fallback
                else:
                    ltp = None
                    oi = 0

                chain_data.append({
                    "tradingsymbol": tsymbol,
                    "strike": row.get("strike"),
                    "expiry": row.get("expiry"),
                    "option_type": opt_type,
                    "ltp": ltp,
                    "openInterest": oi,  # <-- always present now
                    "token": row.get("token")
                })
            except Exception as e:
                print(f"⚠️ LTP/OI fetch failed for {row.get('symbol', 'UNKNOWN')}: {e}")

        return pd.DataFrame(chain_data)

    except Exception as e:
        print(f"⚠️ Option chain fetch error: {e}")
        return pd.DataFrame()
                    
