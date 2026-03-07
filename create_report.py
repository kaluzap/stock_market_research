import argparse

import configuration as cfg
from utils import stock_data

from pathlib import Path
import pandas as pd
from datetime import datetime
import math


data_file_path = cfg.TEMP_DIR / cfg.FILE_STOCK_DATA
PATH_FILE_STOCKS_PRICES = Path("/tmp/stocks_prices.csv")


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
    df: pd.DataFrame, report_file_path: Path, eur_usd_price: dict
):
    last_update = load_request_time()
    
    # Currency info string
    currency_info = " | ".join([f"1 EUR = {amount} {currency}" for currency, amount in eur_usd_price.items()])

    # Identify numeric columns for Tablesort
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    
    # Pre-process the dataframe for display while keeping it numeric for identification
    display_df = df.copy()
    
    # Colorize 'change' column if it's numeric
    if 'change' in display_df.columns and pd.api.types.is_numeric_dtype(display_df['change']):
        def color_change(val):
            try:
                v = float(val)
                if math.isnan(v): return "---"
                cls = "positive" if v > 0 else ("negative" if v < 0 else "neutral")
                return f'<span class="{cls}">{v}%</span>'
            except (ValueError, TypeError):
                return str(val)
        display_df['change'] = display_df['change'].apply(color_change)

    table_html = display_df.to_html(escape=False, index=False, border=0)
    
    # Post-processing the table HTML to add dynamic classes and sort methods
    lines = table_html.split("\n")
    processed_lines = []
    
    for line in lines:
        if "<td>old" in line:
            line = line.replace("<td>", '<td class="ex-dividend-old">')
        elif "<td>20" in line and "-" in line: # Assuming date format YYYY-MM-DD
            line = line.replace("<td>", '<td class="ex-dividend-soon">')
        
        # Colorize classification (matching the specific pattern for the classification column)
        # The classification column values are like "D+", "A-", "C?", etc.
        # We target the pattern <td>[A-D][+|-|?]?</td>
        import re
        line = re.sub(r'<td>([A-D][\+\-\?]?)</td>', r'<td class="classification-\1">\1</td>', line)

        # Add data-sort-method="number" to headers of numeric columns
        if "<th>" in line:
            for col in numeric_cols:
                if f"<th>{col}</th>" in line:
                    line = line.replace(f"<th>{col}</th>", f'<th data-sort-method="number">{col}</th>')

        processed_lines.append(line)
    
    table_html = "\n".join(processed_lines)
    # Add table-specific class for CSS
    table_html = table_html.replace("<table>", '<table id="stock-table">')

    # Prepare the HTML template with modern CSS and JS for sorting
    html_template = f"""
<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@1/css/pico.min.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/tablesort/5.2.1/tablesort.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/tablesort/5.2.1/sorts/tablesort.number.min.js"></script>
    <title>Stock Market Research Report</title>
    <style>
        :root {{
            --primary: #2c3e50;
        }}
        body {{
            padding: 20px;
            font-size: 0.85rem;
        }}
        .header-section {{
            margin-bottom: 2rem;
            border-bottom: 2px solid var(--primary);
            padding-bottom: 1rem;
        }}
        h1 {{
            margin-bottom: 0.2rem;
            color: var(--primary);
        }}
        .header-info {{
            color: #666;
            font-size: 0.8rem;
            display: flex;
            justify-content: space-between;
            align-items: baseline;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th {{
            background-color: var(--primary);
            color: white !important;
            cursor: pointer;
            position: sticky;
            top: 0;
            z-index: 100;
        }}
        th[aria-sort="descending"]::after {{ content: " ▼"; }}
        th[aria-sort="ascending"]::after {{ content: " ▲"; }}
        td, th {{
            text-align: center !important;
            padding: 6px 12px !important;
            border: 1px solid #ddd !important;
        }}
        .positive {{ color: #27ae60 !important; font-weight: bold; }}
        .negative {{ color: #e74c3c !important; font-weight: bold; }}
        .neutral {{ color: #7f8c8d !important; }}
        .ex-dividend-soon {{ background-color: #d4edda !important; font-weight: bold; }}
        .ex-dividend-old {{ background-color: #fff3cd !important; color: #856404; opacity: 0.8; }}
        .recommendation-buy {{ font-weight: bold; color: #2980b9; }}
        [class*="classification-D"] {{ border-left: 5px solid #27ae60 !important; }}
        [class*="classification-C"] {{ border-left: 5px solid #3498db !important; }}
        [class*="classification-B"] {{ border-left: 5px solid #e67e22 !important; }}
        [class*="classification-A"] {{ border-left: 5px solid #7f8c8d !important; }}
        tr:hover {{ background-color: #cbd5e1 !important; outline: 1px solid var(--primary) !important; }}
        a {{ text-decoration: none; font-weight: bold; }}
    </style>
</head>
<body>
    <main class="container-fluid">
        <div class="header-section">
            <hgroup>
                <h1>Stock Market Research Report</h1>
                <div class="header-info" style="display: block;">
                    <span><strong>Last update:</strong> {last_update}</span><br>
                    <span><strong>Exchange Rates:</strong> {currency_info}</span>
                </div>
                <div style="margin-top: 1rem; display: flex; gap: 10px; align-items: center;">
                    <button onclick="actualizeData()" id="actualize-btn" style="padding: 0.5rem 1rem; font-size: 0.8rem; width: auto; margin-bottom: 0;">Actualize Data</button>
                    <button onclick="refreshReport()" id="refresh-btn" style="padding: 0.5rem 1rem; font-size: 0.8rem; width: auto; margin-bottom: 0; background-color: #34495e; border-color: #34495e;">Refresh Report</button>
                    <button onclick="filterDPlus()" id="filter-btn" style="padding: 0.5rem 1rem; font-size: 0.8rem; width: auto; margin-bottom: 0; background-color: #34495e; border-color: #34495e;">Filter D+</button>
                    <span id="actualize-status" style="font-weight: bold; font-size: 0.8rem;"></span>
                </div>
                
                <details style="margin-top: 1rem; font-size: 0.75rem;">
                    <summary style="cursor: pointer; color: var(--primary); font-weight: bold;">Classification Help</summary>
                    <div style="display: flex; gap: 40px; padding: 10px; background: #f9f9f9; border-radius: 5px; margin-top: 5px;">
                        <div>
                            <strong>Letters:</strong><br>
                            A: no earnings data<br>
                            B: no earnings<br>
                            C: has earnings<br>
                            D: has earnings and dividends<br>
                            X: should not exist
                        </div>
                        <div>
                            <strong>Signs:</strong><br>
                            ?: no data<br>
                            -: price expected to go down<br>
                            +: price expected to go up
                        </div>
                    </div>
                </details>
            </hgroup>
        </div>

        <div style="overflow-x: auto;">
            {table_html}
        </div>
    </main>
    <script>
        new Tablesort(document.querySelector('table'));

        async function actualizeData() {{
            const btn = document.getElementById('actualize-btn');
            const status = document.getElementById('actualize-status');
            
            btn.setAttribute('aria-busy', 'true');
            btn.disabled = true;
            status.innerText = 'Actualizing...';
            status.style.color = 'inherit';

            try {{
                const response = await fetch('http://localhost:5000/actualize', {{ method: 'POST' }});
                if (response.ok) {{
                    status.innerText = 'Success! Reloading...';
                    status.style.color = '#27ae60';
                    setTimeout(() => window.location.reload(), 1500);
                }} else {{
                    const data = await response.json();
                    status.innerText = 'Error: ' + (data.error || 'unknown');
                    status.style.color = '#e74c3c';
                    btn.setAttribute('aria-busy', 'false');
                    btn.disabled = false;
                }}
            }} catch (err) {{
                status.innerText = 'Failed to connect to server.';
                status.style.color = '#e74c3c';
                btn.setAttribute('aria-busy', 'false');
                btn.disabled = false;
            }}
        }}

        async function refreshReport() {{
            const btn = document.getElementById('refresh-btn');
            const status = document.getElementById('actualize-status');
            
            btn.setAttribute('aria-busy', 'true');
            btn.disabled = true;
            status.innerText = 'Refreshing...';
            status.style.color = 'inherit';

            try {{
                const response = await fetch('http://localhost:5000/refresh', {{ method: 'POST' }});
                if (response.ok) {{
                    status.innerText = 'Success! Reloading...';
                    status.style.color = '#27ae60';
                    setTimeout(() => window.location.reload(), 1000);
                }} else {{
                    const data = await response.json();
                    status.innerText = 'Error: ' + (data.error || 'unknown');
                    status.style.color = '#e74c3c';
                    btn.setAttribute('aria-busy', 'false');
                    btn.disabled = false;
                }}
            }} catch (err) {{
                status.innerText = 'Failed to connect to server.';
                status.style.color = '#e74c3c';
                btn.setAttribute('aria-busy', 'false');
                btn.disabled = false;
            }}
        }}

        async function filterDPlus() {{
            const btn = document.getElementById('filter-btn');
            const status = document.getElementById('actualize-status');
            
            btn.setAttribute('aria-busy', 'true');
            btn.disabled = true;
            status.innerText = 'Filtering...';
            status.style.color = 'inherit';

            try {{
                const response = await fetch('http://localhost:5000/filter', {{ method: 'POST' }});
                if (response.ok) {{
                    status.innerText = 'Success! Reloading...';
                    status.style.color = '#27ae60';
                    setTimeout(() => window.location.reload(), 1000);
                }} else {{
                    const data = await response.json();
                    status.innerText = 'Error: ' + (data.error || 'unknown');
                    status.style.color = '#e74c3c';
                    btn.setAttribute('aria-busy', 'false');
                    btn.disabled = false;
                }}
            }} catch (err) {{
                status.innerText = 'Failed to connect to server.';
                status.style.color = '#e74c3c';
                btn.setAttribute('aria-busy', 'false');
                btn.disabled = false;
            }}
        }}
    </script>
</body>
</html>
"""
    
    with open(report_file_path, "w") as f:
        f.write(html_template)


