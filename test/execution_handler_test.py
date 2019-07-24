import unittest
import queue
from execution_handler import IBSimulatedExecutionHandler
from event import OrderEvent
from decimal import Decimal
import pandas as pd
from price_parser import PriceParser


class TickPriceHandlerMock(object):
    def __init__(self):
        # self.tickers = {
        #     "MSFT": {"bid": Decimal("50.28"),
        #             "ask": Decimal("50.31"),
        #             "timestamp": pd.to_datetime("2015-01-01")},
        #     "GOOG": {"bid": Decimal("705.46"),
        #             "ask": Decimal("705.46"),
        #             "timestamp": pd.to_datetime("2015-01-02")},
        #     "AMZN": {"bid": Decimal("564.14"),
        #             "ask": Decimal("565.14"),
        #             "timestamp": pd.to_datetime("2015-01-03")},
        # }
        self.tickers = {
            "MSFT": {"bid": 50.28,
                    "ask": 50.31,
                    "timestamp": pd.to_datetime("2015-01-01")},
            "GOOG": {"bid": 705.46,
                    "ask": 705.46,
                    "timestamp": pd.to_datetime("2015-01-02")},
            "AMZN": {"bid": 564.14,
                    "ask": 565.14,
                    "timestamp": pd.to_datetime("2015-01-03")},
        }

    def istick(self):
        return True

    def get_best_bid_ask(self, ticker):
        bid = self.tickers[ticker]["bid"]
        ask = self.tickers[ticker]["ask"]
        return bid, ask

    def get_last_timestamp(self, ticker):
        timestamp = self.tickers[ticker]["timestamp"]
        return timestamp


class TestIBSimulatedExecutionHandler(unittest.TestCase):
    """
    Test IBSimulatedExecutionHandler.
    """
    def setUp(self):
        self.events_queue = queue.Queue()
        self.price_handler = TickPriceHandlerMock()
        self.execution_handler = IBSimulatedExecutionHandler(self.events_queue,
                                                            self.price_handler)


    def test_execute_order(self):
        order_event = OrderEvent(
            "GOOG", "BOT", 100
        )
        self.execution_handler.execute_order(order_event)
        fill_event = self.events_queue.get()

        self.assertEqual(fill_event.timestamp, pd.to_datetime("2015-01-02"))
        self.assertEqual(fill_event.ticker, "GOOG")
        self.assertEqual(fill_event.action, "BOT")
        self.assertEqual(fill_event.quantity, 100)
        self.assertEqual(fill_event.exchange, "ARCA")
        # self.assertEqual(fill_event.price, Decimal("50.31"))
        self.assertEqual(fill_event.price, 705.46)
        self.assertEqual(PriceParser.display(fill_event.commission), 1)


if __name__ == "__main__":
    unittest.main()
