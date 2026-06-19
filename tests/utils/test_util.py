import pytest
import pandas as pd
import math
from utils.util import create_ex_dividend_date

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
