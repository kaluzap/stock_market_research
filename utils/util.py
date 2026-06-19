import pandas as pd
from datetime import datetime
import math
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
