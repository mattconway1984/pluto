"""
Unit tests for the PlutoInstructionRunner
"""
#pylint:disable=missing-docstring
#pylint: disable=no-self-use

from time import sleep
from time import time as timenow
#from threading import Event
from unittest import TestCase
from unittest.mock import MagicMock

from pluto.scheduler.schedule import PlutoSchedule
from pluto.scheduler.instruction import PlutoInstructionRunner

# Test includes
from instructions.fake_instruction import FakeInstruction, SillyError

class TestSchedule(TestCase):
    """
    Test suite to test the PlutoSchedule
    """

    def test_schedule_description(self):
        """
        When a schedule is created, it's description should be retrievable
        """
        schedule = PlutoSchedule("a simple schedule", [])
        self.assertEqual(schedule.description, "a simple schedule")

    def test_run_simple_schedule(self):
        """
        When a schedule executes to completion (without errors) all instructions
        should have been executed.
        """
        instructions = [FakeInstruction(), FakeInstruction(), FakeInstruction()]
        schedule = PlutoSchedule("a simple schedule", instructions)
        schedule.run(MagicMock())
        for instruction in instructions:
            self.assertTrue(instruction.finished)

    def test_stop_schedule(self):
        """
        If a schedule is stopped whilst running, it should stop the active
        instruction and cease to run any pending instructions.
        In this test, the first instruction should finish almost immediately,
        and the second instruction will take 3seconds to execute (if not
        stopped). The schedule will be stopped after 0.5 second, so the second
        instruction should be stopped and the third should never have been
        started.
        """
        stop_after = 0.5
        instructions = [
            FakeInstruction(),
            FakeInstruction(blocking_time=2),
            FakeInstruction()
        ]
        schedule = PlutoSchedule("a simple schedule", instructions)
        runner = PlutoInstructionRunner(MagicMock(), schedule)
        start = timenow()
        runner.start()
        sleep(stop_after)
        runner.stop()
        duration = timenow() - start
        self.assertAlmostEqual(duration, stop_after, 1)
        self.assertTrue(instructions[0].finished)
        self.assertTrue(instructions[1].stopped)
        self.assertFalse(instructions[2].finished)

    def test_scheduled_instruction_raises_error(self):
        """
        If any instruction in the schedule was to raise an Exception during its
        run method, the schedule should not catch that error and should let it
        be raised.
        """
        instructions = [
            FakeInstruction(),
            FakeInstruction(exception=SillyError()),
            FakeInstruction()]
        schedule = PlutoSchedule("a simple schedule", instructions)
        with self.assertRaises(SillyError):
            schedule.run(MagicMock())
        self.assertTrue(instructions[0].finished)
        self.assertFalse(instructions[1].finished)
        self.assertFalse(instructions[2].finished)
