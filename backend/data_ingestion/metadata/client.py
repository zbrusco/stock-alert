import yfinance as yf
from ..credentials import get_api_credentials
import requests

# Load the API keys
_credentials = get_api_credentials()


def fetch_from_fmp(symbol: str) -> dict:
    """
    Fetch metadata for `symbol` from Financial Modeling Prep.
    """
    url = f"https://financialmodelingprep.com/api/v3/profile/{symbol}"
    params = {"apikey": _credentials["api_key_fmp"]}
    r = requests.get(url, params=params)
    data = r.json()
    if not isinstance(data, list) or not data:
        return None

    prof = data[0]

    types = {
        "isEtf": "ETF",
        "isAdr": "ADR",
        "isFund": "FUND",
    }
    asset_type = next(
        (value for key, value in types.items() if prof.get(key)), "EQUITY"
    )

    result = {
        "symbol": prof.get("symbol"),
        "exchange": prof.get("exchangeShortName"),
        "asset_type": asset_type,
        "sector": prof.get("sector"),
        "market_cap": prof.get("mktCap"),
    }

    return result


def fetch_from_yfinance(symbol: str) -> dict:
    """
    Fetch metadata for `symbol` using yfinance.
    """
    ticker = yf.Ticker(symbol)
    info = ticker.info or {}

    result = {
        "symbol": symbol,
        "exchange": info.get("exchange"),
        "asset_type": info.get("quoteType"),
        "sector": info.get("sector"),
        "market_cap": info.get("marketCap"),
    }

    return result
