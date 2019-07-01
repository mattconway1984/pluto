"""
Unit tests for the Parallel instruction
"""
#pylint:disable=missing-docstring
#pylint:disable=no-self-use

from time import time as timenow
from time import sleep
from unittest import TestCase
from unittest.mock import MagicMock

from fake_instruction import FakeInstruction, SillyError
from pluto.scheduler.instructions.parallel import Parallel
from pluto.scheduler.instruction import PlutoInstructionRunner


class TestParallelInstruction(TestCase):
    """
    Test suite to test the Parallel instruction
    """

    def test_master_finishing_causes_slaves_to_stop(self):
        """
        When the master instruction finishes running, all the slaves should
        be stopped by the Parallel.
        Note: For this test, the slaves would run for 10seconds (if not stopped)
        whilst the master only runs for a very short time. Therefore, when the
        master finishes, all the slaves should be stopped.
        """
        expected_duration = 0.1
        master = FakeInstruction(blocking_time=expected_duration)
        slaves = [
            FakeInstruction(blocking_time=10),
            FakeInstruction(blocking_time=10)]
        instruction = Parallel(master, *slaves)
        runner = PlutoInstructionRunner(MagicMock(), instruction)
        start = timenow()
        runner.start()
        runner.wait()
        duration = timenow() - start
        self.assertAlmostEqual(duration, expected_duration, 1)
        # master finished before all slaves, ensure all slaves were stopped:
        sleep(0.1) # Time allowed for run() methods to be collected
        for slave in slaves:
            self.assertTrue(slave.stopped)

    def test_all_slaves_finish_before_master(self):
        """
        Regardless of whether all slave instructions finish early, the master
        should always be allowed to run to completion.
        """
        expected_runtime = 0.5
        master = FakeInstruction(blocking_time=expected_runtime)
        slaves = [
            FakeInstruction(),
            FakeInstruction(),
            FakeInstruction()]
        instruction = Parallel(master, *slaves)
        start = timenow()
        instruction.run(MagicMock())
        duration = timenow() - start
        self.assertAlmostEqual(duration, expected_runtime, 1)
        # Double check that all slave.run() methods finished.
        for slave in slaves:
            self.assertTrue(slave.finished)

    def test_master_throws_exception(self):
        """
        If the master instruction raises an exception during its run() method,
        the Parallel should stop all slave instructions.
        Note: For this test, the master instruction throws an exception
        after 0.1seconds, giving enough time for all the slaves to be started.
        """
        raise_after = 0.1
        master = FakeInstruction(blocking_time=raise_after, exception=SillyError())
        slaves = [
            FakeInstruction(blocking_time=10),
            FakeInstruction(blocking_time=10),
            FakeInstruction(blocking_time=10)]
        instruction = Parallel(master, *slaves)
        start = timenow()
        with self.assertRaises(SillyError):
            instruction.run(MagicMock())
        duration = timenow() - start
        self.assertAlmostEqual(duration, raise_after, 1)
        # master raised the exception, ensure other instructions were stopped:
        sleep(0.1) # Time allowed for run() methods to be collected
        for slave in slaves:
            self.assertTrue(slave.stopped)

    def test_slave_throws_exception(self):
        """
        If a slave instruction raises an exception during its run() method, the
        Parallel should stop all insructions (that didn't raise the exception).
        Note: this test sets up a slave which will raise an exception after 0.1
        seconds, giving enough time for all the instructions to be started.
        """
        raise_after = 0.1
        master = FakeInstruction(blocking_time=10)
        slave_a = FakeInstruction(blocking_time=10)
        slave_b = FakeInstruction(blocking_time=10)
        slave_c = FakeInstruction(blocking_time=raise_after, exception=SillyError())
        instruction = Parallel(master, slave_a, slave_b, slave_c)
        start = timenow()
        with self.assertRaises(SillyError):
            instruction.run(MagicMock())
        duration = timenow() - start
        self.assertAlmostEqual(duration, raise_after, 1)
        # slave_c raised the exception, ensure other instructions were stopped:
        sleep(0.1) # Time allowed for run() methods to be collected
        self.assertTrue(slave_a.stopped)
        self.assertTrue(slave_b.stopped)
        self.assertTrue(master.stopped)
