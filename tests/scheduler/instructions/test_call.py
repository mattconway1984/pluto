"""
Unit tests for the Call instruction
"""

from unittest import TestCase
from unittest.mock import MagicMock

from fake_component import FakeComponent, MyCustomRuntimeError


from pluto.event.event import GetComponentEvent
from pluto.scheduler.instructions.call import Call


class TestCallInstruction(TestCase):
    """
    Test suite to test the Call instruction
    """
    #pylint: disable=missing-docstring

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

    def test_call_method_that_doesnt_exist(self):
        instruction = Call("fake1", "uh_oh_no_chance")
        with self.assertRaises(AttributeError):
            instruction.run(self.eventbus)

    def test_call_method_that_goes_bang(self):
        instruction = Call("fake1", "bang_bang")
        with self.assertRaises(MyCustomRuntimeError):
            instruction.run(self.eventbus)

    def test_call_simple_method(self):
        instruction = Call("fake1", "simple_method")
        self.assertEqual(instruction.run(self.eventbus), None)

    def test_call_complex_method_using_args(self):
        instruction = Call("fake1", "complex_method", "vfoo", "vbar")
        self.assertEqual(instruction.run(self.eventbus), "silly return")

    def test_call_complex_method_using_kwargs(self):
        instruction = Call("fake1", "complex_method", foo="vfoo", bar="vbar")
        self.assertEqual(instruction.run(self.eventbus), "silly return")

    def test_call_complex_method_using_args_and_kwargs(self):
        instruction = Call("fake1", "complex_method", "vfoo", bar="vbar")
        self.assertEqual(instruction.run(self.eventbus), "silly return")
