import argparse
import logging
from pathlib import Path
import pandas as pd
from datetime import datetime
import math

import configuration as cfg
from utils import stock_data, util

data_file_path = cfg.TEMP_DIR / cfg.FILE_STOCK_DATA
PATH_FILE_STOCKS_PRICES = Path("/tmp/stocks_prices.csv")

# Configure logging
logging.getLogger("yfinance").setLevel(logging.CRITICAL)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s",
)
logger = logging.getLogger(__name__)


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
    list_of_stocks = list(set(df["ysymbol"])) + cfg.CURRENCIES
    logger.info(f"Downloading data for: {list_of_stocks}")

    save_request_time()
    stock_data.actualize_stock_data(
        list_of_stocks,
        data_file_path,
    )


def create_simple_report(df: pd.DataFrame, report_file_path: Path, eur_usd_price: dict):
    last_update = load_request_time()

    # Currency info string
    currency_info = " | ".join(
        [f"1 EUR = {amount} {currency}" for currency, amount in eur_usd_price.items()]
    )

    # Identify numeric columns for Tablesort
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()

    # Pre-process the dataframe for display while keeping it numeric for identification
    display_df = df.copy()

    # Colorize 'change' column if it's numeric
    if "change" in display_df.columns and pd.api.types.is_numeric_dtype(
        display_df["change"]
    ):

        def color_change(val):
            try:
                v = float(val)
                if math.isnan(v):
                    return "---"
                cls = "positive" if v > 0 else ("negative" if v < 0 else "neutral")
                return f'<span class="{cls}">{v}%</span>'
            except (ValueError, TypeError):
                return str(val)

        display_df["change"] = display_df["change"].apply(color_change)

    table_html = display_df.to_html(escape=False, index=False, border=0)

    # Post-processing the table HTML to add dynamic classes and sort methods
    lines = table_html.split("\n")
    processed_lines = []

    for line in lines:
        if "<td>old" in line:
            line = line.replace("<td>", '<td class="ex-dividend-old">')
        elif "<td>20" in line and "-" in line:  # Assuming date format YYYY-MM-DD
            line = line.replace("<td>", '<td class="ex-dividend-soon">')

        # Colorize classification (matching the specific pattern for the classification column)
        # The classification column values are like "D+", "A-", "C?", etc.
        # We target the pattern <td>[A-D][+|-|?]?</td>
        import re

        line = re.sub(
            r"<td>([A-D][\+\-\?]?)</td>", r'<td class="classification-\1">\1</td>', line
        )

        # Add data-sort-method="number" to headers of numeric columns
        if "<th>" in line:
            for col in numeric_cols:
                if f"<th>{col}</th>" in line:
                    line = line.replace(
                        f"<th>{col}</th>", f'<th data-sort-method="number">{col}</th>'
                    )

        processed_lines.append(line)

    table_html = "\n".join(processed_lines)
    # Add table-specific class for CSS
    table_html = table_html.replace("<table>", '<table id="stock-table">')

    # Prepare the HTML template with modern CSS and JS for sorting
    template_path = cfg.TEMPLATES_DIR / cfg.FILE_REPORT_TEMPLATE
    with open(template_path, "r") as f:
        html_template = f.read()

    html_template = html_template.replace("{{ last_update }}", str(last_update))
    html_template = html_template.replace("{{ currency_info }}", currency_info)
    html_template = html_template.replace("{{ table_html }}", table_html)

    with open(report_file_path, "w") as f:
        f.write(html_template)


