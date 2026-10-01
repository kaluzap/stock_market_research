import pandas as pd
from datetime import datetime
import math
import re
import logging

logger = logging.getLogger(__name__)


def create_ex_dividend_date(row: pd.Series) -> str:
    """
    Extracts the latest ex-dividend date and calculates the number of days 
    between the two most recent dividend events.

    To handle stale Yahoo Finance API summary data and timezone offsets (which 
    can shift timestamps for the same event by a few hours), this function:
    1. Collects all unique dates from both the summary info (exDividendDate, 
       lastDividendDate) and historical records (ex_date_1, ex_date_2).
    2. Groups/deduplicates dates that are within 10 days of each other.
    3. Identifies the latest (day_last) and previous (day_previous) distinct events.

    Args:
        row (pd.Series): A row representing stock data, containing keys:
            - 'exDividendDate': Summary profile ex-dividend timestamp (float).
            - 'lastDividendDate': Summary profile last dividend timestamp (float).
            - 'ex_date_1': Most recent dividend timestamp from history (float).
            - 'ex_date_2': Second most recent dividend timestamp from history (float).

    Returns:
        str: Formatted ex-dividend date with delta days (e.g., '2026-03-30 (90)' 
             or 'old 2026-03-30 (90)' if in the past), or '---' if no dates exist.
    """

    ex_dividend_date = row.get("exDividendDate", None)
    last_dividend_date = row.get("lastDividendDate", None)
    ex_date_1 = row.get("ex_date_1", None)
    ex_date_2 = row.get("ex_date_2", None)

    try:
        # Collect all valid ex-dividend dates
        dates = []
        for adate in [ex_dividend_date, last_dividend_date, ex_date_1, ex_date_2]:
            if adate is not None and not math.isnan(adate):
                dates.append(datetime.fromtimestamp(float(adate)).date())

        # Deduplicate and sort descending (latest date first)
        _unique_dates = sorted(list(set(dates)), reverse=True)

        # Remove the dates that are closer than one day
        unique_dates = []
        if len(_unique_dates) > 1:
            unique_dates.append(_unique_dates[0])
            for i in range(1, len(_unique_dates)):
                delta = (unique_dates[-1] - _unique_dates[i]).days
                if delta > 10:
                    unique_dates.append(_unique_dates[i])
        elif len(_unique_dates) == 1:
            unique_dates = [_unique_dates[0]]
        else:
            pass

        # Computing the last and previous days
        if len(unique_dates) >= 2:
            day_last = unique_dates[0]
            day_previous = unique_dates[1]
        elif len(unique_dates) == 1:
            day_last = unique_dates[0]
            day_previous = day_last
        else:
            return "---"
    except Exception as e:
        logger.error(f"Error parsing dates: {e}")
        return "-ERROR-"

    delta_days = f"({(day_last - day_previous).days})"

    if datetime.now().date() > day_last:
        return f'old {day_last.strftime("%Y-%m-%d")} {delta_days}'
    return f'{day_last.strftime("%Y-%m-%d")} {delta_days}'


def my_classification(row: pd.Series) -> str:
    """
    Classifies a stock based on its profit margins, dividend yield, and price change.

    The classification consists of a letter code followed by an optional sign suffix.

    Letter Codes:
        - 'A': No earnings data available (profitMargins is NaN or exactly 0.0,
               which Yahoo returns as a placeholder for missing data).
        - 'B': Negative earnings (profitMargins < 0).
        - 'C': Has earnings, but no dividend data (profitMargins > 0 and dividendYield is NaN).
        - 'D': Has earnings and pays dividends (profitMargins > 0 and dividendYield > 0).
        - 'X': Unexpected/invalid state (profitMargins > 0 and dividendYield <= 0).

    Sign Suffixes:
        - '?': No price change data available (change is NaN).
        - '-': Price is expected to go down (change < 0).
        - '+': Price is expected to go up (change > 0).
        - (no suffix): Price is expected to remain unchanged (change == 0).

    Args:
        row (pd.Series): A series containing stock metrics with at least the following keys:
            - 'profitMargins' (float): The net profit margins of the stock.
            - 'dividendYield' (float): The dividend yield of the stock.
            - 'change' (float): The price change ratio/percentage.

    Returns:
        str: The classification code (e.g., 'A?', 'D+', 'C-', 'B').
    """
    classification = ""
    profitMargins = row["profitMargins"]
    if math.isnan(profitMargins) or profitMargins == 0:
        classification = "A"
    elif profitMargins < 0:
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


def make_currency_transformation(row: pd.Series, col: str, eur_currencies_prices: dict[str, float]) -> float:
    """
    Transforms a monetary value in a given column to Euros (EUR).

    If the stock's currency is EUR, the value is returned unchanged.
    If the currency exists in the exchange rate dictionary, the value is divided by the rate.
    Otherwise, the value is negated to flag the unsupported currency in the report.

    Args:
        row (pd.Series): A row representing stock data, containing keys:
            - 'currency' (str): The currency of the stock (e.g., 'EUR', 'USD').
            - col (str): The column containing the value to convert.
        col (str): The name of the column in `row` containing the monetary value.
        eur_currencies_prices (dict[str, float]): A dictionary mapping currency symbols
            (e.g., 'USD') to their respective exchange rate relative to EUR.

    Returns:
        float: The converted value in EUR, or the negated value if currency conversion is missing.
    """
    if row["currency"] == "EUR":
        return row[col]
    elif row["currency"] in eur_currencies_prices:
        return row[col] / eur_currencies_prices[row["currency"]]
    else:
        # Only to note the missing currency in the reoport
        return -row[col]


def make_google_link(row: pd.Series) -> str:
    """
    Generates an HTML anchor link to the stock's Google Finance page.

    Args:
        row (pd.Series): A row representing stock data, containing keys:
            - 'gsymbol' (str): The Google Finance quote symbol (e.g., 'NASDAQ:AAPL').

    Returns:
        str: An HTML link string if a valid gsymbol is found, or an empty string.
    """
    try:
        if row["gsymbol"] == "nan":
            return ""
        text = f'<a href="https://www.google.com/finance/quote/{row["gsymbol"]}" target="_blank">[link]</a>'
        return text
    except KeyError:
        return ""


def is_valid_isin(isin: str) -> bool:
    """
    Validates an ISIN using its format and check digit (Luhn algorithm).

    Catches typos such as the letter 'O' instead of the digit '0'.

    Args:
        isin (str): The ISIN to validate (e.g., 'DE000A1EWWW0').

    Returns:
        bool: True if the ISIN has a valid format and check digit, False otherwise.
    """
    if not isinstance(isin, str) or not re.fullmatch(r"[A-Z]{2}[A-Z0-9]{9}[0-9]", isin):
        return False

    # Letters become two digits (A=10 ... Z=35), digits stay the same
    digits = "".join(str(int(c, 36)) for c in isin[:-1])

    total = 0
    for i, d in enumerate(reversed(digits)):
        n = int(d) * (2 if i % 2 == 0 else 1)
        total += n // 10 + n % 10
    return (10 - total % 10) % 10 == int(isin[-1])
