import yfinance as yf
import requests
from ..credentials import get_api_credentials
from .utils import get_fmp_asset, yf_to_mcal_exchange

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
    asset_type = get_fmp_asset(prof)

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

    exchange = yf_to_mcal_exchange(info.get("exchange"))
    result = {
        "symbol": symbol,
        "exchange": exchange,
        "asset_type": info.get("quoteType"),
        "sector": info.get("sector"),
        "market_cap": info.get("marketCap"),
    }

    return result
