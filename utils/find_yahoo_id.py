import yfinance as yf

def get_yahoo_ticker_from_isin(isin):
    # Perform a search for the ISIN
    search = yf.Search(isin)

    print(search.quotes)

    if not search.quotes:
        return None

    # Priority 1: Gettex (Munich) - best for Scalable/N26
    for quote in search.quotes:
        if quote['symbol'].endswith('.MU'):
            return "Gettex", quote['symbol']

    # Priority 2: Xetra - best general German data
    for quote in search.quotes:
        if quote['symbol'].endswith('.DE'):
            return "Xetra", quote['symbol']

    # Priority 3: Any European exchange (e.g., .PA for Paris, .MI for Milan)
    # This ensures you stay in EUR
    return "Other", search.quotes[0]['symbol']

# Example usage:
isin_list = ['IE00BMC38736', 'IE00BGV5VN51', "IE00B3XXRP09"]
for isin in isin_list:
    ticker = get_yahoo_ticker_from_isin(isin)
    print(f"ISIN: {isin} -> Ticker: {ticker}")

    ticker_yahoo = yf.Ticker(isin)
    print(ticker_yahoo.ticker)
