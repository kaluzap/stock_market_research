import yfinance as yf
import pandas as pd
from typing import Optional

pd.set_option("display.max_columns", None)
pd.set_option("display.max_rows", None)
# data = yf.download("AAPL", start="2020-01-01", end="2021-01-01")
# print(data.head())
#
#
# apple = yf.Ticker("AAPL")
# print(apple.info)  # General information about Apple Inc.


def get_stock_info(stock_code: str) -> dict:
    return yf.Ticker(stock_code)


def download_stock_data(
    stocks: list[str], columns: Optional[list[str]] = None
) -> pd.DataFrame:

    tickers = yf.Tickers(" ".join(stocks))
    data = []
    for stock in stocks:
        try:
            stock_data = tickers.tickers[stock].info
        except KeyError as e:
            print(f"Error with stock: '{e}'.")
            continue
        data.append(stock_data)
        try:
            print(stock_data.dividends)
        except:
            pass

    df_stocks = pd.DataFrame(data)

    if columns is not None:
        df_stocks = df_stocks[columns].copy()

    return df_stocks


if __name__ == "__main__":
    # data = yf.download("AAPL", start="2020-01-01", end="2021-01-01")
    # print(data.head())

    # apple = get_stock_info("AAPL")
    # print(apple.info)  # General information about Apple Inc.

    df = download_stock_data(
        stocks=["NVDA", "HFG.DE"],
        columns = ["symbol", "displayName", "shortName", "regularMarketPrice", "epsCurrentYear"],
    )  # ""MSFT", "AAPL", "GOOG", "uuuuu", "INTC", "NVDA", "HFG.DE"])

    print(df.columns)
    print(df.head())
