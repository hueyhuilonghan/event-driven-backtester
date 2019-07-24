import unittest
from price_handler import HistoricQuandlBarPriceHandler
import queue
import quandl
import numpy as np
import types
import pandas as pd


class TestHistoricQuandlBarPriceHandler(unittest.TestCase):
    """
    Test HistoricQuandlBarPriceHandler, with tickers including
    "GOOG" and "AMZN"
    """
    def setUp(self):
        """
        instantiation of the HistoricQuandlBarPriceHandler class,
        with init_tickers as "GOOG" and "AMZN"
        """
        events_queue = queue.Queue()
        self.price_handler = HistoricQuandlBarPriceHandler(
            events_queue, init_tickers = ["GOOG", "AMZN"]
        )

    def test_download_quandl_data(self):
        """
        check _download_quandl_data()
        """
        self.assertEqual(len(self.price_handler.tickers_data.keys()), 2)
        self.assertEqual(list(self.price_handler.tickers_data["GOOG"].columns),
                        ['Open', 'Low', 'High', 'Close', 'Volume', "Adj Close", "Ticker"])
        self.assertEqual(list(self.price_handler.tickers_data["AMZN"].columns),
                        ['Open', 'Low', 'High', 'Close', 'Volume', "Adj Close", "Ticker"])


    def test_merge_sort_ticker_data(self):
        """
        check _merge_sort_ticker_data()
        """
        self.assertEqual(type(self.price_handler.bar_stream), types.GeneratorType)
        # need to also check adding start_date, end_date will mess things up

    def test_subscribe_ticker(self):
        """
        check subscribe_ticker()
        """
        self.assertEqual(len(self.price_handler.tickers.keys()), 2)


    def test_stream_event(self):
        """
        check stream_event()
            which simultaneously checks _create_event() and _store_event()
        """
        self.price_handler.stream_next()
        bar_event = self.price_handler.events_queue.get()

        # results from _create_event
        self.assertEqual(bar_event.time, pd.to_datetime("1997-05-16"))
        self.assertEqual(bar_event.period, 86400)
        self.assertEqual(bar_event.ticker, "AMZN")
        self.assertEqual(bar_event.open_price, 223800000)
        self.assertEqual(bar_event.high_price, 237500000)
        self.assertEqual(bar_event.low_price, 205000000)
        self.assertEqual(bar_event.close_price, 207500000)
        self.assertEqual(bar_event.volume, 1225000)
        self.assertEqual(bar_event.adj_close_price, 17291666)

        # results from _store_event
        self.assertEqual(self.price_handler.tickers["AMZN"]["close"], 207500000)
        self.assertEqual(self.price_handler.tickers["AMZN"]["adj_close"], 17291666)
        self.assertEqual(self.price_handler.tickers["AMZN"]["timestamp"], pd.to_datetime("1997-05-16"))



class TestHistoricQuandlBarPriceHandlerWithStartAndEndDate(unittest.TestCase):
    """
    Test HistoricQuandlBarPriceHandler, with tickers including
    "GOOG" and "AMZN", with start and end dates added.
    """
    def setUp(self):
        """
        instantiation of the HistoricQuandlBarPriceHandler class,
        with init_tickers as "GOOG" and "AMZN"
        """
        events_queue = queue.Queue()
        self.price_handler = HistoricQuandlBarPriceHandler(
            events_queue, init_tickers = ["GOOG", "AMZN"],
            start_date="2015-01-01", end_date="2015-12-31",
        )

    def test_download_quandl_data(self):
        """
        check _download_quandl_data()
        """
        self.assertEqual(len(self.price_handler.tickers_data.keys()), 2)
        self.assertEqual(list(self.price_handler.tickers_data["GOOG"].columns),
                        ['Open', 'Low', 'High', 'Close', 'Volume', "Adj Close", "Ticker"])
        self.assertEqual(list(self.price_handler.tickers_data["AMZN"].columns),
                        ['Open', 'Low', 'High', 'Close', 'Volume', "Adj Close", "Ticker"])


    def test_merge_sort_ticker_data(self):
        """
        check _merge_sort_ticker_data()
        """
        self.assertEqual(type(self.price_handler.bar_stream), types.GeneratorType)
        # need to also check adding start_date, end_date will mess things up

    def test_subscribe_ticker(self):
        """
        check subscribe_ticker()
        """
        self.assertEqual(len(self.price_handler.tickers.keys()), 2)


    def test_stream_event(self):
        """
        check stream_event()
            which simultaneously checks _create_event() and _store_event()
        """
        self.price_handler.stream_next()
        bar_event = self.price_handler.events_queue.get()

        # results from _create_event
        self.assertEqual(bar_event.time, pd.to_datetime("2015-01-02"))
        self.assertEqual(bar_event.period, 86400)
        self.assertEqual(bar_event.ticker, "AMZN")
        self.assertEqual(bar_event.open_price, 3125800000)
        self.assertEqual(bar_event.high_price, 3147500000)
        self.assertEqual(bar_event.low_price, 3069601000)
        self.assertEqual(bar_event.close_price, 3085200000)
        self.assertEqual(bar_event.volume, 2788101)
        self.assertEqual(bar_event.adj_close_price, 3085200000)

        # results from _store_event
        self.assertEqual(self.price_handler.tickers["AMZN"]["close"], 3085200000)
        self.assertEqual(self.price_handler.tickers["AMZN"]["adj_close"], 3085200000)
        self.assertEqual(self.price_handler.tickers["AMZN"]["timestamp"], pd.to_datetime("2015-01-02"))


if __name__ == "__main__":
    unittest.main()