def create_stocks_df(data_path_dir: Path) -> tuple[pd.DataFrame, float]:

    # Load data from yfinance
    df = stock_data.load_stock_data(data_file_path)

    # Add my names and isin as columns
    file_with_stocks_list = data_path_dir / cfg.FILE_STOCK_LIST
    df_symbol_name = pd.read_csv(file_with_stocks_list)
    symbol_name = dict(zip(df_symbol_name["ysymbol"], df_symbol_name["name"]))
    symbol_isin = dict(zip(df_symbol_name["ysymbol"], df_symbol_name["isin"]))
    symbol_gsymbol = dict(zip(df_symbol_name["ysymbol"], df_symbol_name["gsymbol"]))
    df["my_name"] = df["symbol"].map(lambda x: symbol_name.get(x, None))
    df["isin"] = df["symbol"].map(lambda x: symbol_isin.get(x, None))
    df["gsymbol"] = df["symbol"].map(lambda x: symbol_gsymbol.get(x, None))

    # Add possible percentage change
    df["change"] = df.apply(
        lambda row: round(
            100
            * (row["targetMeanPrice"] - row["regularMarketPrice"])
            / row["regularMarketPrice"],
            2,
        ),
        axis=1,
    )

    # Add my classification
    def my_classification(row: pd.Series) -> str:
        """
        Letters:
        A: no earnings data
        B: no earnings
        C: has earnings
        D: has earnings and dividends
        X: should not exist

        Signs:
        ?: no data
        -: price expected to go down
        +: price expected to go up
        """
        classification = ""
        grossMargins = row["grossMargins"]
        if math.isnan(grossMargins):
            classification = "A"
        elif grossMargins <= 0:
            classification = "B"
        else:
            dividendYield = row["dividendYield"]
            if math.isnan(dividendYield):
                classification = "C"
            elif dividendYield > 0:
                classification = "D"
            else:
                # this cannot be true
                classification = "X"
        change = row["change"]
        if math.isnan(change):
            return classification + "?"
        else:
            if change < 0:
                return classification + "-"
            elif change == 0:
                return classification
            else:
                return classification + "+"

    df["classification"] = df.apply(lambda r: my_classification(r), axis=1)

    # Transform currencies to EUR
    df = df[df["currency"].map(lambda x: isinstance(x, str))].copy()
    # df["currency"] = df["currency"].map(lambda x: x.upper())
    logger.info(f"Currency counts:\n{df['currency'].value_counts()}")
    eur_currencies_prices = dict()
    for currency_symbol in cfg.CURRENCIES:
        try:
            row = df[df["symbol"] == currency_symbol].iloc[0]
            # Try multiple keys to find a valid price
            price = None
            for key in [
                "regularMarketPrice",
                "currentPrice",
                "ask",
                "bid",
                "previousClose",
            ]:
                if key in row and pd.notnull(row[key]):
                    price = float(row[key])
                    break

            if price is not None:
                eur_currencies_prices[row["currency"]] = price
        except IndexError:
            continue

    # Adding GBp (Pence) to GBP transformation
    if "GBP" in eur_currencies_prices:
        eur_currencies_prices["GBp"] = eur_currencies_prices["GBP"] * 100.0

    logger.info(f"Detected Exchange Rates: {eur_currencies_prices}")

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

    df["exDividendDate"] = df.apply(
        lambda row: util.create_ex_dividend_date(row), axis=1
    )

    # yahoo link
    df["yahoo_link"] = df.apply(
        lambda x: f'<a href="https://finance.yahoo.com/quote/{x["symbol"]}" target="_blank">[link]</a>',
        axis=1,
    )

    # google link
    def _make_google_link(row: pd.Series) -> str:
        try:
            if row["gsymbol"] == "nan":
                return ""
            text = f'<a href="https://www.google.com/finance/quote/{row["gsymbol"]}" target="_blank">[link]</a>'
            return text
        except KeyError:
            return ""

    df["google_link"] = df.apply(lambda row: _make_google_link(row), axis=1)

    # Remove columns
    df = df[~df["symbol"].isin(cfg.CURRENCIES)][cfg.WANTED_COLUMNS].copy()

    return df, eur_currencies_prices


def filter_stocks_df(
    df: pd.DataFrame,
    sort_by: str,
    column_value: str,
) -> pd.DataFrame:

    # Sorting DF
    try:
        df = df.sort_values(by=[sort_by])
    except KeyError:
        logger.error(f"unknown column '{sort_by}'.")

    # Filtering if column and value
    try:
        col = column_value.split(":")[0]
        value = column_value.split(":")[1]
    except IndexError:
        col, value = "", ""
    if col and value:
        try:
            df = df[df[col].astype(str) == value].copy()
        except KeyError:
            logger.error(f"unknown column '{col}'.")
    df = df.reset_index(drop=True)

    return df


def main(data_path_dir: Path, sort_by: str, column_value: str, actualize: bool):

    if actualize:
        actualize_stock_data(data_path_dir)

    df, eur_currencies_prices = create_stocks_df(data_path_dir)

    # send a copy for other uses
    df[["my_name", "isin", "regularMarketPrice"]].to_csv(PATH_FILE_STOCKS_PRICES)

    df = filter_stocks_df(df, sort_by, column_value)

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

    main(args.data_path_dir, args.sort_by, args.column_value, args.actualize)
