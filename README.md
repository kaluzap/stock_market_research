# Stock Market Research

[![Python Tests](https://github.com/kaluzap/stock_market_research/actions/workflows/python-tests.yml/badge.svg)](https://github.com/kaluzap/stock_market_research/actions/workflows/python-tests.yml)

This tool provides an automated research report on stock market data using `yfinance`. It is designed as a professional data pipeline with a web-based dashboard.

## Features

- **Automated Data Pipeline:** Downloads and processes stock data, handles currency conversion (to EUR), and generates custom classifications.
- **Privacy First:** Supports a dual-data structure. Prioritizes `my_data/` for personal use while falling back to `data/` for public samples.
- **Interactive Dashboard:** Web interface with client-side sorting and one-click data actualization. Served by a **FastAPI** app (`web_gui/`) with interactive API docs.
- **Testing Suite:** Unit tests with `pytest` and `pytest-mock` (Yahoo and subprocess calls are mocked), run by GitHub Actions on every push and pull request.
- **Logging:** Professional logging system for monitoring the data pipeline execution.

![Web Dashboard Screenshot](image/web_version.png)

## Installation

1. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. Install the project in editable mode:
   ```bash
   pip install -e ".[dev]"
   ```

## How to use

### 1. Web Dashboard (Recommended)

```bash
python web_gui/server.py
```

The server listens only on `127.0.0.1:5000` (not reachable from other machines) and exposes interactive API docs at `http://localhost:5000/docs`.

- **View Report:** Open `http://localhost:5000` in your browser.
- **Actions:** Use the buttons in the header to **Actualize Data**, **Refresh** the report, or **Filter** for high-quality (D+) stocks.

### 2. Generate Report (CLI)

You can run the pipeline directly from the terminal:

```bash
# Basic report using default data
python data_pipeline/create_report.py

# Report with data actualization (downloads new data)
python data_pipeline/create_report.py -a
```

### 3. Running Tests

To verify the logic and data integrity:

```bash
pytest tests/
```

### 4. Code Formatting

The code is formatted with [Black](https://black.readthedocs.io/). A [pre-commit](https://pre-commit.com/) hook runs it automatically before every commit, and CI fails if any file is not formatted. Install the hook once per clone:

```bash
pre-commit install
```

To format everything by hand: `black .`

## Project Structure

- `data_pipeline/`: Core logic for data processing and report generation.
- `web_gui/`: FastAPI dashboard server.
- `configuration.py`: Centralized management of paths, currencies, and report columns.
- `utils/`: Reusable utilities for stock data retrieval.
- `data/`: Sample stock lists for demonstration.
- `my_data/`: (Ignored by git) Private directory for your personal stock lists.
- `reports/`: Location of generated HTML reports.
- `tests/`: Automated test suite.
