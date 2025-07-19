import re
import pandas as pd
import yfinance as yf
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from ..credentials import get_api_credentials
from datetime import datetime

# Load the API keys
_credentials = get_api_credentials()


def convert_tf(timeframe: str, endpoint: str):
    """
    Converts the timeframe according to the API's specification.
    """
    if matches := re.search(
        r"^(\d{1,2})(min|[h]|[d]|week|month)", timeframe, re.IGNORECASE
    ):
        amount, unit = matches.groups()
        amount = int(amount)
        unit = unit.lower()
    else:
        return None

    if endpoint == "alpaca":
        alpaca_unit = {
            "min": TimeFrameUnit.Minute,
            "h": TimeFrameUnit.Hour,
            "d": TimeFrameUnit.Day,
            "week": TimeFrameUnit.Week,
            "month": TimeFrameUnit.Month,
        }
        unit_converted = alpaca_unit.get(unit)

    elif endpoint == "yfinance":
        # Valid intervals: [1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 4h, 1d, 5d, 1wk, 1mo, 3mo]
        yf_unit = {
            "min": "m",
            "h": "h",
            "d": "d",
            "week": "wk",
            "month": "mo",
        }
        unit_converted = yf_unit.get(unit)

    else:
        return None
    return amount, unit_converted


def fetch_from_alpaca(
    symbol: str, timeframe: str, start: datetime, end: datetime, limit: int = None
) -> pd.DataFrame:
    """
    Fetch data from Alpaca API.
     ref. https://docs.alpaca.markets/reference/stockbars-1
    """

    # Convert to timeframe object
    tf_object = convert_tf(timeframe, "alpaca")
    if not tf_object:
        raise ValueError("Alpaca: TimeFrame object conversion failed")

    amount, unit = tf_object

    client = StockHistoricalDataClient(
        _credentials["alpaca_key"], _credentials["alpaca_secret"]
    )
    request_params = StockBarsRequest(
        symbol_or_symbols=symbol,
        timeframe=TimeFrame(amount=amount, unit=unit),
        start=start,
        end=end,
        limit=limit,
    )
    return client.get_stock_bars(request_params).df


def fetch_from_yfinance(
    symbol: str, timeframe: str, start: datetime, end: datetime
) -> pd.DataFrame:
    tf_object = convert_tf(timeframe, "yfinance")
    if not tf_object:
        return ValueError("yFinance: TimeFrame object conversion failed")

    amount, unit = tf_object
    interval = f"{amount}{unit}"

    return yf.download(tickers=symbol, start=start, end=end, interval=interval)


def fetch_from_finage(
    symbol: str, timeframe: str, start: datetime, end: datetime
) -> pd.DataFrame:
    """Fetch data from Finage API"""
    # TODO
    pass


def fetch_from_tiingo(
    symbol: str, timeframe: str, start: datetime, end: datetime
) -> pd.DataFrame:
    """Fetch data from Tiingo API"""
    # TODO
    pass


def fetch_from_polygon(
    symbol: str, timeframe: str, start: datetime, end: datetime
) -> pd.DataFrame:
    """Fetch data from Polygon API"""
    # TODO
    pass


def fetch_from_databento(
    symbol: str, timeframe: str, start: datetime, end: datetime
) -> pd.DataFrame:
    """Fetch data from DataBento API"""
    # TODO
    pass
