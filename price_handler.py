import datetime
import os
import pandas as pd

from abc import ABCMeta, abstractmethod

from event import TickEvent, BarEvent

import quandl


class AbstractPriceHandler(object):
    """
    PriceHandler is a base class providing an interface for
    all subsequent (inherited) price handlers (both live and historic).

    The goal of a (derived) PriceHandler is to output a set of
    TickEvents or BarEvents for each financial instrument and place
    them into an event queue.

    This will replicate how a live strategy would function as current
    tick/bar data would be streamed via a brokerage. Thus a historic
    and live systems will be treated identically by the rest of the
    system.
    """

    __metaclass__ = ABCMeta

    def unsubscribe_ticker(self, ticker):
        """
        Unsubscribes the handler from a current ticker symbol.
        """
        ## not sure what this function is for

        try:
            self.tickers.pop(ticker, None)
            self.tickers_data.pop(ticker, None)
        except KeyError:
            print(
                "Could not unsubscribe ticker {} "\
                "as it was never subscribed.".format(ticker)
            )

    def get_last_timestamp(self, ticker):
        """
        Returns the most recent actual timestamp for a given ticker
        """
        if ticker in self.tickers:
            timestamp = self.tickers[ticker]["timestamp"]
            return timestamp
        else:
            print(
                "Timestamp for ticker {} is not "\
                "available from the {}".format(ticker,
                                    self.__class__.__name__)
            )
            return None


class AbstractTickPriceHandler(AbstractPriceHandler):
    def istick(self):
        return True

    def isbar(self):
        return False

    def _store_event(self, event):
        """
        Store price event for bid/ask
        """
        ticker = event.ticker
        self.tickers[ticker]["bid"] = event.bid
        self.tickers[ticker]["ask"] = event.ask
        self.tickers[ticker]["timestamp"] = event.time

    def get_best_bid_ask(self, ticker):
        """
        Returns the most recent bid/ask price for a ticker.
        """
        if ticker in self.tickers:
            bid = self.tickers[ticker]["bid"]
            ask = self.tickers[ticker]["ask"]
            return bid, ask
        else:
            print(
                "Bid/ask values for ticker {} are not "\
                "available from the PriceHandler.".format(ticker)
            )
            return None, None


class AbstractBarPriceHandler(AbstractPriceHandler):
    def istick(self):
        return False

    def isbar(self):
        return True

    def _store_event(self, event):
        """
        Store price event for closing price and adjusted closing price.
        """
        ticker = event.ticker
        self.tickers[ticker]["close"] = event.close_price
        self.tickers[ticker]["adj_close"] = event.adj_close_price
        self.tickers[ticker]["timestamp"] = event.time

    def get_last_close(self, ticker):
        """
        Returns the most recent actual (unadjusted) closing price.
        """
        if ticker in self.tickers:
            close_price = self.tickers[ticker]["close"]
            return close_price
        else:
            print(
                "Close price for ticker {} is not"\
                "available from the BarPriceHandler."
            )
            return None



## below should be cut into a new file as they are not abstract classes
import os
import pandas as pd
import quandl

# from base import AbstractTickPriceHandler
from event import BarEvent


