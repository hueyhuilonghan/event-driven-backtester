from datetime import datetime
import queue
from event import EventType


from price_handler import HistoricQuandlBarPriceHandler

from position_sizer import NaivePositionSizer
from risk_manager import NaiveRiskManager

from portfolio_handler import PortfolioHandler

from compliance import NaiveCompliance
from execution_handler import IBSimulatedExecutionHandler
from statistics import SimpleStatistics


class TradingSession(object):
    """
    Encapsulates the settings and components for
    carrying out either a backtest or live trading
    sessions.
    """
    def __init__(
        self, output_dir, strategy, tickers,
        equity, start_date, end_date, events_queue,
        session_type="backtest", end_session_time=None,
        price_handler=None, portfolio_handler=None,
        compliance=None, position_sizer=None,
        execution_handler=None, risk_manager=None,
        statistics=None,
        title=None, benchmark=None
    ):
        """
        Set up the backtest variables according to
        what has been passed in.
        """
        self.output_dir = output_dir
        self.strategy = strategy
        self.tickers = tickers
        self.equity = equity
        self.start_date = start_date
        self.end_date = end_date
        self.events_queue = events_queue
        self.price_handler = price_handler
        self.portfolio_handler = portfolio_handler
        self.compliance = compliance
        self.execution_handler = execution_handler
        self.position_sizer = position_sizer
        self.risk_manager = risk_manager
        self.statistics = statistics

        self.title = title
        self.benchmark = benchmark
        self.session_type = session_type
        self._config_session()
        self.cur_time = None

        if self.session_type == "live":
            if self.end_session_time is None:
                raise Exception("Must specify an end_session_time when live trading")

    def _config_session(self):
        """
        Initailizes the necessary classes used
        within the session.
        """
        if self.price_handler is None and self.session_type == "backtest":
            self.price_handler = HistoricQuandlBarPriceHandler(
                self.events_queue, self.tickers,
                start_date=self.start_date,
                end_date=self.end_date
            )

        if self.position_sizer is None:
            self.position_sizer = NaivePositionSizer()

        if self.risk_manager is None:
            self.risk_manager = NaiveRiskManager()

        if self.portfolio_handler is None:
            self.portfolio_handler = PortfolioHandler(
                self.equity,
                self.events_queue,
                self.price_handler,
                self.position_sizer,
                self.risk_manager
            )

        if self.compliance is None:
            self.compliance = NaiveCompliance(self.output_dir)

        if self.execution_handler is None:
            self.execution_handler = IBSimulatedExecutionHandler(
                self.events_queue,
                self.price_handler,
                self.compliance
            )

        if self.statistics is None:
            self.statistics = SimpleStatistics(
                self.output_dir, self.portfolio_handler,
            )

    def _continue_loop_condition(self):
        if self.session_type == "backtest":
            return self.price_handler.continue_backtest
        else:
            return datetime.now() < self.end_session_time

    def _run_session(self):
        """
        Carries out an infinite while loop that pulls the
        events queue and directs each event to either the
        strategy component of the execution handler. The
        loop continues until the event queue has been emptied.
        """
        if self.session_type == "backtest":
            print("Running backtest...")
        else:
            print("Running realtime session until {}".format(self.end_session_time))

        while self._continue_loop_condition():
            try:
                event = self.events_queue.get(False) # what's the False here
            except queue.Empty:
                self.price_handler.stream_next()
            else:
                if event is not None:
                    if (
                        event.type == EventType.TICK or
                        event.type == EventType.BAR
                    ):
                        self.cur_time = event.time
                        self.strategy.calculate_signals(event)
                        self.portfolio_handler.update_portfolio_value()
                        self.statistics.update(event.time, self.portfolio_handler)

                    elif event.type == EventType.SIGNAL:
                        self.portfolio_handler.on_signal(event)

                    elif event.type == EventType.ORDER:
                        self.execution_handler.execute_order(event)
                        # how is this line different between backtest and live versions?

                    elif event.type == EventType.FILL:
                        self.portfolio_handler.on_fill(event)

                    else:
                        raise NotImplementedError("Unsupported event type '{}'".format(event.type))


    def start_trading(self, testing=False):
        """
        Runs either a backtest or live session, and outputs
        performance when complete.
        """
        self._run_session()

        results = self.statistics.get_results()

        print("------------------------------")
        print("Backtest complete.")
        print("Sharpe Ratio: {:2f}".format(results["sharpe"])) # need to check whether string formatting is valid
        print(
            "Max Drawdown: {:2f}%".format(
                results["max_drawdown_pct"] * 100.0
            )
        )


        if not testing:
            self.statistics.plot_results()


        return results