def create_stocks_df(data_path_dir: Path) -> tuple[pd.DataFrame, float]:

    # Load data
    df = stock_data.load_stock_data(data_file_path)

    # Add my names and isin as columns
    file_with_stocks_list = data_path_dir / cfg.FILE_STOCK_LIST
    df_symbol_name = pd.read_csv(file_with_stocks_list)
    symbol_name = dict(zip(df_symbol_name["symbol"], df_symbol_name["name"]))
    symbol_isin = dict(zip(df_symbol_name["symbol"], df_symbol_name["isin"]))
    symbol_gsymbol = dict(zip(df_symbol_name["symbol"], df_symbol_name["gsymbol"]))
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

    if "exDividendDate" in df.columns:

        def _create_date(row: str) -> str:
            if math.isnan(row["exDividendDate"]):
                return "---"
            stock_date = datetime.fromtimestamp(float(row["exDividendDate"]))

            delta_days = "(?)"
            if not math.isnan(row["lastDividendDate"]):
                last_date = datetime.fromtimestamp(float(row["lastDividendDate"]))
                delta_days = f"({(stock_date - last_date).days})"

            if datetime.now() > stock_date:
                return f'old {stock_date.strftime("%Y-%m-%d")} {delta_days}'
            return f'{stock_date.strftime("%Y-%m-%d")} {delta_days}'

        df["exDividendDate"] = df.apply(lambda row: _create_date(row), axis=1)

    # Remove columns
    df = df[~df["symbol"].isin(cfg.CURRENCIES)][cfg.WANTED_COLUMNS].copy()

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
        print(f"ERROR: unknown column '{sort_by}'.")

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
            print(f"ERROR: unknown column '{col}'.")
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
