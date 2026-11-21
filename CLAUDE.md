# CLAUDE.md

Personal stock-watchlist tool: downloads data from Yahoo Finance (`yfinance`), converts prices to EUR, classifies each stock and renders an HTML report served by a small FastAPI app.

## Commands

```bash
source venv/bin/activate
pip install -e ".[dev]"                        # install with test dependencies
pytest tests/                                  # run tests (also run by GitHub Actions)
python data_pipeline/create_report.py          # rebuild report from stored data
python data_pipeline/create_report.py -a       # download fresh data, then rebuild
python web_gui/server.py                       # dashboard at http://localhost:5000
python utils/find_yahoo_id.py <ISIN> ...       # find the best Yahoo ticker for an ISIN
black .                                        # format code (also run by the pre-commit hook and checked in CI)
```

## Layout

- `configuration.py`: paths, port, report columns, currency pairs.
- `data_pipeline/create_report.py`: the pipeline (load → merge with stock list → classify → EUR → HTML).
- `utils/`: `stock_data.py` (Yahoo download/cache), `util.py` (classification, dates, currency, ISIN check), `notify.py` (desktop pop-ups via `notify-send`).
- `web_gui/server.py`: FastAPI; each endpoint runs `create_report.py` as a subprocess.
- `templates/report_template.html`: report page with sorting and action buttons.
- `my_data/list_of_stocks.csv` (private, git-ignored) is used if present, otherwise `data/` (public sample).
- `temp/` holds the downloaded data cache and last update time; `reports/` holds the generated HTML. Both git-ignored and created on the first run; without data, run `create_report.py -a` first.

## Conventions

- Code is formatted with Black (line length 88); run `black .` before committing if the hook is not installed.
- Tests must not hit the network: mock `yfinance`, `subprocess.run` and `desktop_notification`.
- The server binds to `127.0.0.1` only; keep it that way (no CORS, no `0.0.0.0`).
- Monetary columns are shown in EUR; add new currencies to `CURRENCIES` in `configuration.py`.
- Keep it simple: this is a personal tool and portfolio piece, not a production service.
