#pylint:disable=missing-docstring
#pylint:disable=enable-docstring


from abc import ABC, abstractmethod


class PlutoState(ABC):
    """
    Base class for a PlutoState runnable by the PlutoStateMachine

    :attr machine: reference to the statemachine which owns the state
    :attr logger: reference to the logger which the state should use
    """

    name = None

    def __init__(self, machine):
        self.machine = machine
        self.logger = machine.logger

    @abstractmethod
    def enter(self):
        """
        Called by the PlutoStateMachine when the state is "entered"
        """
        return

    @abstractmethod
    def leave(self):
        """
        Called by the PlutoStateMachine when the state is "left"
        """
        return
