"""
Unit tests for Wait instructions
"""

from concurrent.futures import ThreadPoolExecutor
from threading import Thread
from time import sleep
from time import time as timenow
from unittest import TestCase
from unittest.mock import MagicMock

from fake_component import MyCustomRuntimeError, FakeComponent

from pluto.scheduler.instruction import PlutoInstructionRunner

from pluto.event.event import GetComponentEvent
from pluto.exceptions.exceptions import BadParameters
from pluto.scheduler.instructions.wait import (
    WaitSeconds,
    WaitAttributesWithinRange,
    WaitAttributesGreaterThan,
)


#pylint:disable=too-few-public-methods
class RunnerMixin:
    """
    Provides useful functionality for running tests
    """

    @staticmethod
    def run_wait(wait, eventbus):
        """
        Run the wait instruction
        :param wait_time: The @seconds param to use when creating a WaitSeconds
        :param env: The environment to run the instruction under

        :returns: The result returned from running the instruction and the
        amount of time it took for the instruction to complete running
        """
        before = timenow()
        result = wait.run(eventbus)
        after = timenow()
        return result, after - before

    @staticmethod
    def set_attribute_value(comp, attr, target_value):
        """
        "Slowly" sets the attributes value to @target_value

        Args:
            comp (object): The component whose attribute needs stabilising
            attr (str): The name of the attribute
            stable_value (int): The stable value to arrive at
        """
        initial_value = getattr(comp, attr)
        if initial_value == target_value:
            adjustment_range = 0
        elif initial_value > target_value:
            adjustment_range = initial_value - target_value
        else:
            adjustment_range = target_value - initial_value
        for _ in range(adjustment_range):
            sleep(0.01)
            current_value = getattr(comp, attr)
            if current_value > target_value:
                setattr(comp, attr, current_value - 1)
            else:
                setattr(comp, attr, current_value + 1)


class TestBase(TestCase):
    """
    Base for tests
    """

    def setUp(self):
        self.components = {}
        self.components["fake1"] = FakeComponent("fake1")
        self.eventbus = MagicMock()
        self.eventbus.post.side_effect = self._eventbus_post

    def tearDown(self):
        self.eventbus = None

    def _eventbus_post(self, event, wait):
        """
        A patched implementation for PlutoEventBus.post
        """
        if wait:
            pass
        # If the code under test is posting a GetComponentEvent, return an
        # object representing the component being requested.
        if isinstance(event, GetComponentEvent):
            event.callback(self.components.get(event.component))


class TestWaitSeconds(TestBase, RunnerMixin):
    """
    Tests for WaitSeconds instruction
    """

    #pylint: disable=missing-docstring
    def test_wait_success(self):
        wait = WaitSeconds(seconds=1)
        result, waited = self.run_wait(wait, self.eventbus)
        self.assertTrue(result)
        self.assertEqual(int(waited), 1)

    #pylint: disable=missing-docstring
    def test_stop_event_whilst_waiting(self):
        wait = WaitSeconds(seconds=10)
        runner = Thread(target=self.run_wait, args=(wait, self.eventbus))
        runner.start()
        sleep(1)
        stop_set = timenow()
        wait.stop()
        runner.join()
        wait_done = timenow()
        self.assertEqual(int(wait_done - stop_set), 0)


