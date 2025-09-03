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
    for fmt in ("%Y-%m-%d", "%d-%b-%Y", "%d-%b-%y"):
        try:
            return pd.to_datetime(expiry_str, format=fmt)
        except Exception:
            continue
    try:
        return pd.to_datetime(expiry_str, errors="coerce")
    except Exception:
        return pd.NaT


def fetch_option_chain(obj, symbol):
    try:
        instruments = fetch_instruments()
        if instruments.empty:
            print("⚠️ Instruments not available")
            return pd.DataFrame()

        options = instruments[
            (instruments["name"].str.upper() == symbol.upper()) &
            (instruments["instrumenttype"].isin(["OPTIDX", "OPTSTK"]))
        ].copy()

        if options.empty:
            print(f"⚠️ No option contracts found for {symbol}")
            return pd.DataFrame()

        options["expiry_parsed"] = options["expiry"].apply(normalize_expiry)
        expiry_dates = sorted([e for e in options["expiry_parsed"].unique() if pd.notna(e) and e >= pd.Timestamp.today()])
        if not expiry_dates:
            print(f"⚠️ No valid upcoming expiries for {symbol}")
            return pd.DataFrame()
        nearest_expiry = expiry_dates[0]

        options = options[options["expiry_parsed"] == nearest_expiry]

        chain_data = []
        for _, row in options.iterrows():
            try:
                tsymbol = (
                    row["tradingsymbol"]
                    if "tradingsymbol" in options.columns and pd.notna(row.get("tradingsymbol"))
                    else row["symbol"]
                )

                if "optiontype" in options.columns and pd.notna(row.get("optiontype")):
                    opt_type = row["optiontype"]
                elif "opttype" in options.columns and pd.notna(row.get("opttype")):
                    opt_type = row["opttype"]
                elif isinstance(tsymbol, str) and tsymbol[-2:] in ["CE", "PE"]:
                    opt_type = tsymbol[-2:]
                else:
                    opt_type = None

                ltp_resp = obj.ltpData("NFO", tsymbol, row["token"])
                if "data" in ltp_resp and ltp_resp["data"] is not None:
                    ltp = ltp_resp["data"].get("ltp", None)
                else:
                    ltp = None

                chain_data.append({
                    "tradingsymbol": tsymbol,
                    "strike": row.get("strike"),
                    "expiry": row.get("expiry"),
                    "option_type": opt_type,
                    "ltp": ltp,
                    "token": row.get("token")
                })
            except Exception as e:
                print(f"⚠️ LTP fetch failed for {row.get('symbol', 'UNKNOWN')}: {e}")

        return pd.DataFrame(chain_data)

    except Exception as e:
        print(f"⚠️ Option chain fetch error: {e}")
        return pd.DataFrame()
