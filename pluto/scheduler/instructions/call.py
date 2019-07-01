#pylint:disable=missing-docstring
#pylint:enable=missing-docstring

from threading import Event

from pluto.event.event import GetComponentEvent
from pluto.scheduler.instruction import PlutoInstruction
from pluto.scheduler.logger import LOGGER


class Call(PlutoInstruction):
    """
    Pluto instruction to call a public method exposed by a registered
    PlutoComponent.

    Args:
        component (str): The component whose method will be called.
        method (str): The name of the method to call.
        *args (list): Arguments to be passed to the method call.
        **kwargs (dict): Keyword arguments to be passed to the method call.

    Example
        .. code-block::python

            # The following snippet is equivalent to:
            #   my_component.my_method("hello", 123)
            Call("my_component", "my_method", ["hello", 123])

            # The following snippet is equivalent to:
            #   my_component.my_method()
            Call("my_component", "my_method")
    """

    def __init__(self, component, method, *args, **kwargs):
        self._component = component
        self._method = method
        self._args = args
        self._kwargs = kwargs
        self._stop = None

    @property
    def description(self):
        return \
            "Call {}.{}({})".format(
                self._component,
                self._method,
                f"args={[arg for arg in self._args]} kwargs={self._kwargs}")

    def run(self, eventbus):
        """
        Run the Call instruction.

        Calls the components method defined when the Call instruction was
        created. This API will log the return value from the method that is
        being called.

        Args:
            eventbus (PlutoEventBus): The evenbus which the instruction can
                use to annonymously interact with registered components.

        Raises:
            Exceptions if the component encountered an error as a result of
            executing the method being called.

        Returns:
            The return value from the method being called.
        """
        self._stop = Event()
        instance = GetComponentEvent.run(eventbus, self._component)
        callable_method = getattr(instance, self._method)
        LOGGER.info(
            "Calling: %s.%s(%s)",
            self._component,
            self._method,
            f"args={[arg for arg in self._args]} kwargs={self._kwargs}")
        result = callable_method(*self._args, **self._kwargs)
        LOGGER.info(
            "Called: %s.%s(), returned: ##%s##",
            self._component,
            self._method, result)
        return result

    def stop(self):
        """
        Stop the Call instruction

        FIX: Think about how to stop a long life method call,

        i.e. stop a scan for hours, maybe that's just an implementation thing,
        such as having to have an object that has a stop() method, which would
        unblock the method call? food for thought.
        """
        if self._stop is not None:
            self._stop.set()
