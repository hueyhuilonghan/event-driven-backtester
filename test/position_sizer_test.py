import unittest
from position_sizer import NaivePositionSizer

from event import OrderEvent

class PortfolioMock(object):
    def __init__(self):
        pass

class TestNaivePositionSizer(unittest.TestCase):
    """
    Test the NaivePositionSizer.
    """
    def setUp(self):
        self.portfolio = PortfolioMock()
        self.naive_position_sizer = NaivePositionSizer()


    def test_size_order(self):
        """
        Test the size_order function for NaivePositionSizer.
        """
        initial_order = OrderEvent(
            "GOOG", "BOT", 100
        )
        sized_order = self.naive_position_sizer.size_order(self.portfolio,
                                                        initial_order)

        self.assertEqual(sized_order.ticker, "GOOG")
        self.assertEqual(sized_order.action, "BOT")
        self.assertEqual(sized_order.quantity, 100)


if __name__ == "__main__":
    unittest.main()