class TestWaitAttributesWithinRange(TestBase, RunnerMixin):
    """
    Tests for the Pluto Instruction WaitAttributesWithinRange
    """

    #pylint: disable=missing-docstring
    def test_missing_param_raises_bad_parameters_error(self):
        good_args = {
            "component": "fake1",
            "attributes": ["bar"],
            "stable_for": 0.5,
            "timeout": 10,
            "minimum": 100,
            "maximum": 100,
            }
        for arg in good_args:
            with self.assertRaises(BadParameters):
                incomplete_args = good_args.copy()
                del incomplete_args[arg]
                WaitAttributesWithinRange(**incomplete_args)

    #pylint: disable=missing-docstring
    def test_attribute_that_doesnt_exist(self):
        timeout = 1
        wait = \
            WaitAttributesWithinRange(
                component="fake1",
                attributes=["no_such_attribute"],
                stable_for=0.5,
                timeout=timeout,
                minimum=100,
                maximum=110)
        with self.assertRaises(AttributeError):
            self.run_wait(wait, self.eventbus)

    #pylint: disable=missing-docstring
    def test_attribute_explodes(self):
        timeout = 1
        wait = \
            WaitAttributesWithinRange(
                component="fake1",
                attributes=["bang"],
                stable_for=0.5,
                timeout=timeout,
                minimum=100,
                maximum=110)
        with self.assertRaises(MyCustomRuntimeError):
            self.run_wait(wait, self.eventbus)

    #pylint: disable=missing-docstring
    def test_multiple_attributes_some_exist_some_dont(self):
        timeout = 1
        wait = \
            WaitAttributesWithinRange(
                component="fake1",
                attributes=["fake1", "bar", "no_such_attribute",],
                stable_for=0.5,
                timeout=timeout,
                minimum=100,
                maximum=110)
        with self.assertRaises(AttributeError):
            self.run_wait(wait, self.eventbus)

    #pylint: disable=missing-docstring
    def test_attribute_never_enters_stable_range(self):
        timeout = 1
        wait = \
            WaitAttributesWithinRange(
                component="fake1",
                attributes=["bar"],
                stable_for=0.5,
                timeout=timeout,
                minimum=100,
                maximum=110)
        # Whilst waiting the "watched" attribute doesnt become stable.
        are_stable, waited = self.run_wait(wait, self.eventbus)
        self.assertFalse(are_stable)
        self.assertEqual(int(waited), int(timeout))

    #pylint: disable=missing-docstring
    def test_attribute_enters_stable_range_and_becomes_stable(self):
        timeout = 4
        wait = \
            WaitAttributesWithinRange(
                component="fake1",
                attributes=["bar"],
                stable_for=1,
                timeout=timeout,
                minimum=100,
                maximum=110)
        runner = PlutoInstructionRunner(self.eventbus, wait)
        runner.start()
        # Whilst wait is running in the background, stabilise the watched attr
        self.set_attribute_value(self.components["fake1"], "bar", 105)
        self.assertTrue(runner.result())

    #pylint: disable=missing-docstring
    def test_multiple_attributes_become_stable(self):
        timeout = 4
        wait = \
            WaitAttributesWithinRange(
                component="fake1",
                attributes=["bar", "baz"],
                stable_for=1,
                timeout=timeout,
                minimum=100,
                maximum=110)
        runner = PlutoInstructionRunner(self.eventbus, wait)
        runner.start()
        # Whilst the wait is running in the background, stabilise all attributes
        self.set_attribute_value(self.components["fake1"], "bar", 105)
        self.set_attribute_value(self.components["fake1"], "baz", 105)
        self.assertTrue(runner.result())

    #pylint: disable=missing-docstring
    def test_multiple_attributes_only_one_becomes_stable(self):
        timeout = 4
        wait = \
            WaitAttributesWithinRange(
                component="fake1",
                attributes=["bar", "baz"],
                stable_for=1,
                timeout=timeout,
                minimum=100,
                maximum=110)
        runner = PlutoInstructionRunner(self.eventbus, wait)
        runner.start()
        # Whilst the wait is running in a thread, only stabilise one attr
        self.set_attribute_value(self.components["fake1"], "bar", 105)
        self.assertFalse(runner.result())

    #pylint: disable=missing-docstring
    def test_attribute_enters_then_exists_the_stable_range(self):
        with ThreadPoolExecutor(max_workers=1) as executor:
            unstable_after = 1
            timeout = 4
            wait = \
                WaitAttributesWithinRange(
                    component="fake1",
                    attributes=["bar"],
                    stable_for=2,
                    timeout=timeout,
                    minimum=100,
                    maximum=110)
            # Run the wait in a new thread
            future = executor.submit(self.run_wait, wait, self.eventbus)
            # Whilst the wait is running in a thread, stabilise the attribute
            self.set_attribute_value(self.components["fake1"], "bar", 105)
            # Decrement foo.bar so it leaves the defined "stable range" before
            # being stable for @stable_for seconds
            sleep(unstable_after)
            self.set_attribute_value(self.components["fake1"], "bar", 10)
            # Verify the wait instruction "failed" as attribute is not stable
            are_stable, waited = future.result()
            self.assertFalse(are_stable)
            self.assertEqual(int(waited), int(timeout))

    #pylint: disable=missing-docstring
    def test_multiple_attributes_enter_stable_range_but_one_leaves(self):
        with ThreadPoolExecutor(max_workers=1) as executor:
            unstable_after = 1
            timeout = 4
            wait = \
                WaitAttributesWithinRange(
                    component="fake1",
                    attributes=["bar", "baz"],
                    stable_for=2,
                    timeout=timeout,
                    minimum=100,
                    maximum=110)
            # Run the wait in a new thread
            future = executor.submit(self.run_wait, wait, self.eventbus)
            # Whilst the wait is running in a thread, stabilise all attributes
            self.set_attribute_value(self.components["fake1"], "bar", 105)
            self.set_attribute_value(self.components["fake1"], "baz", 105)
            # After all attributes have stabilised, wait a little time
            sleep(unstable_after)
            # Unstabilise one attribute:
            self.set_attribute_value(self.components["fake1"], "bar", 10)
            # Verify the wait instruction "failed" as "foo.bar" is not stable
            are_stable, waited = future.result()
            self.assertFalse(are_stable)
            self.assertEqual(int(waited), int(timeout))

    #pylint: disable=missing-docstring
    def test_stop_event_while_waiting_and_attributes_unstable(self):
        with ThreadPoolExecutor(max_workers=1) as executor:
            wait_before_stop = 1
            timeout = 4
            wait = \
                WaitAttributesWithinRange(
                    component="fake1",
                    attributes=["bar"],
                    stable_for=2,
                    timeout=timeout,
                    minimum=100,
                    maximum=110)
            # Run the wait in a new thread
            future = executor.submit(self.run_wait, wait, self.eventbus)
            # Wait a little time before stopping
            sleep(wait_before_stop)
            wait.stop()
            result, waited = future.result()
            # When the instruction is stopped, the run() should return True
            self.assertTrue(result)
            self.assertEqual(int(waited), int(wait_before_stop))

    #pylint: disable=missing-docstring
    def test_stop_event_while_waiting_and_attributes_stable(self):
        with ThreadPoolExecutor(max_workers=1) as executor:
            wait_after_stable = 1
            timeout = 4
            wait = \
                WaitAttributesWithinRange(
                    component="fake1",
                    attributes=["bar"],
                    stable_for=2,
                    timeout=timeout,
                    minimum=100,
                    maximum=110)
            # Run the wait in a new thread
            future = executor.submit(self.run_wait, wait, self.eventbus)
            # Whilst the wait is running in a thread, stabilise the attribute
            time_before_stable = timenow()
            self.set_attribute_value(self.components["fake1"], "bar", 105)
            stable_after = timenow() - time_before_stable
            # Whilst stable, Wait a little time before stopping the instruction
            sleep(wait_after_stable)
            wait.stop()
            result, waited = future.result()
            # When the instruction is stopped, the run() should return True
            self.assertTrue(result)
            self.assertEqual(int(waited), int(stable_after + wait_after_stable))


