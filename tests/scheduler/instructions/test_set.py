"""
Unit tests for the Set instruction
"""
#pylint:disable=no-self-use

from unittest import TestCase
from unittest.mock import MagicMock

from fake_component import FakeComponent, MyCustomRuntimeError


from pluto.event.event import GetComponentEvent
from pluto.scheduler.instructions.set import Set
from pluto.scheduler.instruction import PlutoInstructionRunner


class TestSetInstruction(TestCase):
    """
    Test suite to test the Set instruction
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

    def test_set_single_writable_attribute(self):
        instruction = Set("fake1", {"bar":999})
        instruction.run(self.eventbus)
        self.assertEqual(self.components["fake1"].bar, 999)

    def test_set_multiple_writable_attributes(self):
        instruction = Set("fake1", {"bar":777, "baz": "cowabunga!"})
        instruction.run(self.eventbus)
        self.assertEqual(self.components["fake1"].bar, 777)
        self.assertEqual(self.components["fake1"].baz, "cowabunga!")

    def test_set_instruction_goes_bang(self):
        instruction = Set("fake1", {"bang":999})
        with self.assertRaises(MyCustomRuntimeError):
            instruction.run(self.eventbus)

    def test_set_instruction_read_only_attribute(self):
        instruction = Set("fake1", {"name": "cowabunga"})
        with self.assertRaises(AttributeError):
            instruction.run(self.eventbus)

    def test_set_instruction_stop_whilst_setting_multiple_attrs(self):
        """
        When setting many attributes and the instruction is stopped mid-run,
        only some of the attributes should become set (as requested).
        Simulate this by setting attributes that take a long time to set.
        """
        self.assertFalse(any([
            self.components["fake1"].long_a,
            self.components["fake1"].long_b]))
        instruction = Set("fake1", {"long_a": 0.25, "long_b": 0.25})
        runner = PlutoInstructionRunner(self.eventbus, instruction)
        runner.start()
        runner.stop()
        self.assertTrue(any([
            self.components["fake1"].long_a,
            self.components["fake1"].long_b]))
