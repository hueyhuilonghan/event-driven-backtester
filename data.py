import datetime
import os
import pandas as pd

from abc import ABCMeta, abstractmethod

from event import MarketEvent

import quandl


class DataHandler(object):
    """
    DataHandler is an abstract base class providing an interface
    for all subsequent (inherited) data handlers (both live and
    historic).

    The goal of a (derived) DataHandler object is to output a
    generated set of bars (OLHCVI) for each symbol requested.

    This will replicate how a live strategy would function as
    current market data would be sent "down the pipe." Thus a
    historic and live system will be treated identically by the
    rest of the backtesting suite.
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def get_latest_bars(self, symbol, N=1):
        """
        Returns the last N bars from the latest_symbol_list,
        or fewer if less bars are available.
        """
        raise NotImplementedError("Should implement get_latest_bars()")

    @abstractmethod
    def update_bars(self):
        """
        Pushes the latest bar to the latest symbol structure
        for all symbols in the symbol list.
        """
        raise NotImplementedError("Should implement update_bars()")


class HistoricQuandlDataHandler(DataHandler):
    """
    HistoricQuandlDataHandler is designed to obtain data from
    Quandl upon class instantiation and subsequently provide
    an interface to obtain the "latest" bar in a manner identical
    to a live trading interface.
    """

    def __init__(self, events, symbol_list, start_date):
        """
        Initialize the historic data handler by requesting
        a list of symbols.


        Parameters:
        events - The Event Queue
        symbol_list - A list of symbol strings.
        """
        self.events = events
        self.symbol_list = symbol_list
        self.start_date = start_date

        self.symbol_data = {}
        self.latest_symbol_data = {}
        self.continue_backtest = True

        quandl.ApiConfig.api_key = 'kvQa8EEFyvB4yeMWuVxQ'
        self._download_quandl_data()

    def _download_quandl_data(self):
        """
        Opens the CSV files from the data directory, converting
        them into pandas DataFrames within a symbol dictionary.

        For this handler it will be assumed that the data is taken
        from DTN IQFeed. Thus its format will be respected.
        """
        comb_index = None
        for s in self.symbol_list:
            # download quandl data
            data = quandl.get('EOD/{}'.format(s),
                            start_date=self.start_date,
                            end_date=datetime.datetime.today().strftime('%Y-%m-%d'))
            data = data[["Adj_Open", "Adj_Low", "Adj_High",
                        "Adj_Close", "Adj_Volume"]]
            data.columns = ['open', 'low', 'high',
                            'close', 'volume']
            self.symbol_data[s] = data

            # Combine the index to pad forwrd values
            # padding forward values can be suboptimal though
            if comb_index is None:
                comb_index = self.symbol_data[s].index
            else:
                comb_index.union(self.symbol_data[s].index)

            # Set the latest symbol_data to None
            self.latest_symbol_data[s] = []

        # Reindex the dataframes
        for s in self.symbol_list:
            self.symbol_data[s] = self.symbol_data[s].reindex(index=comb_index, method="pad").iterrows()


    def _get_new_bar(self, symbol):
        """
        Returns the latest bar from the data feed as a tuple of
        (symbol, datetime, open, low, high, close, volume).
        """
        for b in self.symbol_data[symbol]:
            yield tuple([symbol, b[0].strftime("%Y-%m-%d %H:%M:%S"),
                        b[1][0], b[1][1], b[1][2], b[1][3], b[1][4]])


    def get_latest_bars(self, symbol, N=1):
        """
        Returns the last N bars from the latest_symbol list,
        or N-k if less available.
        """
        try:
            bars_list = self.latest_symbol_data[symbol]
        except KeyError:
            print("That symbol is not available in the historical data set.")
        else:
            return bars_list[-N:]


    def update_bars(self):
        """
        Pushes the latest bar to the latest_symbol_data structure for
        all symbols in the symbol list.
        """
        for s in self.symbol_list:
            try:
                bar = next(self._get_new_bar(s))
            except StopIteration:
                self.continue_backtest = False
            else:
                if bar is not None:
                    self.latest_symbol_data[s].append(bar)
        self.events.put(MarketEvent())
