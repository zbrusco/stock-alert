from datetime import datetime, timedelta
from market_data.models import (
    Stock,
    UnobtainableRange,
    StockPrice5Min,
    StockPrice15Min,
    StockPrice1H,
    StockPrice1D,
    StockPrice1Month,
)
from . import api_clients as api
import pandas_market_calendars as mcal
import logging

logger = logging.getLogger(__name__)


# Add more timeframes if needed
TIMEFRAME_CONFIG = {
    "5min": {
        "model": StockPrice5Min,
        "delta": timedelta(minutes=5),
    },
    "15min": {
        "model": StockPrice15Min,
        "delta": timedelta(minutes=15),
    },
    "1h": {
        "model": StockPrice1H,
        "delta": timedelta(hours=1),
    },
    "1d": {
        "model": StockPrice1D,
        "delta": timedelta(days=1),
    },
    "1month": {
        "model": StockPrice1Month,
        "delta": timedelta(days=30),
    },
}


def ensure_data(
    symbol: str, timeframe: str, start: datetime, end: datetime, limit: int
) -> bool:
    """
    Check if the data exists in the DB, if not then fetch it.
    Returns true if succesful else false.
    """
    PriceModel = get_timeframe(timeframe, "model")

    if is_all_bars_available(symbol, timeframe, start, end, PriceModel):
        logger.debug(f"All data already available for {symbol} {timeframe}")
        return True

    result = fetch_missing_data(symbol, timeframe, start, end, limit, PriceModel)

    if result:
        logger.info(f"Successfully ensured data for {symbol} {timeframe}")
    else:
        logger.error(f"Failed to ensure data for {symbol} {timeframe}")

    return result


def fetch_missing_data(
    symbol: str, timeframe: str, start: datetime, end: datetime, limit: int, PriceModel
) -> bool:
    """
    Fetch data from an API with multiple fallbacks.
    Returns true if successful, else false.
    """
    stock, _ = Stock.objects.get_or_create(symbol=symbol)

    existing_timestamps = set(
        PriceModel.objects.filter(
            stock=stock, timestamp__range=(start, end)
        ).values_list("timestamp", flat=True)
    )
    unobtainable_timestamps = list(
        UnobtainableRange.objects.filter(
            stock=stock,
            timeframe=timeframe,
            start__lt=end,
            end__gt=start,
        ).values_list("start", "end")
    )

    missing_dates = []
    expected_timestamps = get_expected_bar_timestamps(symbol, timeframe, start, end)
    # If the calendar check fails fetch the whole data
    if not expected_timestamps:
        return fetch_gap_data(stock, symbol, timeframe, gap_start, gap_end, PriceModel)

    # Ensure all timestamps are available in the response
    for expected_date in expected_timestamps:
        if expected_date in existing_timestamps:
            continue

        # Skip if within unobtainable range
        is_unobtainable = any(
            unobt_start <= expected_date <= unobt_end
            for unobt_start, unobt_end in unobtainable_timestamps
        )
        if is_unobtainable:
            continue

        missing_dates.append(expected_date)

    if not missing_dates:
        return True

    gap = group_ranges(missing_dates, timeframe)

    for gap_start, gap_end in gap:
        if not fetch_gap_data(stock, symbol, timeframe, gap_start, gap_end, PriceModel):
            return False
    return True


def group_ranges(timestamps, timeframe: str) -> list:
    """
    Groups a sorted list of timestamps into contiguous ranges.
    Returns list of (start_date, end_date) tuples.
    """
    if not timestamps:
        return []

    expected_delta = get_timeframe(timeframe, "delta")

    ranges = []
    current_start = timestamps[0]
    current_end = timestamps[0]

    for i in range(1, len(timestamps)):
        current_ts = timestamps[i]
        previous_ts = timestamps[i - 1]

        # Check if current timestamp is contiguous with previous
        if timeframe.lower() == "1d":
            # For daily data, use market calendar logic
            expected_next = previous_ts + expected_delta
            # Allow for weekends and holidays (more flexible gap detection)
            is_contiguous = (current_ts - previous_ts).days <= 4
        else:
            # For intraday data, strict timing
            expected_next = previous_ts + expected_delta
            is_contiguous = abs((current_ts - expected_next).total_seconds()) < 60

        if is_contiguous:
            # Extend current range
            current_end = current_ts
        else:
            # Gap found, close current range and start new one
            ranges.append((current_start, current_end))
            current_start = current_ts
            current_end = current_ts

    # Add the final range
    ranges.append((current_start, current_end))

    return ranges


