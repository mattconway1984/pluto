#pylint:disable=missing-docstring
#pylint:enable=missing-docstring

from threading import Event

from pluto.event.event import GetComponentEvent
from pluto.scheduler.instruction import PlutoInstruction
from pluto.scheduler.logger import LOGGER


class Set(PlutoInstruction):
    """
    Pluto instruction to set a (or a list of) public variable(s) exposed by
    a registered PlutoComponent.

    Args:
        component (str): The component whose variable(s) to set.
        attributes (dict of variable: value): Maps values to set to variables.

    Example
        .. code-block::python

            # The following snippet is equivalent to:
            #   my_component.foo = "new foo value
            #   my_component.bar = 10
            Set("my_component", {"foo": "new foo value", "bar": 10})
    """

    def __init__(self, component, attributes):
        self._component = component
        self._attrs = attributes
        self._stop = None

    def __repr__(self):
        return "Set: "

    @property
    def description(self):
        return f"Set: component={self._component} attrs={self._attrs}"

    def run(self, eventbus):
        """
        Run the Set instruction.

        Sets the components variables to the values defined when the Set
        instruction was created.

        Args:
            eventbus (PlutoEventBus): The evenbus which the instruction can
                use to annonymously interact with registered components.

        Raises:
            Exceptions if the component encountered an error when setting the
            requested variables.
        """
        self._stop = Event()
        instance = GetComponentEvent.run(eventbus, self._component)
        for attr, value in self._attrs.items():
            if self._stop.is_set():
                LOGGER.info("%rStopping...", self)
                break
            LOGGER.info("%r%s.%s = %s", self, self._component, attr, value)
            setattr(instance, attr, value)

    def stop(self):
        """
        Stop the Set instruction
        """
        if self._stop:
            self._stop.set()
