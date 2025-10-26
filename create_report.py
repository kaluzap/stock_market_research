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
    list_of_stocks = list(set(df["symbol"])) + ["EURUSD=X"]
    print(f"Downloading data for: {list_of_stocks}")

    save_request_time()
    stock_data.actualize_stock_data(
        list_of_stocks,
        data_file_path,
    )


def create_simple_report(df: pd.DataFrame, report_file_path: Path, eur_usd_price: float):

    report_file = open(report_file_path, "w")

    # Label
    text = '<p><font size="8" color="black">STOCKS SIMPLE REPORT</font></p>'
    report_file.write(text + "\n")

    text = f'<p><font size="2" color="red">1 EUR = {eur_usd_price} USD</font></p>'
    report_file.write(text + "\n")

    text = (
        f'<p><font size="2" color="red">Last update: {load_request_time()}</font></p>'
    )
    report_file.write(text + "\n")

    table = df.to_html(escape=False, justify="center")
    report_file.write(table.replace("<td>", '<td align="center">'))

    report_file.close()


def create_stocks_df(data_path_dir: Path, sort_by: str) -> tuple[pd.DataFrame, float]:

    # Load data
    df = stock_data.load_stock_data(data_file_path)

    # Add my names and isin as columns
    file_with_stocks_list = data_path_dir / cfg.FILE_STOCK_LIST
    df_symbol_name = pd.read_csv(file_with_stocks_list)
    symbol_name = dict(zip(df_symbol_name['symbol'], df_symbol_name['name']))
    symbol_isin = dict(zip(df_symbol_name['symbol'], df_symbol_name['isin']))
    df["my_name"] = df["symbol"].map(lambda x: symbol_name.get(x,""))
    df["isin"] = df["symbol"].map(lambda x: symbol_isin.get(x,""))

    # Sorting DF
    df = df.sort_values(by=[sort_by])
    df = df.reset_index(drop=True)

    # Transform USD to EUR
    eur_usd_price = round(df[df["symbol"] == "EURUSD=X"].iloc[0]["ask"], 5)
    print(f"EUR price : {eur_usd_price} USD")
    for col in cfg.COLUMNS_NEED_EUR_CONVERTION:
        df[col] = df[col].map(lambda x: round(x / eur_usd_price,2))

    # Remove columns
    df = df[~df["symbol"].isin(["EURUSD=X"])][cfg.WANTED_COLUMNS].copy()

    return df, eur_usd_price


def main(data_path_dir: Path, sort_by: str, actualize: bool):

    if actualize:
        actualize_stock_data(data_path_dir)

    df, eur_usd_price = create_stocks_df(data_path_dir, sort_by)

    report_file_path = cfg.REPORT_DIR / "simple_stock_report.html"
    create_simple_report(df, report_file_path, eur_usd_price)


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
        help="Specify column for sorting.",
    )

    parser.add_argument(
        "-a",
        "--actualize",
        action="store_true",
        default=False,
        help="Download and actualize data.",
    )

    args = parser.parse_args()

    main(args.data_path_dir, args.sort_by, args.actualize)
