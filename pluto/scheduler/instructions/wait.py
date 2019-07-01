#pylint:disable=missing-docstring
#pylint:enable=missing-docstring

from threading import Event

from pluto.event.event import GetComponentEvent
from pluto.scheduler.instruction import PlutoInstruction
from pluto.scheduler.instructions.wait_util import (
    BlockingWait,
    TimeoutWait,
    StopEventWatcher,
    AttributesWatcher,
    WaitMixin,
    WaitAttributesMixin,
)


class WaitSeconds(PlutoInstruction, WaitMixin):
    """
    Pluto instruction to wait for a specified number of seconds.

    Args:
        seconds (int): The number of seconds to wait.
    """

    def __init__(self, seconds):
        self._stop = None
        self._wait_seconds = seconds
        super().__init__()

    @property
    def description(self):
        return f"WaitSeconds: waiting {self._wait_seconds}"

    @property
    def message_before_run(self):
        """
        Get a string message to describe the wait instruction before it is
        executed(which can be used for debug puporses)
        """
        return "{}: waiting for {:0.2f}s".format(
            __class__.__name__, self._wait_seconds)

    #pylint:disable=unused-argument
    @WaitMixin.run_decorator
    def run(self, eventbus):
        """
        Run the Wait instruction.

        Waits (blocks) for a number of seconds, unless @stop_instruction event
        becomes set.

        Args:
            eventbus (PlutoEventBus): The evenbus which the instruction can
                use to annonymously interact with registered components.
        """
        self._stop = Event()
        result = self.execute_wait([
            BlockingWait(self._wait_seconds),
            StopEventWatcher(self._stop),
        ])
        self._stop = None
        return result

    def stop(self):
        """
        Stop the WaitSeconds instruction
        """
        if self._stop is not None:
            self._stop.set()


class WaitAttributesWithinRange(
        PlutoInstruction,
        WaitAttributesMixin,
        WaitMixin
    ):
    """
    Wait for attribute to come into range, and then remain in range for
    @stable_for seconds

    :param: component: The component whose attributes shall be monitored
    :param: attributes: The attributes to monitor
    :param: stable_for: The time attributes must become stable (in seconds)
    :param: timeout: The maximum time allowed for attributes to become stable
    :param: minimum: The minimum value attributes values must be
    :param: maximum: The maximum value attributes values must be
    """

    #pylint:disable=too-few-public-methods
    class Attribute(AttributesWatcher.Attribute):
        """
        An implementation of the monitored attribute for "value within range"
        value checking
        """

        def __init__(self, getter, minimum, maximum):
            super().__init__(getter)
            self._minimum = minimum
            self._maximum = maximum

        def in_range(self):
            """
            Check the value is in range (gte min and lte max)
            """
            return self._minimum <= self.value <= self._maximum

    #pylint: disable=too-many-arguments
    def __init__(
            self,
            component,
            attributes,
            stable_for,
            timeout,
            minimum,
            maximum):
        self._stable_for = stable_for
        self._minimum = minimum
        self._maximum = maximum
        self._component = component
        self._attributes = attributes
        self._timeout = timeout
        self._stop = None
        super().__init__()

    @property
    def description(self):
        return self.message_before_run

    @property
    def stable_for(self):
        """
        Get the number of seconds the value of the "watched attribute(s)" must
        remain in the defined "stable range".
        """
        return self._stable_for

    @property
    def message_before_run(self):
        """
        Get a string message to describe the wait instruction before it is
        executed(which can be used for debug puporses)
        """
        return "{}: waiting for: {:0.2f} <= {}.{} <= {:0.2f}".format(
            __class__.__name__,
            self._minimum,
            self._component,
            self._attributes,
            self._maximum)

    @WaitMixin.run_decorator
    def run(self, eventbus):
        """
        Run the Wait instruction

        Args:
            eventbus (PlutoEventBus): The evenbus which the instruction can
                use to annonymously interact with registered components.

        Returns:
            True if attributes become stable OR the wait was aborted
        """
        self._stop = Event()
        attrs = self.create_attributes(
            GetComponentEvent.run(eventbus, self._component),
            self._attributes,
            WaitAttributesWithinRange.Attribute,
            (self._minimum, self._maximum,))
        return self.execute_wait([
            TimeoutWait(self._timeout),
            StopEventWatcher(self._stop),
            AttributesWatcher(attrs, self._stable_for),
        ])

    def stop(self):
        """
        Stop exection of the WaitAttributes.
        """
        if self._stop is not None:
            self._stop.set()


class WaitAttributesGreaterThan(
        PlutoInstruction,
        WaitAttributesMixin,
        WaitMixin
    ):
    """
    Wait for attribute to become greater than @threshold, and then remain above
    @threshold for @stable_for seconds. If there is no need for a stable period
    set @stable_for to zero.

    :param: component: The component whose attributes shall be monitored
    :param: attributes: The attributes to monitor
    :param: stable_for: The time attributes must become stable (in seconds)
    :param: timeout: The maximum time allowed for attributes to become stable
    :param: threshold: The minimum value attributes values must become
    """

    class Attribute(AttributesWatcher.Attribute):
        """
        An implementation of the monitored attribute for "value greater than"
        value checking
        """

        def __init__(self, getter, threshold):
            super().__init__(getter)
            self._threshold = threshold

        def in_range(self):
            return self.value >= self._threshold

    #pylint: disable=too-many-arguments
    def __init__(self, component, attributes, stable_for, timeout, threshold):
        self._component = component
        self._attributes = attributes
        self._stable_for = stable_for
        self._timeout = timeout
        self._threshold = threshold
        self._stop = None
        super().__init__()

    @property
    def description(self):
        return self.message_before_run

    @property
    def stable_for(self):
        return self._stable_for

    @property
    def message_before_run(self):
        return "{}: waiting for: {}.{} >= {:0.2f}".format(
            __class__.__name__,
            self._component,
            self._attributes,
            self._threshold)

    @WaitMixin.run_decorator
    def run(self, eventbus):
        """
        Run the Wait instruction

        Args:
            eventbus (PlutoEventBus): The evenbus which the instruction can
                use to annonymously interact with registered components.

        Returns:
            True if attributes become stable OR the wait was aborted
        """
        self._stop = Event()
        attrs = self.create_attributes(
            GetComponentEvent.run(eventbus, self._component),
            self._attributes,
            WaitAttributesGreaterThan.Attribute,
            (self._threshold,))
        return self.execute_wait([
            TimeoutWait(self._timeout),
            StopEventWatcher(self._stop),
            AttributesWatcher(attrs, self._stable_for),
        ])

    def stop(self):
        """
        Stop exection of the WaitAttributes.
        """
        if self._stop is not None:
            self._stop.set()
