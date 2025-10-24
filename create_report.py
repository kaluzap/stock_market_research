import argparse

import configuration as cfg
from utils import stock_data

from pathlib import Path
import pandas as pd


data_file_path = cfg.TEMP_DIR / cfg.FILE_STOCK_DATA


def actualize_stock_data(data_path_dir: Path):

    file_with_stocks_list = data_path_dir / cfg.FILE_STOCK_LIST
    df = pd.read_csv(file_with_stocks_list)

    list_of_stocks = list(set(df["symbol"]))
    print(f"Downloading data for: {list_of_stocks}")

    stock_data.actualize_stock_data(
            list_of_stocks,
            data_file_path,
        )


def main(data_path_dir: Path, actualize: bool):

    if actualize:
        actualize_stock_data(data_path_dir)

    df = stock_data.load_stock_data(data_file_path)

    print(df.head())



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
        default = cfg.DATA_DIR,
        help="Specify the data directory.",
    )

    parser.add_argument(
        "-a",
        "--actualize",
        action="store_true",
        default = False,
        help="Download and actualize data.",
    )

    args = parser.parse_args()

    main(args.data_path_dir, args.actualize)
