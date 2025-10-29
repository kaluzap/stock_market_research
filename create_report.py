import argparse

import configuration as cfg
from utils import stock_data

from pathlib import Path
import pandas as pd
from datetime import datetime


data_file_path = cfg.TEMP_DIR / cfg.FILE_STOCK_DATA


def save_request_time() -> datetime:
    request_time = datetime.now()
    log_time_file = cfg.TEMP_DIR / cfg.FILE_REQUEST_TIME
    with open(log_time_file, "w") as f:
        f.write(f"{request_time}")
    return request_time


def load_request_time() -> str:
    log_time_file = cfg.TEMP_DIR / cfg.FILE_REQUEST_TIME
    with open(log_time_file) as f:
        data = f.read()
    return data


def actualize_stock_data(data_path_dir: Path):

    file_with_stocks_list = data_path_dir / cfg.FILE_STOCK_LIST
    df = pd.read_csv(file_with_stocks_list)

    # Add always EUR to transform USD to EUR.
    list_of_stocks = list(set(df["symbol"])) + cfg.CURRENCIES
    print(f"Downloading data for: {list_of_stocks}")

    save_request_time()
    stock_data.actualize_stock_data(
        list_of_stocks,
        data_file_path,
    )


def create_simple_report(
    df: pd.DataFrame, report_file_path: Path, eur_usd_price: float
):

    report_file = open(report_file_path, "w")

    # Label
    text = '<p><font size="8" color="black">STOCKS SIMPLE REPORT</font></p>'
    report_file.write(text + "\n")

    text = ""
    for currency, amount in eur_usd_price.items():
        text += f"1 EUR = {amount} {currency}<br>"
    text = f'<p><font size="2" color="red">{text}</font></p>'
    report_file.write(text + "\n")

    text = (
        f'<p><font size="2" color="red">Last update: {load_request_time()}</font></p>'
    )
    report_file.write(text + "\n")

    table = df.to_html(escape=False, justify="center")
    report_file.write(table.replace("<td>", '<td align="center">'))

    report_file.close()


def create_stocks_df(
    data_path_dir: Path, sort_by: str, column_value: str
) -> tuple[pd.DataFrame, float]:

    # Load data
    df = stock_data.load_stock_data(data_file_path)

    # Add my names and isin as columns
    file_with_stocks_list = data_path_dir / cfg.FILE_STOCK_LIST
    df_symbol_name = pd.read_csv(file_with_stocks_list)
    symbol_name = dict(zip(df_symbol_name["symbol"], df_symbol_name["name"]))
    symbol_isin = dict(zip(df_symbol_name["symbol"], df_symbol_name["isin"]))
    df["my_name"] = df["symbol"].map(lambda x: symbol_name.get(x, "NO DATA"))
    df["isin"] = df["symbol"].map(lambda x: symbol_isin.get(x, "NO DATA"))

    # Add possible percentage change
    df["change"] = df.apply(lambda row: round(100*(row["targetMeanPrice"] - row["regularMarketPrice"])/row["regularMarketPrice"],2), axis=1)

    # Sorting DF
    try:
        df = df.sort_values(by=[sort_by])
    except KeyError:
        print(f"ERROR: unknown column '{sort_by}'.")


    # Transform currencies to EUR
    df["currency"] = df["currency"].map(lambda x: x.upper())
    print(df["currency"].value_counts())
    eur_currencies_prices = dict()
    for currency_symbol in cfg.CURRENCIES:
        try:
            row = df[df["symbol"] == currency_symbol].iloc[0]
        except IndexError:
            continue
        eur_currencies_prices[row["currency"]] = float(row["ask"])
    print(eur_currencies_prices)

    def _make_currency_transformation(row: pd.Series, col):
        if row["currency"] == "EUR":
            return row[col]
        elif row["currency"] in eur_currencies_prices:
            return row[col] / eur_currencies_prices[row["currency"]]
        else:
            # Only to note the missing currency in the reoport
            return -row[col]

    for col in cfg.COLUMNS_NEED_CURRENCY_CONVERTION:
        df[col] = df.apply(
            lambda r: round(_make_currency_transformation(r, col), 2), axis=1
        )

    # Remove columns
    df = df[~df["symbol"].isin(cfg.CURRENCIES)][cfg.WANTED_COLUMNS].copy()

    # Filtering if column and value
    df = df.astype(str)
    try:
        col = column_value.split("+")[0]
        value = column_value.split("+")[1]
    except IndexError:
        col, value = "", ""
    if col and value:
        try:
            df = df[df[col] == value].copy()
        except KeyError:
            print(f"ERROR: unknown column '{col}'.")
    df = df.reset_index(drop=True)






    return df, eur_currencies_prices


def main(data_path_dir: Path, sort_by: str, column_value: str, actualize: bool):

    if actualize:
        actualize_stock_data(data_path_dir)

    df, eur_currencies_prices = create_stocks_df(data_path_dir, sort_by, column_value)

    report_file_path = cfg.REPORT_DIR / "simple_stock_report.html"
    create_simple_report(df, report_file_path, eur_currencies_prices)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Stock market report.",
        epilog="Example: python create_report.py",
    )

    parser.add_argument(
        "--data_path_dir",
        "-d",
        required=False,
        type=Path,
        default=cfg.DATA_DIR,
        help="Specify the data directory.",
    )

    parser.add_argument(
        "--sort_by",
        "-s",
        required=False,
        type=str,
        default="my_name",
        help="Specify column for sorting (default = my_name).",
    )

    parser.add_argument(
        "--column_value",
        "-cv",
        required=False,
        type=str,
        default="",
        help="Specify a column and value for filtering. Use + as separator (recommendationKey+hold).",
    )

    parser.add_argument(
        "-a",
        "--actualize",
        action="store_true",
        default=False,
        help="Download and actualize data.",
    )

    args = parser.parse_args()

    main(
        args.data_path_dir,
        args.sort_by,
        args.column_value,
        args.actualize
    )
