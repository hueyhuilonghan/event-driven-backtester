from abc import ABCMeta, abstractmethod

import pickle # what's this for?

class AbstractStatistics(object):
    """
    Statistics is an abstract class providing an interface for
    all inherited statistic classes (live, historic, custom, etc).

    The goal of a Statistics object is to keep a record of useful
    information about one or many trading strategies as the strategy
    is running. This is done by hooking into the main event loop and
    essentially updating the object according to portfolio performance
    over time.

    Ideally, Statistics should be subclassed according to the strategies
    and timeframe-traded by the user. Different trading strategies
    may require different metrics or frequencies-of-metrics to be updated,
    however the example given is suitable for longer timeframes.
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def update(self):
        """
        Update all the statistics according to values of the
        portfolio and open positions. This should be called
        from within the event loop.
        """
        raise NotImplementedError("Should implement update()")

    @abstractmethod
    def get_results(self):
        """
        Return a dict containing all statistics.
        """
        raise NotImplementedError("Should implement get_results()")

    @abstractmethod
    def plot_results(self):
        """
        Plot all statistics collected up until "now"
        """
        raise NotImplementedError("Should implement plot_results()")

    @abstractmethod
    def save(self, filename):
        """
        Save statistics results to filename.
        """
        raise NotImplementedError("Should implement save()")

    @classmethod # Hmm, why classmethod here?
    def load(cls, filename):
        with open(filename, 'rb') as fd:
            stats = pickle.load(fd)
        return stats


def load(filename):
    return AbstractStatistics.load(filename)




###########
import pickle

import datetime
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

class SimpleStatistics(AbstractStatistics):
    """
    Simple Statistics provides a bare-bones example of
    statistics that can be collected through trading.

    Statistics included are Sharpe Ratio, Drawdown,
    Max Drawdown, Max Drawdown Duration.

    TODO think about Alpha/Beta, compare strategy of benchmark.
    TODO think about speed -- will be bad doing for every tick
        on anything that trades sub-minute.
    TODO think about slippage, fill rate, etc
    TODO brokerage costs?

    TODO need some kind of trading-frequency parameter in setup
        Sharpe calculations need to know if daily, hourly,
        minutely, etc.
    """
    def __init__(self, output_dir, portfolio_handler):
        """
        Takes in a portfolio handler.
        """
        self.output_dir = output_dir
        self.drawdowns = [0]
        self.equity = []
        self.equity_returns = [0.0]
        # Initialize timeseries. Correct timestamp not available yet.
        self.timeseries = ["0000-00-00 00:00:00"]
        # Initialize in order for first-step calculations to be correct.
        current_equity = portfolio_handler.portfolio.equity
        self.hwm = [current_equity] # high-water mark
        self.equity.append(current_equity)

    def update(self, timestamp, portfolio_handler):
        """
        Update all statistics that must be tracked over time.
        """
        if timestamp != self.timeseries[-1]:
            # Retrieve equity value of Portfolio
            current_equity = portfolio_handler.portfolio.equity
            self.equity.append(current_equity)
            self.timeseries.append(timestamp)

            # Calculate percentage return between current and previous equity value.
            pct = ((self.equity[-1] - self.equity[-2]) / self.equity[-1]) * 100 # shouldn't this be divided by self.equity[-2]?
            self.equity_returns.append(round(pct, 4))
            # Calculate Drawdown.
            self.hwm.append(max(self.hwm[-1], self.equity[-1]))
            self.drawdowns.append(self.hwm[-1] - self.equity[-1])

    def get_results(self):
        """
        Return a dict with all important results & stats.
        """

        # Modify timeseries in local scope only. We initialize with 0-date,
        # but would rather show a realistic starting date.
        timeseries = self.timeseries
        timeseries[0] = pd.to_datetime(timeseries[1]) - pd.Timedelta(days=1)
        # not sure what the above is doing

        statistics = {}
        statistics["sharpe"] = self.calculate_sharpe()
        statistics["drawdowns"] = pd.Series(self.drawdowns, index=timeseries)
        statistics["max_drawdown"] = max(self.drawdowns)
        statistics["max_drawdown_pct"] = self.calculate_max_drawdown_pct()
        statistics["equity"] = pd.Series(self.equity, index=timeseries)
        statistics["equity_returns"] = pd.Series(self.equity_returns, index=timeseries)

        return statistics


    def calculate_sharpe(self, benchmark_return=0.00):
        """
        Calculate the sharpe ratio of our equity_returns.

        Expects benchmark_return to be, for example, 0.01, for 1%
        """
        excess_returns = pd.Series(self.equity_returns) - benchmark_return / 252 # what's the 252 for?

        # Return the annualized Sharpe ratio based on the excess daily returns
        return round(self.annualized_sharpe(excess_returns), 4)

    def annualized_sharpe(self, returns, N=252):
        """
        Calculate the annualized Sharpe ratio of a returns stream
        based on a number of trading period, N. N defaults to 252,
        which then assumes a stream of daily returns.

        The function assumes that the returns are the excess of
        those compared to a benchmark.
        """
        return np.sqrt(N) * returns.mean() / returns.std()

    def calculate_max_drawdown_pct(self):
        """
        Calculate the percentage drop related to the "worst"
        drawdown seen.
        """
        drawdown_series = pd.Series(self.drawdowns)
        equity_series = pd.Series(self.equity)
        bottom_index = drawdown_series.idxmax()
        try:
            top_index = equity_series[:bottom_index].idxmax()
            pct = (
                (equity_series.iloc[top_index] - equity_series.iloc[bottom_index]) /
                equity_series.iloc[top_index] * 100
            )
            return round(pct, 4)
        except ValueError:
            return np.nan # what is this line? in what situation will np.nan be returned?

    def plot_results(self):
        """
        A simple script to plot the balance of the portfolio, or
        "equity curve," as a function of time.
        """
        sns.set_palette("deep", desat=.6)
        sns.set_context(rc={"figure.figsize": (8, 4)})

        # Plot two charts: Equity curve, period returns
        fig = plt.figure()
        fig.patch.set_facecolor("white")

        df = pd.DataFrame()
        df["equity"] = pd.Series(self.equity, index=self.timeseries)
        df["equity_returns"] = pd.Series(self.equity_returns, index=self.timeseries)
        df["drawdowns"] = pd.Series(self.drawdowns, index=self.timeseries)

        # Plot the equity curve
        ax1 = fig.add_subplot(311, ylabel="Equity Value")
        df["equity"].plot(ax=ax1, color=sns.color_palette()[0])

        # Plot the returns
        ax2 = fig.add_subplot(312, ylabel="Equity Returns")
        df["equity_returns"].plot(ax=ax2, color=sns.color_palette()[1])

        # drawdown, max_dd, dd_duration = self.create_drawdowns(df["Equity"]) # what is this?
        ax3 = fig.add_subplot(313, ylabel="Drawdowns")
        df["drawdowns"].plot(ax=ax3, color=sns.color_palette()[2])

        # Rotate dates
        fig.autofmt_xdate()

        # Plot the figure
        plt.show()


    def get_filename(self, filename=""):
        if filename == "":
            now = datetime.datetime.utcnow()
            filename = "statistics_" + now.strftime("%Y-%m-%d_%H%M%S") + ".pkl"
            filename = os.path.expanduser(os.path.join(self.output_dir, filename))
        return filename

    def save(self, filename=""):
        filename = self.get_filename(filename)
        print("Save results to '{}'".format(filename))
        with open(filename, "wb") as fd:
            pickle.dump(self, fd)
