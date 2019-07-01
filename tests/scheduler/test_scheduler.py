"""
Unit tests for the PlutoScheduler, which is a component to run PlutoSchedules
"""
#pylint:disable=missing-docstring
#pylint: disable=no-self-use

#from time import sleep
#from time import time as timenow
#from threading import Event
from unittest import TestCase
from unittest.mock import MagicMock

from pluto.scheduler.scheduler import PlutoScheduler
#from pluto.scheduler.schedule import PlutoSchedule
#from pluto.scheduler.instruction import PlutoInstructionRunner

# Test includes
#from instructions.fake_instruction import FakeInstruction, SillyError
from fake_schedule import FakeSchedule


class TestScheduler(TestCase):
    """
    Test suite to test the PlutoScheduler
    """

    @classmethod
    def setUpClass(cls):
        cls.scheduler = PlutoScheduler("scheduler", MagicMock())

    def test_load_bad_schedule_type(self):
        with self.assertRaises(Exception):
            TestScheduler.scheduler.load({"foo":1, "bar":"hello"})

    def test_run_all_schedules(self):
        schedule_a = FakeSchedule("schedlue a")
        schedule_b = FakeSchedule("schedlue b")
        schedule_c = FakeSchedule("schedlue c")
        TestScheduler.scheduler.load(schedule_a)
        TestScheduler.scheduler.load(schedule_b)
        TestScheduler.scheduler.load(schedule_c)
        TestScheduler.scheduler.run()
        TestScheduler.scheduler.wait()
        self.assertTrue(schedule_a.finished)
        self.assertTrue(schedule_b.finished)
        self.assertTrue(schedule_c.finished)
