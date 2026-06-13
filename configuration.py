from pathlib import Path

# Directories
BASE_DIR = (Path(__file__).parent).resolve()
_PRIVATE_DATA_DIR = BASE_DIR / "my_data"
_PUBLIC_DATA_DIR = BASE_DIR / "data"

# Prioritize private data if it exists and contains the stock list
if (_PRIVATE_DATA_DIR / "list_of_stocks.csv").exists():
    DATA_DIR = _PRIVATE_DATA_DIR
else:
    DATA_DIR = _PUBLIC_DATA_DIR

REPORT_DIR = BASE_DIR / "reports"
TEMP_DIR = BASE_DIR / "temp"
TEMPLATES_DIR = BASE_DIR / "templates"

# Files
FILE_STOCK_DATA = "stock_data.json"
FILE_STOCK_LIST = "list_of_stocks.csv"
FILE_REQUEST_TIME = "request_time.txt"
FILE_REPORT_TEMPLATE = "report_template.html"

WANTED_COLUMNS = [
    "my_name",
    "isin",
    "shortName",
    "regularMarketPrice",
    "targetMeanPrice",
    "change",
    "recommendationKey",
    "dividendYield",
    "exDividendDate",
    "classification",
    "yahoo_link",
    "google_link",
]

COLUMNS_NEED_CURRENCY_CONVERTION = [
    "regularMarketPrice",
    "targetMeanPrice",
    "epsTrailingTwelveMonths",
]

CURRENCIES = [
    "EURUSD=X",
    "EURHKD=X",
    "EURGBP=X",
    "EURCHF=X",
    "EURJPY=X",
    "EURBRL=X",
    "EURCHF=X",
]

if __name__ == "__main__":
    print("PATHS")
    print("=====")
    print(f"BASE_DIR = {BASE_DIR}")
    print(f"DATA_DIR = {DATA_DIR}")
    print(f"REPORT_DIR = {REPORT_DIR}")
    print(f"TEMP_DIR = {TEMP_DIR}")
