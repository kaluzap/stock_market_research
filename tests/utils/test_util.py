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
    assert "(90)" in res or "(91)" in res  # ~90 days difference

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
    # Should choose 2026-03-30 and 2025-12-30
    assert "2026-03-30" in res or "2026-03-29" in res
    assert "(90)" in res or "(91)" in res

def test_create_ex_dividend_date_no_history():
    # No history case: only exDividendDate and lastDividendDate are available
    row = pd.Series({
        "exDividendDate": 1774825200.0,
        "lastDividendDate": 1767052800.0,
        "ex_date_1": float("nan"),
        "ex_date_2": float("nan"),
    })
    res = create_ex_dividend_date(row)
    assert "(90)" in res or "(91)" in res

def test_create_ex_dividend_date_missing():
    row = pd.Series({
        "exDividendDate": float("nan"),
        "lastDividendDate": float("nan"),
        "ex_date_1": float("nan"),
        "ex_date_2": float("nan"),
    })
    res = create_ex_dividend_date(row)
    assert res == "---"
