#pylint:disable=missing-docstring
#pylint:enable=missing-docstring
#pylint: disable=too-few-public-methods


class PlutoEvent:
    """
    Base class for event objects which can be posted to the PlutoEventBus
    """

    handlers = []

    @classmethod
    def add_handler(cls, handler):
        """
        Add a handler for this event
        """
        cls.handlers.append(handler)

    @classmethod
    def remove_handler(cls, handler):
        """
        Remove a handler for this event
        """
        cls.handlers.remove(handler)


class PlutoRecEvent(PlutoEvent):
    """
    Base class for recordable events which can be posted to the PlutoEventBus.
    A recordable event will cause the event to be recorded in the data log.
    """


class StopEvent(PlutoEvent):
    """
    Base class for StopEvents which stop execution of the active schedule
    """


class StopExceptionEvent(StopEvent):
    """
    Stop execution due to an exception raised by one of the event handlers
    """


class StopUserEvent(StopEvent):
    """
    Stop execution due to user request
    """


class VariableUpdateEvent(PlutoRecEvent):
    """
    Signals when a (public) component variable has been updated
    """

    def __init__(self, component, variable, value):
        self._component = component
        self._variable = variable
        self._value = value

    @property
    def component(self):
        """
        Get the component whose variable has been updated
        """
        return self._component

    @property
    def variable(self):
        """
        Get the variable whose value has been updated
        """
        return self._variable

    @property
    def value(self):
        """
        Get the value whose of the component variable which has been updated
        """
        return self._value


class GetComponentEvent(PlutoEvent):
    """
    Event to retrieve the instance for a component whose name is known.
    """

    @staticmethod
    def run(eventbus, requested_component):
        """
        Gets a component instance by posting a GetComponentEvent to the
        PlutoEventBus (@eventbus) to retrieve the instance of the component
        whose name matches @requested_component.

        Args:
            eventbus (PlutoEventBus): Active event bus to use.
            requested_component (str): Name of the component to get.

        Raises:
            RuntimeError: if the component could not be retrieved.

        Returns:
            object: Object corresponding to the requested component.
        """
        component_instance = None
        def handle_component(component):
            nonlocal component_instance
            component_instance = component
        eventbus.post(
            event=GetComponentEvent(requested_component, handle_component),
            wait=True)
        if not component_instance:
            raise RuntimeError(f"Failed to get component {requested_component}")
        return component_instance

    def __init__(self, component, callback):
        self._component = component
        self._callback = callback

    @property
    def component(self):
        """
        Get the name of the component to retrive
        """
        return self._component

    @property
    def callback(self):
        """
        Retrieve the callback function to handle the retrieved component
        """
        return self._callback