def fetch_gap_data(
    stock,
    symbol: str,
    timeframe: str,
    gap_start: datetime,
    gap_end: datetime,
    PriceModel,
) -> bool:
    """
    Attempt to fetch data from multiple API sources.
    Returns true if successful, false otherwise.
    """
    logger.info(f"Fetching {symbol} {timeframe} data from {gap_start} to {gap_end}")

    sources = [
        api.fetch_from_yfinance,
        api.fetch_from_alpaca,
        api.fetch_from_finage,
        api.fetch_from_tiingo,
        api.fetch_from_polygon,
        api.fetch_from_databento,
    ]
    for src in sources:
        try:
            data = src(symbol, timeframe, gap_start, gap_end)
            if data is not None and not data.empty:
                save_to_db(data, stock, PriceModel)
                logger.info(
                    f"Successfully fetched {timeframe} {symbol} from {gap_start} to {gap_start} - {src.__name__}"
                )
                return True
        except Exception as e:
            logger.warning(f"Failed to fetch from {src.__name__}: {e}")
            continue

    # If all sources failed, mark as unobtainable
    logger.error(
        f"All API sources failed for {symbol} {timeframe} {gap_start} to {gap_end}"
    )
    UnobtainableRange.objects.create(
        stock=stock,
        timeframe=timeframe,
        start=gap_start,
        end=gap_end,
        reason="All data sources failed",
    )
    return False


def save_to_db(df, stock, PriceModel):
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

    try:
        records = [
            PriceModel(stock=stock, timestamp=index.to_pydatetime(), **row.to_dict())
            for index, row in df.iterrows()
        ]
        PriceModel.objects.bulk_create(records, ignore_conflicts=True)
    except Exception as e:
        logger.error(f"Failed to save data for {stock.symbol}: {e}")
        pass


def get_timeframe(timeframe: str, type: str):
    """
    Get the Django model given a timeframe.
    """
    config = TIMEFRAME_CONFIG.get(timeframe.lower())
    if not config:
        raise ValueError(f"Invalid timeframe of '{timeframe}'")
    if type == "model":
        return config["model"]
    elif type == "delta":
        return config["delta"]
    else:
        raise ValueError(f"Invalid type")


def is_all_bars_available(
    symbol: str, timeframe: str, start: datetime, end: datetime, PriceModel
):
    """
    Ensures all data bars are available in the database according to
    the exchange's calendar.
    """
    expected_bars = get_expected_bars(symbol, timeframe, start, end)
    if expected_bars == -1:
        return False

    actual_bars = PriceModel.objects.filter(
        stock__symbol__iexact=symbol,
        timestamp__gte=start,
        timestamp__lte=end,
    ).count()

    return actual_bars >= expected_bars


def get_expected_bars(
    symbol: str, timeframe: str, start: datetime, end: datetime
) -> int:
    """
    Gets the expected bars in a specific timeframe given an exchange's calendar.
    """
    try:
        db_exchange = get_exchange_from_db(symbol)
        if not db_exchange:
            logger.debug(f"No exchange found in DB for {symbol}, using NYSE")
            raise KeyError  # Get fallback exchange
        exchange = mcal.get_calendar(db_exchange)
    except KeyError:
        exchange = mcal.get_calendar("NYSE")

    schedule = exchange.schedule(start_date=start.date(), end_date=end.date())

    if schedule.empty:
        logger.warning(f"Empty schedule for {symbol} from {start} to {end}")
        return -1  # Skip calendar validation

    try:
        total_bars = len(mcal.date_range(schedule, frequency=timeframe))
        logger.info(f"Expected {total_bars} bars for {symbol} {timeframe}")
        return total_bars
    except (KeyError, ValueError) as e:
        logger.warning(f"Calendar validation failed for {symbol} {timeframe}: {e}")
        return -1  # Skip calendar validation


def get_exchange_from_db(symbol: str):
    """
    Gets the Exchange metadata from the DB.
    """
    stock = Stock.objects.filter(symbol__iexact=symbol).only("exchange").first()
    return stock.exchange if stock else None


def get_expected_bar_timestamps(
    symbol: str, timeframe: str, start: datetime, end: datetime
):
    """
    Returns a list of expected trading timestamps for the given symbol, timeframe, and date range.
    Uses market calendar to respect trading hours and holidays.
    """
    try:
        db_exchange = get_exchange_from_db(symbol)
        exchange = mcal.get_calendar(db_exchange)
    except Exception:
        exchange = mcal.get_calendar("NYSE")

    # Get market schedule for the date range
    schedule = exchange.schedule(start_date=start.date(), end_date=end.date())

    try:
        total_bars = mcal.date_range(schedule, frequency=timeframe)
        return [bar.to_pydatetime() for bar in total_bars]
    except KeyError:
        return []
