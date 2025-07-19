import logging
from datetime import timedelta
from django.utils import timezone
from market_data.models import Stock, StockMetadata
from data_ingestion.metadata import client

logger = logging.getLogger(__name__)

UPDATE_FREQUENCY_DAYS = 30


def is_metadata_updated(symbol: str) -> bool:
    """
    Check if metadata is missing or outdated.
    Returns true if metadata was updated within the specified days, false otherwise.
    """
    try:
        stock = Stock.objects.get(symbol__iexact=symbol)
    except Stock.DoesNotExist:
        return False

    latest = stock.stockmetadata_set.order_by("-last_updated").first()
    if not latest:
        return False
    return timezone.now() - latest.last_updated <= timedelta(days=UPDATE_FREQUENCY_DAYS)


def ensure_metadata(symbol: str, force_update: bool = False) -> bool:
    """
    Ensure metadata exists for a symbol.

    Args:
        symbol: Stock symbol
        force_update: Force update even if cache is fresh

    Returns:
        True if metadata is available, False if fetch failed
    """
    if not force_update and is_metadata_updated(symbol):
        logger.debug(f"Metadata for {symbol} is updated, skipping update")
        return True

    return fetch_metadata(symbol)


def fetch_metadata(symbol: str):

    logger.info(f"Fetching {symbol} metadata")
    stock, _ = Stock.objects.get_or_create(symbol=symbol)

    sources = [
        client.fetch_from_fmp,
        client.fetch_from_yfinance,
    ]

    for src in sources:
        try:
            metadata = src(symbol)
            if metadata:
                save_metadata(metadata, stock)
                logger.info(f"Success: fetched metadata for {symbol} - {src.__name__}")
                return True
        except Exception as e:
            logger.warning(f"Fail to fetch from {src.__name__}: {e}")
            continue

    # If all sources failed, mark as unobtainable
    logger.error(f"All API sources failed to fetch metadata for {symbol}")
    return False


def save_metadata(metadata: dict, stock: object) -> bool:
    exchange = metadata.get("exchange")
    if exchange and stock.exchange != exchange:
        stock.exchange = exchange
        stock.save()

    try:
        StockMetadata.objects.create(
            stock=stock,
            asset_type=metadata["asset_type"],
            sector=metadata["sector"],
            market_cap=metadata["market_cap"],
            last_updated=timezone.now(),
        )
        return True
    except Exception as e:
        logger.exception(f"Failed to save metadata for {stock.symbol}")
        return False
