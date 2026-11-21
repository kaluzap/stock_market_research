import pytest
import pandas as pd
import json
import threading
from pathlib import Path
from utils.stock_data import (
    download_stock_data,
    save_stock_data,
    load_stock_data,
    actualize_stock_data,
)


def test_download_stock_data(mocker):
    # Mock yfinance.Tickers
    mock_tickers_obj = mocker.Mock()
    mock_ticker_a = mocker.Mock()
    mock_ticker_a.info = {"symbol": "AAPL", "price": 150}
    mock_ticker_b = mocker.Mock()
    mock_ticker_b.info = {"symbol": "MSFT", "price": 300}

    mock_tickers_obj.tickers = {"AAPL": mock_ticker_a, "MSFT": mock_ticker_b}

    mocker.patch("yfinance.Tickers", return_value=mock_tickers_obj)

    stocks = ["AAPL", "MSFT"]
    result = download_stock_data(stocks)

    assert len(result) == 2
    assert result["AAPL"]["symbol"] == "AAPL"
    assert result["MSFT"]["price"] == 300


def test_save_stock_data(tmp_path):
    data = {"AAPL": {"price": 150}}
    file_path = tmp_path / "test_data.json"

    save_stock_data(data, file_path)

    assert file_path.exists()
    with open(file_path, "r") as f:
        saved_data = json.load(f)
    assert saved_data == data


def test_load_stock_data(tmp_path):
    data = {
        "AAPL": {"symbol": "AAPL", "price": 150},
        "MSFT": {"symbol": "MSFT", "price": 300},
    }
    file_path = tmp_path / "test_data.json"
    with open(file_path, "w") as f:
        json.dump(data, f)

    df = load_stock_data(file_path)

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert "symbol" in df.columns
    assert df.iloc[0]["symbol"] in ["AAPL", "MSFT"]


def test_actualize_stock_data(mocker, tmp_path):
    # Mock download_stock_data to return predictable data
    mock_data = {"AAPL": {"symbol": "AAPL"}}
    mocker.patch("utils.stock_data.download_stock_data", return_value=mock_data)

    file_path = tmp_path / "actualized.json"
    actualize_stock_data(["AAPL"], file_path)

    assert file_path.exists()
    with open(file_path, "r") as f:
        saved_data = json.load(f)
    assert saved_data == mock_data


def test_download_stock_data_skips_failing_ticker(mocker):
    # A ticker that raises (delisted, Yahoo error, ...) must not stop the others
    mock_tickers_obj = mocker.Mock()
    mock_ok = mocker.Mock()
    mock_ok.info = {"symbol": "AAPL"}
    mock_bad = mocker.Mock()
    type(mock_bad).info = mocker.PropertyMock(side_effect=Exception("404 Not Found"))
    mock_tickers_obj.tickers = {"AAPL": mock_ok, "GONE": mock_bad}
    mocker.patch("yfinance.Tickers", return_value=mock_tickers_obj)

    result = download_stock_data(["AAPL", "GONE"])

    assert list(result) == ["AAPL"]


def test_actualize_stock_data_keeps_old_file_when_nothing_downloaded(mocker, tmp_path):
    file_path = tmp_path / "data.json"
    file_path.write_text('{"AAPL": {"price": 150}}')
    mocker.patch("utils.stock_data.download_stock_data", return_value={})

    with pytest.raises(RuntimeError):
        actualize_stock_data(["AAPL"], file_path)

    assert json.loads(file_path.read_text()) == {"AAPL": {"price": 150}}


def mock_tickers(mocker, tickers: dict):
    tickers_obj = mocker.Mock()
    tickers_obj.tickers = tickers
    mocker.patch("yfinance.Tickers", return_value=tickers_obj)


def test_download_stock_data_adds_last_two_dividends(mocker):
    ticker = mocker.Mock()
    ticker.info = {"symbol": "KO"}
    ticker.dividends = pd.Series(
        [0.48, 0.51, 0.51],
        index=pd.to_datetime(["2025-06-13", "2025-09-15", "2025-12-01"], utc=True),
    )
    mock_tickers(mocker, {"KO": ticker})

    data = download_stock_data(["KO"])["KO"]

    assert data["ex_date_1"] == int(pd.Timestamp("2025-12-01", tz="UTC").timestamp())
    assert data["ex_value_1"] == 0.51
    assert data["ex_date_2"] == int(pd.Timestamp("2025-09-15", tz="UTC").timestamp())


def test_download_stock_data_with_one_dividend(mocker):
    ticker = mocker.Mock()
    ticker.info = {"symbol": "NEW"}
    ticker.dividends = pd.Series([1.0], index=pd.to_datetime(["2025-12-01"], utc=True))
    mock_tickers(mocker, {"NEW": ticker})

    data = download_stock_data(["NEW"])["NEW"]

    assert data["ex_value_1"] == 1.0
    assert "ex_date_2" not in data


def test_download_stock_data_keeps_info_when_dividends_fail(mocker):
    ticker = mocker.Mock()
    ticker.info = {"symbol": "AAPL"}
    type(ticker).dividends = mocker.PropertyMock(side_effect=Exception("timeout"))
    mock_tickers(mocker, {"AAPL": ticker})

    assert download_stock_data(["AAPL"]) == {"AAPL": {"symbol": "AAPL"}}


def test_download_stock_data_runs_in_parallel(mocker):
    # Both tickers wait for each other: this only finishes if they are
    # downloaded at the same time (sequentially, the barrier times out)
    barrier = threading.Barrier(2, timeout=5)

    def info():
        barrier.wait()
        return {"ok": True}

    tickers = {}
    for symbol in ("A", "B"):
        ticker = mocker.Mock()
        type(ticker).info = mocker.PropertyMock(side_effect=info)
        ticker.dividends = pd.Series(dtype=float)
        tickers[symbol] = ticker
    mock_tickers(mocker, tickers)

    assert download_stock_data(["A", "B"]) == {"A": {"ok": True}, "B": {"ok": True}}
