from datetime import datetime
from django.db import models, IntegrityError
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from market_data.models import (
    Stock,
    StockPrice5Min,
    StockPrice15Min,
    StockPrice1H,
    StockPrice1D,
    StockPrice1Month,
)
import os
import re
import yfinance as yf
import pandas_market_calendars as mcal

# Loading .env variables
api_key_alpaca = os.environ.get("api_key_alpaca")
api_secret_alpaca = os.environ.get("api_secret_alpaca")
api_key_finage = os.environ.get("api_key_finage")
api_key_alpha = os.environ.get("api_key_alpha")
api_key_polygon = os.environ.get("api_key_polygon")
api_key_tiingo = os.environ.get("api_key_tiingo")
api_key_bento = os.environ.get("api_key_bento")

api_src = ["alpaca", "finage", "alphavantage", "polygon", "tiingo", "databento"]


def ensure_data(
    symbol: str, timeframe: str, start: datetime, end: datetime, limit: int
):
    """
    Check if the data exists in the DB, if not then fetch it.
    Returns true if succesful else false.
    """
    PriceModel = get_timeframe_model(timeframe)

    bars_available = is_all_bars_available(symbol, timeframe, start, end, PriceModel)
    if not bars_available:
        return fetch_data(symbol, timeframe, start, end, limit, PriceModel)
    return True


def fetch_data(
    symbol: str, timeframe: str, start: datetime, end: datetime, limit: int, PriceModel
):
    """
    Fetch data from an API with multiple fallbacks
    """

    # yFinance
    try:
        df = fetch_from_yfinance(symbol, timeframe, start, end)
        # Store non empty dataframe
        if df is not None and not df.empty:
            save_to_db(df, symbol, PriceModel)
            return True
    except Exception as e:
        print(f"yfinance fetch failed: {e}")

    # Alpaca
    try:
        df = fetch_from_alpaca(symbol, timeframe, start, end, limit)
        if df is not None and not df.empty:
            save_to_db(df, symbol, PriceModel)
            return True
    except Exception as e:
        print(f"yfinance fetch failed: {e}")

    # If all sources fail
    print(f"df = {df}")
    return False


def save_to_db(df, symbol: str, PriceModel):
    stock, _ = Stock.objects.get_or_create(symbol=symbol.upper())
    # Standardize column names (yFinance)
    df.rename(
        columns={
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume",
        },
        inplace=True,
        errors="ignore",
    )

    records = [
        PriceModel(stock=stock, timestamp=index.to_pydatetime(), **row.to_dict())
        for index, row in df.iterrows()
    ]
    PriceModel.objects.bulk_create(records, ignore_conflicts=True)


def fetch_from_alpaca(
    symbol: str, timeframe: str, start: datetime, end: datetime, limit: int
):
    """
    Get stock market info from the Alpaca API.
     ref. https://docs.alpaca.markets/reference/stockbars-1
    """

    # Convert to timeframe object
    tf_object = convert_tf(timeframe, "alpaca")
    if not tf_object:
        return ValueError("Alpaca: TimeFrame object conversion failed")

    amount, unit = tf_object

    client = StockHistoricalDataClient(api_key_alpaca, api_secret_alpaca)
    request_params = StockBarsRequest(
        symbol_or_symbols=symbol,
        timeframe=TimeFrame(amount=amount, unit=unit),
        start=start,
        end=end,
        limit=limit,
    )
    return client.get_stock_bars(request_params)


def fetch_from_yfinance(symbol: str, timeframe: str, start: datetime, end: datetime):
    tf_object = convert_tf(timeframe, "yfinance")
    if not tf_object:
        return ValueError("yFinance: TimeFrame object conversion failed")

    amount, unit = tf_object
    interval = f"{amount}{unit}"

    return yf.download(tickers=symbol, start=start, end=end, interval=interval)


# Convert the timeframe the API specification
def convert_tf(timeframe: str, endpoint: str):
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


def get_timeframe_model(timeframe: str):
    # Add more timeframe models if needed
    MARKET_DATA_TIMEFRAME_MODEL = {
        "5min": StockPrice5Min,
        "15min": StockPrice15Min,
        "1h": StockPrice1H,
        "1d": StockPrice1D,
        "1month": StockPrice1Month,
    }
    model = MARKET_DATA_TIMEFRAME_MODEL.get(timeframe.lower())
    if not model:
        raise ValueError(f"Invalid timeframe of '{timeframe}'")
    return model


def is_all_bars_available(
    symbol: str, timeframe: str, start: datetime, end: datetime, PriceModel
):
    """
    Ensures all data bars are available in the database according to
    the exchange's calendar.
    """
    expected_bars = get_expected_bars(symbol, timeframe, start, end)

    actual_bars = PriceModel.objects.filter(
        stock__symbol__iexact=symbol,
        timestamp__gte=start,
        timestamp__lte=end,
    ).count()

    return actual_bars >= expected_bars


def get_expected_bars(symbol: str, timeframe: str, start: datetime, end: datetime):
    """
    Gets the expected bars in a specific timeframe given an exchange's calendar.
    """
    # db_exchange = get_exchange(symbol)
    # exchange = mcal.get_calendar(convert_exchange(db_exchange))
    exchange = mcal.get_calendar("NYSE")
    schedule = exchange.schedule(start_date=start.date(), end_date=end.date())

    if timeframe == "1D":
        return len(schedule)
    elif timeframe == "1Month":
        # this is more ambiguous—you may want to count unique months in the schedule
        return schedule.index.to_series().dt.to_period("M").nunique()

    minutes_df = mcal.date_range(schedule, frequency="1min")  # gives trading minutes

    if timeframe == "5Min":
        return len(minutes_df) // 5
    elif timeframe == "15Min":
        return len(minutes_df) // 15
    elif timeframe == "1H":
        return len(minutes_df) // 60

    raise ValueError(f"Unsupported timeframe: {timeframe}")


def get_exchange():
    # Get Exchange from metadata DB
    ...


def convert_exchange():
    # convert exchange to API's inputs
    ...
