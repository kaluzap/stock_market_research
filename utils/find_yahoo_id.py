"""
Finds the best Yahoo Finance ticker for an ISIN.

For this report the best ticker is the one with the most data (fundamentals and
analyst targets), not the one where the asset is bought. Prices are converted to
EUR anyway, so the home listing (e.g. VOD.L) is better than a German secondary
listing (e.g. VODI.DE), which often lacks this data.

Usage:
    python utils/find_yahoo_id.py DE000A1EWWW0 GB00BH4HKS39 ...
"""

import sys

import yfinance as yf

from utils.util import is_valid_isin

# Fields the report needs; a ticker scores one point for each one available
WANTED_FIELDS = [
    "profitMargins",
    "dividendYield",
    "payoutRatio",
    "targetMeanPrice",
    "numberOfAnalystOpinions",
]

# On ties (e.g. ETFs, which have no fundamentals) prefer the German venues
PREFERRED_SUFFIXES = [".DE", ".MU"]


def score_ticker(info: dict) -> int:
    # Yahoo returns 0 as a placeholder for missing data
    return sum(info.get(field) not in (None, 0) for field in WANTED_FIELDS)


def get_yahoo_ticker_from_isin(isin: str) -> str | None:
    if not is_valid_isin(isin):
        print(f"WARNING: '{isin}' is not a valid ISIN (check digit or format)")

    symbols = [quote["symbol"] for quote in yf.Search(isin).quotes]
    if not symbols:
        return None

    candidates = []
    for order, symbol in enumerate(symbols):
        try:
            info = yf.Ticker(symbol).info
        except Exception:
            continue
        preferred = any(symbol.endswith(s) for s in PREFERRED_SUFFIXES)
        candidates.append((score_ticker(info), preferred, -order, symbol, info))
        print(
            f"  {symbol:12} score={score_ticker(info)} "
            f"currency={info.get('currency')} analysts={info.get('numberOfAnalystOpinions')}"
        )

    if not candidates:
        return None

    _, _, _, best, info = max(candidates)

    # Depositary receipts (ADR/GDR) have a US ISIN for a foreign company, and Yahoo
    # only finds the receipt listings, not the home listing of the share
    if isin.startswith("US") and info.get("country") not in (None, "United States"):
        print(
            f"WARNING: '{isin}' looks like a depositary receipt of a company from "
            f"{info.get('country')}. Search the home listing manually."
        )

    return best


if __name__ == "__main__":
    for isin in sys.argv[1:]:
        print(f"ISIN: {isin}")
        print(f"  -> {get_yahoo_ticker_from_isin(isin)}")
