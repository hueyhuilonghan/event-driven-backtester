import unittest

from risk_manager import NaiveRiskManager
from event import OrderEvent

class PortfolioMock(object):
    def __init__(self):
        pass

class PositionSizerMock(object):
    def __init__(self):
        pass

    def size_order(self, portfolio, initial_order):
        return initial_order

class TestNaiveRiskManager(unittest.TestCase):
    """
    Test NaiveRiskManager.
    """
    def setUp(self):
        self.portfolio = PortfolioMock()
        self.position_sizer = PositionSizerMock()
        self.risk_manager = NaiveRiskManager()

    def test_risk_manager(self):
        initial_order = OrderEvent(
            "GOOG", "BOT", 100
        )
        resized_order = self.position_sizer.size_order(self.portfolio, initial_order)
        final_order = self.risk_manager.refine_orders(self.portfolio, resized_order)

        self.assertEqual(final_order[0].ticker, "GOOG")
        self.assertEqual(final_order[0].action, "BOT")
        self.assertEqual(final_order[0].quantity, 100)



if __name__ == "__main__":
    unittest.main()
