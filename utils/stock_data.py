import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd
import yfinance as yf
from curl_cffi import requests

# Tickers downloaded at the same time. Each ticker needs two requests (info and
# dividend history); most of the time is spent waiting for Yahoo, so parallel
# requests make the update about this many times faster.
DOWNLOAD_WORKERS = 16


def download_one(tickers: yf.Tickers, stock: str) -> dict | None:
    """The Yahoo info of one ticker, with its last two dividends.

    The dividends are added as 'ex_date_1', 'ex_value_1', 'ex_date_2' and
    'ex_value_2' (they are not in the info). Returns None if the info fails
    (delisted ticker, Yahoo error, ...), so only this ticker is skipped.
    """
    try:
        stock_data = dict(tickers.tickers[stock].info)
    except Exception as e:
        print(f"Error with stock_data for '{stock}': '{e}'")
        return None

    # The dividend history is in a different place; without it the info is kept
    try:
        history = tickers.tickers[stock].dividends
        for i in (1, 2):
            if len(history) >= i:
                stock_data[f"ex_date_{i}"] = int(history.index[-i].timestamp())
                stock_data[f"ex_value_{i}"] = float(history.iloc[-i])
    except Exception as e:
        print(f"Error dividend_history for '{stock}': '{e}'")
    return stock_data


def download_stock_data(stocks: list[str]) -> dict:
    """Downloads the tickers in parallel; the ones that fail are left out."""
    session = requests.Session(impersonate="chrome")
    tickers = yf.Tickers(" ".join(stocks), session=session)
    with ThreadPoolExecutor(max_workers=DOWNLOAD_WORKERS) as executor:
        results = executor.map(lambda stock: download_one(tickers, stock), stocks)
        return {stock: data for stock, data in zip(stocks, results) if data is not None}


def save_stock_data(data: dict, data_file_path: Path):
    with open(data_file_path, "w") as outfile:
        json.dump(data, outfile, indent=4, sort_keys=True)


def actualize_stock_data(stocks: list[str], data_file_path: Path):
    data = download_stock_data(stocks)
    if not data:
        # e.g. Yahoo rate limit: keep the previous data file instead of emptying it
        raise RuntimeError("No stock data could be downloaded. Previous data kept.")
    save_stock_data(data, data_file_path)


def load_stock_data(data_file_path: Path) -> pd.DataFrame:
    with open(data_file_path, "r") as input_file:
        data = json.load(input_file)
    df = pd.DataFrame([x for x in data.values()])
    return df
