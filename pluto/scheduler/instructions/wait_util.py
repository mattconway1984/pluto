"""
Contains the Wait instructions, which provide functionality to pause a schedule
and wait for a condition to become true.
"""

from abc import ABC, abstractmethod, abstractproperty
from concurrent.futures import ThreadPoolExecutor
from functools import wraps
from threading import Event, Timer
from time import sleep
from typing import List

from pluto.exceptions.exceptions import BadParameters
from pluto.scheduler.logger import LOGGER


#pylint: disable=too-few-public-methods
class WaitRunner(ABC):
    """
    Interface for wait runners
    """

    @abstractmethod
    def run(self, stop_running):
        """
        Run the wait.

        This API must block until either:
            1. The wait completes
            2. The @stop_running_event is set

        Args:
            stop_running (Event): An event to stop the runner if it becomes set

        Returns:
            (bool) True if the wait completed
        """
        return


#pylint: disable=too-few-public-methods
class StopEventWatcher(WaitRunner):
    """
    Watches a StopEvent.

    Unblocks and returns True if the StopEvent becomes set.

    Args:
        stop_event (Event): The event to watch, if set, will unblock
    """

    def __init__(self, stop_event):
        self._stop_event = stop_event

    def run(self, stop_running):
        """
        Run the stop event watcher.

        Args:
            stop_running (Event): An event to stop the runner if it becomes set

        Returns:
            (boo) True if the watched StopEvent was set
        """
        while not (stop_running.is_set() or self._stop_event.is_set()):
            sleep(0.1)
        LOGGER.debug(
            "StopEventWatcher finished, result=%s", self._stop_event.is_set())
        return self._stop_event.is_set()


class BlockingWait(WaitRunner):
    """
    Blocks for a number of seconds.
    """

    def __init__(self, block_for):
        self._block_for = block_for

    def run(self, stop_running):
        """
        Run the blocking wait.

        Args:
            stop_running (Event): An event to stop the runner if it becomes set

        Returns:
            (bool) True if the wait blocked for the defined amount of time
        """
        LOGGER.debug("BlockingWait waiting for %0.2f", self._block_for)
        result = not stop_running.wait(timeout=self._block_for)
        LOGGER.debug("BlockingWait finished, result=%s", result)
        return result


class TimeoutWait(WaitRunner):
    """
    The timeout out is an inversion of the BlockingWait, where the timeout is
    considered a negative result.

    Args:
        timeout (int): The timeout value (in seconds)
    """

    def __init__(self, timeout):
        self._timeout = timeout

    def run(self, stop_running):
        """
        Run the blocking wait

        Args:
            stop_running (Event): An event to stop the runner if it becomes set

        Returns:
            (bool) True if the wait blocked for the defined amount of time
        """
        LOGGER.debug("TimeoutWait waiting for %0.2fs", self._timeout)
        result = stop_running.wait(timeout=self._timeout)
        LOGGER.debug("TimeoutWait finished, result=%s", result)
        return result


class EventBusWatcher(WaitRunner):
    """
    A wait runner which watches the EventBus for a particular class of event
    to be posted.
    """

    CHECK_INTERVAL = 0.1

    def __init__(self, eventbus, event):
        self._eventbus = eventbus
        self._event = event
        self._event_posted = Event()

    def run(self, stop_running):
        """
        Run the EventBus wait.

        Args:
            stop_running (Event): An event to stop the runner if it becomes set

        Returns:
            (bool) True if an event whose class matches @event is posted to the
            EventBus before the defined timeout
        """
        LOGGER.debug("WaitEvent: waiting for event %s", self._event.__name__)
        self._eventbus.register_handler(self._event, self._event_handler)
        while not (stop_running.is_set() or self._event_posted.is_set()):
            sleep(__class__.CHECK_INTERVAL)
        self._eventbus.deregister_handler(self._event, self._event_handler)
        return self._event_posted.is_set()

    def _event_handler(self, event):
        """
        Handle when an event which matches the registered event class is posted
        to the EventBus, this will stop the wait
        """
        if event:
            LOGGER.debug(
                "WaitEvent: Received event %s ...Continuing",
                self._event.__name__)
            self._event_posted.set()


