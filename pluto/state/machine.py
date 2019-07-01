#pylint:disable=missing-docstring
#pylint:enable=missing-docstring


from logging import getLogger

from pluto.state.state import PlutoState


DEFAULT_LOGGER = getLogger("PlutoStateMachine")


class PlutoStateMachine:
    """
    The PlutoStateMachine represents a class able to run different
    implementations of class PlutoState

    :param state_base: Class which represents the base class for the states
    :param logger: The logger instance which the statemachine will use to log
    """

    def __init__(self, state_base, logger=None):
        assert issubclass(state_base, PlutoState)
        if logger is None:
            self._logger = DEFAULT_LOGGER
        else:
            self._logger = logger
        # Create instances for each state that inherrits from @state_base
        self._states = \
            {cls.name: cls(self) for cls in state_base.__subclasses__()}
        # The current state:
        self._state = None

    @property
    def logger(self):
        """
        Get the statemachines logger (required by PlutoState instances)
        """
        try:
            logger = self._logger
        except AttributeError:
            logger = None
        return logger

    @property
    def state(self) -> str:
        """
        Name of the current state
        """
        try:
            name = self._state.name
        except AttributeError:
            name = ""
        return name

    def set_state(self, state):
        """
        Set the state

        :param state: The name of the state to set
        """
        new_state = self._states.get(state)
        if not new_state:
            raise ValueError(
                "Invalid state {}. Valid states are {}."
                .format(state, self._states.keys()))
        if self._state:
            self._state.leave()
            self._logger.info("Left state: %s", self._state.name)
        self._state = new_state
        self.logger.info("Entered state: %s", state)
        self._state.enter()