class TestWaitAttributesGreaterThan(TestBase, RunnerMixin):
    """
    Tests for the Pluto Instruction WaitAttributesGreaterThan
    """

    #pylint: disable=missing-docstring
    def test_missing_param_raises_bad_parameters_error(self):
        good_args = {
            "component": "fake1",
            "attributes": ["bar"],
            "stable_for": 0.5,
            "timeout": 10,
            "threshold": 100,
            }
        for arg in good_args:
            with self.assertRaises(BadParameters):
                incomplete_args = good_args.copy()
                del incomplete_args[arg]
                WaitAttributesGreaterThan(**incomplete_args)

    def test_attribute_never_enters_stable_range(self):
        with ThreadPoolExecutor(max_workers=1) as executor:
            timeout = 1
            wait = \
                WaitAttributesGreaterThan(
                    component="fake1",
                    attributes=["bar"],
                    stable_for=0.5,
                    timeout=timeout,
                    threshold=100)
            # Run the wait in a new thread as a future to reap the result:
            future = executor.submit(self.run_wait, wait, self.eventbus)
            # Whilst the wait is running in a thread, the "watched" attribute
            # does not become stable.
            are_stable, waited = future.result()
            self.assertFalse(are_stable)
            self.assertEqual(int(waited), int(timeout))

    def test_attribute_enters_stable_range_and_becomes_stable(self):
        with ThreadPoolExecutor(max_workers=1) as executor:
            timeout = 4
            wait = \
                WaitAttributesGreaterThan(
                    component="fake1",
                    attributes=["bar"],
                    stable_for=1,
                    timeout=timeout,
                    threshold=100)
            # Run the wait in a new thread
            future = executor.submit(self.run_wait, wait, self.eventbus)
            # Whilst the wait is running in a thread, the attribute stabilises
            self.set_attribute_value(self.components["fake1"], "bar", 105)
            # Wait for the wait instruction to finish and reap the result
            are_stable, waited = future.result()
            self.assertTrue(are_stable)
            self.assertLess(waited, timeout)

    def test_multiple_attributes_become_stable(self):
        with ThreadPoolExecutor(max_workers=1) as executor:
            timeout = 4
            wait = \
                WaitAttributesGreaterThan(
                    component="fake1",
                    attributes=["bar", "baz"],
                    stable_for=1,
                    timeout=timeout,
                    threshold=100)
            future = executor.submit(self.run_wait, wait, self.eventbus)
            # Whilst the wait is running in a thread, the attribute stabilises
            self.set_attribute_value(self.components["fake1"], "bar", 105)
            self.set_attribute_value(self.components["fake1"], "baz", 105)
            # Wait for the wait instruction to finish and reap the result
            are_stable, waited = future.result()
            self.assertTrue(are_stable)
            self.assertLess(waited, timeout)

    def test_multiple_attributes_only_some_become_stable(self):
        with ThreadPoolExecutor(max_workers=1) as executor:
            timeout = 4
            wait = \
                WaitAttributesGreaterThan(
                    component="fake1",
                    attributes=["bar", "baz"],
                    stable_for=1,
                    timeout=timeout,
                    threshold=100)
            # Run the wait in a new thread as a future to reap the result:
            future = executor.submit(self.run_wait, wait, self.eventbus)
            # Only stabilise one of the attributes. The other will be out of
            # spec...
            self.set_attribute_value(self.components["fake1"], "bar", 105)
            are_stable, waited = future.result()
            self.assertFalse(are_stable)
            self.assertEqual(int(waited), int(timeout))

    def test_attribute_enters_then_exists_the_stable_range(self):
        with ThreadPoolExecutor(max_workers=1) as executor:
            timeout = 4
            unstable_after = 1
            wait = \
                WaitAttributesGreaterThan(
                    component="fake1",
                    attributes=["bar"],
                    stable_for=2,
                    timeout=timeout,
                    threshold=100)
            # Run the wait in a new thread
            future = executor.submit(self.run_wait, wait, self.eventbus)
            # Whilst the wait is running in a thread, stabilise the attribute
            self.set_attribute_value(self.components["fake1"], "bar", 105)
            # Decrement foo.bar so it leaves the defined "stable range" before
            # being stable for @stable_for seconds
            sleep(unstable_after)
            self.set_attribute_value(self.components["fake1"], "bar", 10)
            # Verify the wait instruction "failed" as attribute is not stable
            are_stable, waited = future.result()
            self.assertFalse(are_stable)
            self.assertEqual(int(waited), int(timeout))

    def test_multiple_attributes_enter_stable_range_but_one_leaves(self):
        with ThreadPoolExecutor(max_workers=1) as executor:
            unstable_after = 1
            timeout = 4
            wait = \
                WaitAttributesGreaterThan(
                    component="fake1",
                    attributes=["bar", "baz"],
                    stable_for=2,
                    timeout=timeout,
                    threshold=100)
            # Run the wait in a new thread
            future = executor.submit(self.run_wait, wait, self.eventbus)
            # Whilst the wait is running in a thread, stabilise all attributes
            self.set_attribute_value(self.components["fake1"], "bar", 105)
            self.set_attribute_value(self.components["fake1"], "baz", 105)
            # After all attributes have stabilised, wait a little time
            sleep(unstable_after)
            # Unstabilise one attribute:
            self.set_attribute_value(self.components["fake1"], "bar", 10)
            # Verify the wait instruction "failed" as "foo.bar" is not stable
            are_stable, waited = future.result()
            self.assertFalse(are_stable)
            self.assertEqual(int(waited), int(timeout))

    def test_stop_event_while_waiting_and_attributes_unstable(self):
        with ThreadPoolExecutor(max_workers=1) as executor:
            timeout = 4
            wait_before_stop = 1
            wait = \
                WaitAttributesGreaterThan(
                    component="fake1",
                    attributes=["bar"],
                    stable_for=2,
                    timeout=timeout,
                    threshold=100)
            # Run the wait in a new thread as a future to reap the result:
            future = executor.submit(self.run_wait, wait, self.eventbus)
            # Wait a little time before stopping
            sleep(wait_before_stop)
            wait.stop()
            result, waited = future.result()
            # When the instruction is stopped, the run() should return True
            self.assertTrue(result)
            self.assertEqual(int(waited), int(wait_before_stop))

    def test_stop_event_while_waiting_and_attributes_stable(self):
        with ThreadPoolExecutor(max_workers=1) as executor:
            timeout = 4
            wait_after_stable = 1
            wait = \
                WaitAttributesGreaterThan(
                    component="fake1",
                    attributes=["bar"],
                    stable_for=2,
                    timeout=timeout,
                    threshold=100)
            # Run the wait in a new thread
            start_time = timenow()
            future = executor.submit(self.run_wait, wait, self.eventbus)
            # Whilst the wait is running in a thread, stabilise the attribute
            self.set_attribute_value(self.components["fake1"], "bar", 105)
            # Whilst stable, Wait a little time before stopping the instruction
            sleep(wait_after_stable)
            wait.stop()
            stop_time = timenow()
            elapsed = stop_time - start_time
            result, waited = future.result()
            # When the instruction is stopped, the run() should return True
            self.assertTrue(result)
            self.assertEqual(int(waited), int(elapsed))
