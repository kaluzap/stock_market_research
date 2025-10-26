from pathlib import Path

# Directories
BASE_DIR = (Path(__file__).parent).resolve()
DATA_DIR = BASE_DIR / "data"
REPORT_DIR = BASE_DIR / "reports"
TEMP_DIR = BASE_DIR / "temp"

# Files
FILE_STOCK_DATA = "stock_data.json"
FILE_STOCK_LIST = "list_of_stocks.csv"
FILE_REQUEST_TIME = "request_time.txt"

WANTED_COLUMNS = [
    "symbol",
    "my_name",
    "isin",
    "shortName",
    "currentPrice",
    "targetMeanPrice",
    "recommendationKey",
    "averageAnalystRating",
    "dividendYield",
    "epsTrailingTwelveMonths",
]

COLUMNS_NEED_EUR_CONVERTION = [
    "currentPrice",
    "targetMeanPrice",
    "epsTrailingTwelveMonths",
]

if __name__ == "__main__":
    print("PATHS")
    print("=====")
    print(f"BASE_DIR = {BASE_DIR}")
    print(f"DATA_DIR = {DATA_DIR}")
    print(f"REPORT_DIR = {REPORT_DIR}")
    print(f"TEMP_DIR = {TEMP_DIR}")
