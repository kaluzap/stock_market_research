import yfinance as yf
import pandas as pd
from pathlib import Path
import json


def download_stock_data(stocks: list[str]) -> dict:
    tickers = yf.Tickers(" ".join(stocks))
    data = dict()
    for stock in stocks:
        try:
            stock_data = tickers.tickers[stock].info
            # dividend history is in a different place
            dividend_history = tickers.tickers[stock].dividends
            if not dividend_history.empty:
                try:
                    ex_date_timestamp_1 = dividend_history.index[-1]
                    ex_date_1 = ex_date_timestamp_1.strftime("%Y-%m-%d")
                    ex_value_1 = dividend_history.iloc[-1]
                    ex_date_timestamp_2 = dividend_history.index[-2]
                    ex_date_2 = ex_date_timestamp_2.strftime("%Y-%m-%d")
                    ex_value_2 = dividend_history.iloc[-2]
                    stock_data["ex_date_1"] = ex_date_1
                    stock_data["ex_value_1"] = ex_value_1
                    stock_data["ex_date_2"] = ex_date_2
                    stock_data["ex_value_2"] = ex_value_2
                except:
                    pass
        except KeyError as e:
            print(f"Error with stock: '{e}'.")
            continue
        data[stock] = stock_data
    return data


def save_stock_data(data: dict, data_file_path: Path):
    with open(data_file_path, "w") as outfile:
        json.dump(data, outfile, indent=4, sort_keys=True)


def actualize_stock_data(stocks: list[str], data_file_path: Path):
    data = download_stock_data(stocks)
    save_stock_data(data, data_file_path)


def load_stock_data(data_file_path: Path) -> pd.DataFrame:
    with open(data_file_path, "r") as input_file:
        data = json.load(input_file)
    df = pd.DataFrame([x for x in data.values()])
    return df



