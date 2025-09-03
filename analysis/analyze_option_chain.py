import pandas as pd


def analyze_option_chain(df: pd.DataFrame):
    if df.empty:
        return None

    ce_data = df[df["option_type"] == "CE"]
    pe_data = df[df["option_type"] == "PE"]

    if ce_data.empty or pe_data.empty:
        return None

    ce_total = ce_data["ltp"].dropna().sum()
    pe_total = pe_data["ltp"].dropna().sum()

    pcr = round((pe_total / ce_total), 2) if ce_total > 0 else 0

    if pcr > 1.2:
        signal = f"📈 Bullish (PCR={pcr})"
    elif pcr < 0.8:
        signal = f"📉 Bearish (PCR={pcr})"
    else:
        signal = f"⚖️ Neutral (PCR={pcr})"

    try:
        top_ce = ce_data.sort_values("ltp", ascending=False).head(3)
        top_pe = pe_data.sort_values("ltp", ascending=False).head(3)

        ce_strikes = ", ".join(top_ce["strike"].astype(str).tolist())
        pe_strikes = ", ".join(top_pe["strike"].astype(str).tolist())

        details = f"Top CE Strikes: {ce_strikes}\nTop PE Strikes: {pe_strikes}"
    except Exception:
        details = ""

    return f"{signal}\n{details}"
