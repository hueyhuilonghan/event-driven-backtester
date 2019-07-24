import unittest
from price_parser import PriceParser


print(PriceParser.display("10"))



# class TestPriceParser(unittest.TestCase):
#     """
#     Test PriceParser
#     """
#
#     def test_parse(self):
#         """
#         Test parse.
#         """
#         self.assertEqual(PriceParser.parse(10), "MSFT")
#         self.assertEqual(PriceParser.parse("10"), "BOT")
#         self.assertEqual(PriceParser.parse(10.0), 0)
#
#
#
#
# if __name__ == "__main__":
#     unittest.main()
