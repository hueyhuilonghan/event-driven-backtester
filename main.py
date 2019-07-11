from data import HistoricQuandlDataHandler
from strategy import BuyAndHoldStrategy
from portfolio import NaivePortfolio
from execution import SimulatedExecutionHandler
import queue

# Declare event queues
events = queue.Queue()

# Declare the variables necessary to instantiate the class objects
symbol_list = ['AAPL', 'GOOGL']
start_date = '2015-01-01'
initial_capital = 100000.0

# Declare the components with respective parameters
bars = HistoricQuandlDataHandler(events, symbol_list, start_date)
strategy = BuyAndHoldStrategy(bars, events)
port = NaivePortfolio(bars, events, start_date, initial_capital=initial_capital)
broker = SimulatedExecutionHandler(events)

while True:
    # Update the bars (specific backtest code, as opposed to live trading)
    if bars.continue_backtest == True:
        bars.update_bars()
    else:
        break

    # Handle the events
    while True:
        try:
            event = events.get(False)
        except queue.Empty:
            break
        else:
            if event is not None:
                if event.type == "MARKET":
                    strategy.calculate_signals(event)
                    port.update_timeindex(event)

                elif event.type == "SIGNAL":
                    port.update_signal(event)

                elif event.type == "ORDER":
                    broker.execute_order(event)

                elif event.type == "FILL":
                    port.update_fill(event)

    # # 10-Minute heartbeat
    # time.sleep(10*60)

port.create_equity_curve_dataframe()
print(port.equity_curve)
