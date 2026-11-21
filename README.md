# Stock Market Research

[![Python Tests](https://github.com/kaluzap/stock_market_research/actions/workflows/python-tests.yml/badge.svg)](https://github.com/kaluzap/stock_market_research/actions/workflows/python-tests.yml)

A personal tool to monitor a watchlist of stocks and ETFs. It downloads data from Yahoo Finance with `yfinance`, converts prices to EUR, gives each asset a simple classification and shows everything in a sortable HTML report, served by a small FastAPI app.

The goal is to spot red flags in a hand-picked list (losses, no data, analysts expecting a drop), not to find new stocks.

![Web Dashboard Screenshot](image/web_version.png)

## Features

- **Data pipeline:** downloads data for every ticker in the stock list, converts prices and analyst targets to EUR and classifies each asset.
- **Private data:** uses your own list in `my_data/` (ignored by git) if it exists, otherwise the sample list in `data/`.
- **Dashboard:** sortable table with buttons to download fresh data, rebuild the report or show only D+ assets. A desktop notification (Linux, `notify-send`) tells you when an update finishes.
- **Tests and CI:** `pytest` unit tests with Yahoo and subprocess calls mocked, run by GitHub Actions on pushes to `main` and on pull requests, together with a Black formatting check.

## Requirements

- Python 3.12 or newer
- Optional: `notify-send` (Linux) for desktop notifications

## Installation

```bash
python3 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

## How to use

### First run

The report is built from downloaded data, so download it once first (about 30 seconds for 150 tickers; 16 tickers are downloaded at a time):

```bash
python data_pipeline/create_report.py -a
```

The `temp/` (data cache) and `reports/` (HTML report) folders are created automatically.

### Web dashboard

```bash
python web_gui/server.py
```

Open `http://localhost:5000`. The header buttons:

- **Actualize Data:** download fresh data and rebuild the report.
- **Refresh Report:** rebuild the report from the stored data, without downloading.
- **Filter D+:** show only D+ assets (see [Classification](#classification)), sorted by analyst recommendation.

The server only listens on `127.0.0.1`, so it cannot be reached from other machines. API docs are at `http://localhost:5000/docs`.

### Command line

```bash
python data_pipeline/create_report.py                        # rebuild from stored data
python data_pipeline/create_report.py -a                     # download fresh data first
python data_pipeline/create_report.py -s change              # sort by a column
python data_pipeline/create_report.py -cv classification:D+  # keep rows where column == value
python data_pipeline/create_report.py -d path/to/data_dir    # use another stock list folder
```

The report is written to `reports/simple_stock_report.html`. `make_update.sh` and `make_top_picks.sh` are shortcuts for the `-a` and D+ commands.

### Find the Yahoo ticker of an ISIN

```bash
python utils/find_yahoo_id.py DE000A1EWWW0 US0231351067
```

It checks the ISIN and lists the Yahoo listings found for it. It picks the one with the most data (fundamentals and analyst targets), which is usually the home exchange rather than a German secondary listing.

## Stock list format

`my_data/list_of_stocks.csv` (or `data/list_of_stocks.csv`) has one row per asset:

| Column | Required | Example | Meaning |
|---|---|---|---|
| `name` | yes | `adidas` | Your name for the asset, shown as `my_name` |
| `isin` | yes | `DE000A1EWWW0` | Checked for typos (a warning is logged if invalid) |
| `ysymbol` | yes | `ADS.DE` | Yahoo Finance ticker; rows without it are skipped |
| `gsymbol` | no | `ADS:ETR` | Google Finance symbol, for the link column |
| `wkn`, `notes` | no | | Not used by the report |

Several rows can share a ticker (e.g. an old and a new ISIN of the same asset).

## Classification

Each asset gets a letter and a sign, for example `D+`.

| Letter | Meaning |
|---|---|
| A | No earnings data (e.g. ETFs) |
| B | Losing money (negative profit margin) |
| C | Profitable, no dividend |
| D | Profitable and pays a dividend |
| X | Invalid data: negative dividend yield (should never appear) |

| Sign | Meaning |
|---|---|
| `+` | Analysts' average target price is above the current price |
| `-` | Analysts' average target price is below the current price |
| `?` | No analyst target |

The sign comes from the `change` column (target vs. price). It can rest on very few analysts, so check `recommendationKey` and the linked pages before acting on it.

## Development

```bash
pytest tests/        # run the tests
black .              # format the code
pre-commit install   # once per clone: run Black automatically before every commit
```

CI fails if a test fails or a file is not formatted with Black.

## Project structure

- `configuration.py`: paths, server port, report columns and currency pairs.
- `data_pipeline/create_report.py`: the pipeline (load data, merge with the stock list, classify, convert to EUR, write HTML).
- `utils/`: Yahoo download and cache (`stock_data.py`), classification, dates, currency conversion and ISIN check (`util.py`), ticker search (`find_yahoo_id.py`), desktop notifications (`notify.py`).
- `web_gui/server.py`: FastAPI dashboard server.
- `templates/report_template.html`: HTML, CSS and JavaScript of the report page.
- `data/`: sample stock list. `my_data/`: your private list (ignored by git).
- `temp/`, `reports/`: downloaded data and generated report (created on first run, ignored by git).
- `notebooks/`: notebook used to maintain the stock list.
- `tests/`: test suite.
- `CLAUDE.md`: notes for the Claude Code AI assistant.

## Disclaimer

Personal project, not financial advice. Data comes from Yahoo Finance and can be incomplete or wrong.
