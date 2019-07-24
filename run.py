from trading_session import TradingSession
from strategy import NaiveBuyAndSellStrategy
import queue
import os

from decimal import *

getcontext().prec = 10

output_dir = os.path.join(os.getcwd(), "outputs") # how will this interact with expanduser
tickers = ["AMZN", "GOOG"]
equity = 100000.0
start_date = "2015-01-01"
end_date = "2016-12-31"

events_queue = queue.Queue()
strategy = NaiveBuyAndSellStrategy(events_queue)


trading_session = TradingSession(
                            output_dir, strategy, tickers,
                            equity, start_date, end_date, events_queue
)

results = trading_session.start_trading()
