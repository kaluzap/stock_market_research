import pytest
import pandas as pd
from utils.util import (
    create_ex_dividend_date,
    my_classification,
    make_currency_transformation,
    make_google_link,
    is_valid_isin,
)

def test_create_ex_dividend_date_standard():
    # Regular case: history and info are aligned
    # ex_date_1 = 2026-03-30 (1774825200.0)
    # ex_date_2 = 2025-12-30 (1767052800.0)
    row = pd.Series({
        "exDividendDate": 1774825200.0,
        "lastDividendDate": 1774828800.0,
        "ex_date_1": 1774825200.0,
        "ex_date_2": 1767052800.0,
    })
    res = create_ex_dividend_date(row)
    # Support timezone shifts (e.g. UTC vs local timezone) which can shift day differences between 89 and 91 days
    assert any(x in res for x in ["(89)", "(90)", "(91)"])

def test_create_ex_dividend_date_stale_info():
    # Stale info case: exDividendDate is stuck in 2023, but history is updated
    # ex_date_1 = 2026-03-30 (1774825200.0)
    # ex_date_2 = 2025-12-30 (1767052800.0)
    # exDividendDate = 2023-06-29 (1687996800.0)
    row = pd.Series({
        "exDividendDate": 1687996800.0,
        "lastDividendDate": 1774828800.0,
        "ex_date_1": 1774825200.0,
        "ex_date_2": 1767052800.0,
    })
    res = create_ex_dividend_date(row)
    # Should choose the latest dates (approx. 2026-03-30 and 2025-12-30)
    assert "2026-03-30" in res or "2026-03-29" in res
    assert any(x in res for x in ["(89)", "(90)", "(91)"])

def test_create_ex_dividend_date_no_history():
    # No history case: only exDividendDate and lastDividendDate are available
    row = pd.Series({
        "exDividendDate": 1774825200.0,
        "lastDividendDate": 1767052800.0,
        "ex_date_1": float("nan"),
        "ex_date_2": float("nan"),
    })
    res = create_ex_dividend_date(row)
    assert any(x in res for x in ["(89)", "(90)", "(91)"])

def test_create_ex_dividend_date_missing():
    row = pd.Series({
        "exDividendDate": float("nan"),
        "lastDividendDate": float("nan"),
        "ex_date_1": float("nan"),
        "ex_date_2": float("nan"),
    })
    res = create_ex_dividend_date(row)
    assert res == "---"


@pytest.mark.parametrize(
    "profit_margins, dividend_yield, change, expected",
    [
        # Letter A: No earnings data (profitMargins is NaN)
        (float("nan"), 0.05, 0.02, "A+"),
        (float("nan"), 0.05, -0.01, "A-"),
        (float("nan"), 0.05, 0.0, "A"),
        (float("nan"), 0.05, float("nan"), "A?"),
        # 0.0 is a Yahoo placeholder for missing data
        (0.0, 0.05, 0.02, "A+"),
        (0.0, float("nan"), float("nan"), "A?"),
        
        # Letter B: Negative earnings (profitMargins < 0)
        (-0.2, 0.05, 0.02, "B+"),
        (-0.1, 0.05, -0.01, "B-"),
        (-0.5, 0.05, 0.0, "B"),
        (-0.01, 0.05, float("nan"), "B?"),
        
        # Letter C: Has earnings, no dividends (profitMargins > 0, dividendYield is NaN)
        (0.2, float("nan"), 0.02, "C+"),
        (0.5, float("nan"), -0.01, "C-"),
        (0.01, float("nan"), 0.0, "C"),
        (0.3, float("nan"), float("nan"), "C?"),
        
        # Letter D: Has earnings and dividends (profitMargins > 0, dividendYield > 0)
        (0.2, 0.03, 0.02, "D+"),
        (0.5, 0.01, -0.01, "D-"),
        (0.01, 0.05, 0.0, "D"),
        (0.3, 0.02, float("nan"), "D?"),
        
        # Letter X: Unexpected state (profitMargins > 0, dividendYield <= 0)
        (0.2, 0.0, 0.02, "X+"),
        (0.5, -0.01, -0.01, "X-"),
        (0.01, -0.05, 0.0, "X"),
        (0.3, 0.0, float("nan"), "X?"),
    ],
)
def test_my_classification(profit_margins, dividend_yield, change, expected):
    row = pd.Series({
        "profitMargins": profit_margins,
        "dividendYield": dividend_yield,
        "change": change
    })
    assert my_classification(row) == expected


def test_make_currency_transformation():
    # Case 1: EUR currency, value should remain the same
    row_eur = pd.Series({"currency": "EUR", "price": 100.0})
    rates = {"USD": 1.1, "GBP": 0.85}
    assert make_currency_transformation(row_eur, "price", rates) == 100.0

    # Case 2: USD currency, converted to EUR using rates (price / rate)
    row_usd = pd.Series({"currency": "USD", "price": 110.0})
    assert make_currency_transformation(row_usd, "price", rates) == pytest.approx(100.0)

    # Case 3: GBP currency, converted to EUR
    row_gbp = pd.Series({"currency": "GBP", "price": 85.0})
    assert make_currency_transformation(row_gbp, "price", rates) == pytest.approx(100.0)

    # Case 4: Missing/unsupported currency, returns negated price
    row_jpy = pd.Series({"currency": "JPY", "price": 120.0})
    assert make_currency_transformation(row_jpy, "price", rates) == -120.0


def test_make_google_link():
    # Case 1: Valid gsymbol
    row_valid = pd.Series({"gsymbol": "NASDAQ:AAPL"})
    expected_link = '<a href="https://www.google.com/finance/quote/NASDAQ:AAPL" target="_blank">[link]</a>'
    assert make_google_link(row_valid) == expected_link

    # Case 2: gsymbol is "nan"
    row_nan = pd.Series({"gsymbol": "nan"})
    assert make_google_link(row_nan) == ""

    # Case 3: Missing gsymbol key (KeyError)
    row_missing = pd.Series({})
    assert make_google_link(row_missing) == ""


@pytest.mark.parametrize(
    "isin, expected",
    [
        ("DE000A1EWWW0", True),   # adidas
        ("US0231351067", True),   # amazon
        ("DE000A0D9PT0", True),   # MTU
        ("DE000A0D9PTO", False),  # MTU with letter 'O' instead of digit '0'
        ("US0231351068", False),  # wrong check digit
        ("US023135106", False),   # too short
        ("de000a1ewww0", False),  # lowercase
        ("none", False),
        (float("nan"), False),
    ],
)
def test_is_valid_isin(isin, expected):
    assert is_valid_isin(isin) == expected