class AttributesWatcher(WaitRunner):
    """
    A wait runner which watches attributes, if the attributes become "stable",
    this watcher will return.
    """
    #pylint: disable=too-few-public-methods

    class Attribute(ABC):
        """
        Represent a watched attribute

        :param: get_value: A function to retrieve the attributes value
        """

        def __init__(self, get_value):
            self._get_value = get_value

        @property
        def value(self):
            """
            Get the current value of the attribute
            """
            return self._get_value()

        @abstractmethod
        def in_range(self) -> bool:
            """
            Check the attribute falls within an acceptable range

            :returns: True if the attribute is within range
            """
            return

    POLL_INTERVAL = 0.5

    def __init__(self, attributes, stable_for):
        self._attributes = attributes
        self._stable_for = stable_for
        self._attributes_stable = Event()
        self._timer = None

    def run(self, stop_running):
        """
        Run the wait attributes

        Args:
            stop_running (Event): An event to stop the runner if it becomes set

        Returns:
            (bool) True if the watched attributes become stable
        """
        while not (stop_running.is_set() or self._attributes_stable.is_set()):
            if self._timer:
                if not self.all_attributes_in_range:
                    LOGGER.debug("All attributes no longer in the stable range")
                    self._stop_timer()
            else:
                if self.all_attributes_in_range:
                    LOGGER.debug("All attributes entered the stable range")
                    self._start_timer()
            sleep(__class__.POLL_INTERVAL)
        result = self._attributes_stable.is_set()
        return result

    @property
    def all_attributes_in_range(self) -> bool:
        """
        True if all monitored attributes fall within the acceptable range
        """
        return all(attr.in_range() for attr in self._attributes)

    def _start_timer(self):
        """
        Start the timer
        """
        if not self._timer:
            self._timer = Timer(self._stable_for, self._handle_timer)
            self._timer.start()

    def _stop_timer(self):
        """
        Stop the timer
        """
        if self._timer:
            self._timer.cancel()
            self._timer = None

    def _handle_timer(self):
        """
        Handles when the timer fires. The timer fires once the values of the
        monitored attributes have been within the stable range for @stable_for
        seconds
        """
        self._attributes_stable.set()


class WaitMixin:
    """
    Provides useful functionality for wait objects
    """

    def __new__(cls, *args, **kwargs):
        """
        Check the users args and raise a custom exception if they don't satisfy
        the constructor
        """
        try:
            inst = super().__new__(cls,)
            inst.__init__(*args, **kwargs)
        except TypeError as err:
            raise BadParameters(err.args)
        return super().__new__(cls,)

    @staticmethod
    def execute_wait(wait_runners) -> bool:
        """
        Execute the wait by executing each of the wait_runners in parallel

        :param: env: Environment under which the instruction is running
        :param: wait_runners: a number of wait runners to run in parallel
        :returns: the result from the first wait_runner to complete
        """

        class WaitExecutor:
            """
            Class to execute all the wait runner objects required.
            """

            def __init__(self):
                super().__init__()
                self._result = None
                self._stop_running = Event()

            def execute(self, wait_runners):
                """
                Will execute each of the wait runner objects. Once the first
                runner has completed, all the other runners will be stopped
                by setting the stop_running event.

                :returns: The result of the wait runner that completed first
                """
                with ThreadPoolExecutor(max_workers=3) as executor:
                    for runner in wait_runners:
                        future = executor.submit(runner.run, self._stop_running)
                        future.add_done_callback(self._handle_completed)
                return self._result

            def _handle_completed(self, fut):
                """
                Handle futures as they complete, the result should only be
                reaped from the first future that completes as that is the
                WaitRunner which completed first and thus indicates the result
                of the Instruction
                """
                if self._result is None:
                    self._stop_running.set()
                    self._result = fut.result()

        return WaitExecutor().execute(wait_runners)

    def message_after_run(self, result):
        """
        Used by WaitMixin.run_decorator() to log a message after running the
        decorated run method

        :param: result: The result of the decorated run method
        """
        return "{} finished, result = {}".format(
            self.__class__.__name__,
            "Success" if result else "Fail")

    @abstractproperty
    def message_before_run(self):
        """
        The subclass must implement this property, used by
        WaitMixin.run_decorator() to log a message before running the decorated
        run method
        """
        return

    @staticmethod
    def run_decorator(func):
        """
        Decorate the run method of an Instruction, will log a message before
        the run is invoked and then log the result of the instruction
        """
        @wraps(func)
        def inner(*args, **kwargs):
            self = args[0]
            LOGGER.info(self.message_before_run)
            result = func(*args, **kwargs)
            LOGGER.info(self.message_after_run(result))
            return result
        return inner


class WaitAttributesMixin:
    """
    Base class for implementing different types of "wait for attributes"
    behaviour.
    """

    @abstractproperty
    def stable_for(self) -> float:
        """
        Get the amount of time attributes must remain in range to be considered
        stable
        """
        return

    @staticmethod
    def create_attributes(
            component,
            attributes,
            attribute_class,
            args) -> List[AttributesWatcher.Attribute]:
        """
        Create a list of AttributesWatcher.Attribute objects to represent
        the attributes that require monitoring.

        Args:
            component (PlutoComponent): Whose attributes will be monitored
            attributes (:obj:'list' of :obj:'str'): Names of monitored
                attributes
            attribute_class (:obj:'AttributesWatcher.Attribute'): Instance used
                to monitor the attributes
            *args: Variable length argument list (passed to the constructor for
                the attribute class; an AttributesWatcher.Attribute)

        Returns:
            :obj:'list' of 'AttributesWatcher.Attribute': created attributes
        """
        attribute_objects = []
        for attribute in attributes:
            # Get the attribute from the component (ensures the attr exists)
            getattr(component, attribute)
            attribute_objects.append(
                attribute_class(
                    lambda attr=attribute: getattr(component, attr),
                    *args))
        return attribute_objects
