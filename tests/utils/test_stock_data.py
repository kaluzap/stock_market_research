import pytest
import pandas as pd
import json
from pathlib import Path
from utils.stock_data import download_stock_data, save_stock_data, load_stock_data, actualize_stock_data

def test_download_stock_data(mocker):
    # Mock yfinance.Tickers
    mock_tickers_obj = mocker.Mock()
    mock_ticker_a = mocker.Mock()
    mock_ticker_a.info = {"symbol": "AAPL", "price": 150}
    mock_ticker_b = mocker.Mock()
    mock_ticker_b.info = {"symbol": "MSFT", "price": 300}
    
    mock_tickers_obj.tickers = {
        "AAPL": mock_ticker_a,
        "MSFT": mock_ticker_b
    }
    
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
        "MSFT": {"symbol": "MSFT", "price": 300}
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