class HistoricQuandlBarPriceHandler(AbstractBarPriceHandler):
    """
    HistoricQuandlBarPriceHandler is designed to obtain daily EOD
    data from Quandl upon class instantiation and subsequently
    provide an interface to stream the "latest" bar in a manner
    identical to a live trading interface.
    """
    def __init__(
        self, events_queue,
        init_tickers=None,
        start_date=None, end_date=None,
        calc_adj_returns=False
    ):
        """
        Takes the events queue and a possible list of initial
        ticker symbols then creates an (optional) list of
        ticker subscriptions and associated prices.
        """
        self.events_queue = events_queue
        self.continue_backtest = True
        self.tickers = {}
        self.tickers_data = {}
        if init_tickers is not None:
            for ticker in init_tickers:
                self.subscribe_ticker(ticker)
        self.start_date = start_date
        self.end_date = end_date
        self.bar_stream = self._merge_sort_ticker_data()
        self.calc_adj_returns = calc_adj_returns
        if self.calc_adj_returns: # what's this?
            self.adj_close_price = []

    def _download_quandl_data(self, ticker):
        """
        Download the Quandl data as a pandas DataFrame and
        store it in a dictionary.
        """
        quandl.ApiConfig.api_key = 'kvQa8EEFyvB4yeMWuVxQ'
        data = quandl.get('EOD/{}'.format(ticker))
        data = data[["Open", "Low", "High",
                    "Close", "Volume", "Adj_Close"]]
        data.columns = ['Open', 'Low', 'High',
                        'Close', 'Volume', "Adj Close"]
        self.tickers_data[ticker] = data
        self.tickers_data[ticker]["Ticker"] = ticker


    def _merge_sort_ticker_data(self):
        """
        Concatenates all of the separate equities DataFrames
        into a single DataFrame that is time ordered, allowing
        tick data events to be added to the queue in a
        chronological fashion.

        Note that this is an idealized situation, utilized
        solely for backtesting. In live trading ticks may arrive
        "out of order."
        """
        df = pd.concat(self.tickers_data.values()).sort_index()
        start = None
        end = None
        if self.start_date is not None:
            start = df.index.searchsorted(self.start_date)
        if self.end_date is not None:
            end = df.index.searchsorted(self.end_date)
        # This is added so that the ticker events are
        # always deterministic, otherwise unit test
        # values will differ
        df["colFromIndex"] = df.index
        df = df.sort_values(by=["colFromIndex", "Ticker"])
        if start is None and end is None:
            return df.iterrows()
        elif start is not None and end is None:
            return df.iloc[start:].iterrows()
        elif start is None and end is not None:
            return df.iloc[:end].iterrows()
        else:
            return df.iloc[start:end].iterrows()


    def subscribe_ticker(self, ticker):
        """
        Subscribes the price handler to a new ticker symbol.
        """
        if ticker not in self.tickers:
            try:
                self._download_quandl_data(ticker)
                dft = self.tickers_data[ticker]
                row0 = dft.iloc[0]

                close = row0["Close"]
                adj_close = row0["Adj Close"]

                ticker_prices = {
                    "close": close,
                    "adj_close": adj_close,
                    "timestamp": dft.index[0]
                }
                self.tickers[ticker] = ticker_prices
            except:
                print(
                    "Could not subscribe ticker {} "\
                    "as no Quandl data is found for pricing.".format(ticker)
                )

        else:
            print(
                "Could not subscribe ticker {} "\
                "as it is already subscribed".format(ticker)
            )


    def _create_event(self, index, period, ticker, row):
        """
        Obtain all elements of the bar from a row of DataFrame
        and return a BarEvent.
        """
        open_price = row["Open"]
        high_price = row["High"]
        low_price = row["Low"]
        close_price = row["Close"]
        adj_close_price = row["Adj Close"]

        volume = int(row["Volume"])
        bev = BarEvent(
            ticker, index, period, open_price,
            high_price, low_price, close_price,
            volume, adj_close_price
        )
        return bev

    def _store_event(self, event):
        """
        Store price event for closing price and adjusted closing price.
        """
        ticker = event.ticker
        # If the calc_adj_returns flag is True, then calculate
        # and store the full list of adjusted closing price
        # percentage returns in a list
        # TODO: Make this faster
        if self.calc_adj_returns:
            prev_adj_close = self.tickers[ticker]["adj_close"]
            cur_adj_close = event.adj_close_price
            self.tickers[ticker][
                "adj_close_ret"
            ] = cur_adj_close / prev_adj_close - 1.0
            self.adj_close_returns.append(self.tickers[ticker]["adj_close_ret"])
        self.tickers[ticker]["close"] = event.close_price
        self.tickers[ticker]["adj_close"] = event.adj_close_price
        self.tickers[ticker]["timestamp"] = event.time


    def stream_next(self):
        """
        Place the next BarEvent onto the event queue.
        """
        try:
            index, row = next(self.bar_stream)
        except StopIteration:
            self.continue_backtest = False
            return
        # Obtain all elements of the bar from the DataFrame
        ticker = row["Ticker"]
        period = 86400 # seconds in a day
        # Create the tick event for the queue
        bev = self._create_event(index, period, ticker, row)
        # Store event
        self._store_event(bev)
        # Send event to queue
        self.events_queue.put(bev)
