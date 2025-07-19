from datetime import datetime
import pandas as pd
from django.test import TestCase
from alpaca.data.timeframe import TimeFrameUnit
from unittest.mock import patch
from data_ingestion.ohlcv.services import (
    ensure_data,
    fetch_missing_data,
    save_to_db,
    convert_tf,
    get_timeframe_model,
    get_expected_bars,
    is_all_bars_available,
    get_exchange,
    convert_exchange,
)
from market_data.models import (
    Stock,
    StockPrice5Min,
    StockPrice15Min,
    StockPrice1H,
    StockPrice1D,
    StockPrice1Month,
)


class StockTestCase(TestCase):

    @patch("data_ingestion.services.fetch_from_yfinance")
    @patch("data_ingestion.services.fetch_from_alpaca")
    def test_ensure_data(self, mock_alpaca, mock_yfinance):
        # mock data
        df_mock = pd.DataFrame(
            {
                "open": [100],
                "high": [105],
                "low": [99],
                "close": [102],
                "volume": [10000],
            },
            index=[pd.Timestamp("2025-01-01")],
        )
        mock_yfinance.return_value = df_mock
        mock_alpaca.return_value = pd.DataFrame()
        self.assertEqual(
            ensure_data("SPY", "1D", datetime(2025, 1, 1), datetime(2025, 1, 2), 2),
            True,
        )
        # Invalid arguments
        with self.assertRaises(TypeError):
            ensure_data("1D", datetime(2025, 1, 1), datetime(2025, 1, 2), 2)
            ensure_data("SPY", datetime(2025, 1, 1), datetime(2025, 1, 2), 2)
            ensure_data("SPY", "1D", datetime(2025, 1, 2), 2)
            ensure_data("SPY", "1D", datetime(2025, 1, 1), datetime(2025, 1, 2))

    def test_convert_tf(self):
        self.assertEqual(convert_tf("1d", "alpaca"), (1, TimeFrameUnit.Day))
        self.assertEqual(convert_tf("5WEEK", "alpaca"), (5, TimeFrameUnit.Week))
        self.assertIsNone(convert_tf("FOO", "alpaca"), None)
        self.assertIsNone(convert_tf("2FOO", "alpaca"), None)

        self.assertEqual(convert_tf("1d", "yfinance"), (1, "d"))
        self.assertEqual(convert_tf("5WEEK", "yfinance"), (5, "wk"))
        self.assertIsNone(convert_tf("FOO", "yfinance"), None)
        self.assertIsNone(convert_tf("2FOO", "yfinance"), None)

    def test_get_timeframe_model(self):
        self.assertEqual(get_timeframe_model("5min"), StockPrice5Min)
        self.assertEqual(get_timeframe_model("15min"), StockPrice15Min)
        self.assertEqual(get_timeframe_model("1h"), StockPrice1H)
        self.assertEqual(get_timeframe_model("1d"), StockPrice1D)
        self.assertEqual(get_timeframe_model("1month"), StockPrice1Month)

        with self.assertRaises(ValueError):
            get_timeframe_model("foo")
            get_timeframe_model("")
            get_timeframe_model(None)

    @patch("data_ingestion.services.StockPrice1D.objects.filter")
    @patch("data_ingestion.services.get_expected_bars")
    def test_is_all_bars_available(self, mock_expected_bars, mock_filter):
        mock_query = mock_filter.return_value

        # All data available:
        # Expected bars
        mock_expected_bars.return_value = 1
        # Actual bars in the DB
        mock_query.count.return_value = 1

        self.assertTrue(
            is_all_bars_available(
                "SPY", "1D", datetime(2025, 1, 1), datetime(2025, 1, 2), StockPrice1D
            )
        )

        # Missing data
        mock_expected_bars.return_value = 2
        # Actual bars in the DB
        mock_query.count.return_value = 1

        self.assertFalse(
            is_all_bars_available(
                "SPY", "1D", datetime(2025, 1, 1), datetime(2025, 1, 3), StockPrice1D
            )
        )

    def test_get_expected_bars(self):
        self.assertEqual(
            get_expected_bars("SPY", "1D", datetime(2025, 1, 1), datetime(2025, 1, 2)),
            1,
        )
        self.assertNotEqual(
            get_expected_bars("SPY", "1D", datetime(2025, 1, 1), datetime(2025, 1, 1)),
            1,
        )
