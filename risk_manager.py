from abc import ABCMeta, abstractmethod
from event import OrderEvent

class AbstractRiskManager(object):
    """
    The AbstractRiskManager abstract class lets the
    sized order through, creates the corresponding
    OrderEvent object and adds it to a list.
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def refine_orders(self, portfolio, sized_order):
        raise NotImplementedError("Should implement refine_orders()")


class NaiveRiskManager(AbstractRiskManager):
    """
    This NaiveRiskManager object simply lets the
    sized order through, creates the correspondings
    OrderEvent object and adds it to a list.
    """
    def __init__(self):
        pass

    def refine_orders(self, portfolio, sized_order):
        order_event = OrderEvent(
            sized_order.ticker,
            sized_order.action,
            sized_order.quantity
        )
        return [order_event]
