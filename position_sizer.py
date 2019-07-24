from abc import ABCMeta, abstractmethod

class AbstractPositionSizer(object):
    """
    The AbstractPositionSizer abstract class modifies
    the quantity (or not) of any share transacted.
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def size_order(self, portfolio, initial_order):
        raise NotImplementedError("Should implement size_order()")


class NaivePositionSizer(AbstractPositionSizer):
    """
    This NaivePositionSizer object follows all
    suggestions from the initial order without
    modifications. Useful for testing simpler
    strategies that do not reside in a larger
    risk-managed portfolio.
    """
    def __init__(self):
        pass

    def size_order(self, portfolio, initial_order):
        return initial_order
