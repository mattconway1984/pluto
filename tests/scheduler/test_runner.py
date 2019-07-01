"""
Unit tests for the PlutoInstructionRunner
"""
#pylint:disable=missing-docstring
#pylint: disable=no-self-use

from time import sleep
from time import time as timenow
from threading import Event
from unittest import TestCase
from unittest.mock import MagicMock

from pluto.scheduler.instruction import PlutoInstructionRunner
from pluto.exceptions.exceptions import LogicError


class TestInstructionRunner(TestCase):
    """
    Test suite to test the PlutoInstructionRunner
    """

    def test_stop_before_started(self):
        runner = PlutoInstructionRunner(MagicMock(), MagicMock())
        with self.assertRaises(LogicError):
            runner.stop()

    def test_wait_before_started(self):
        runner = PlutoInstructionRunner(MagicMock(), MagicMock())
        with self.assertRaises(LogicError):
            runner.wait()

    def test_result_before_started(self):
        runner = PlutoInstructionRunner(MagicMock(), MagicMock())
        with self.assertRaises(LogicError):
            runner.result()

    def test_finished_before_started(self):
        runner = PlutoInstructionRunner(MagicMock(), MagicMock())
        self.assertFalse(runner.finished)

    def test_start_runner(self):
        """
        A simple instruction which does not block and returns immediatley
        """
        instruction = MagicMock()
        runner = PlutoInstructionRunner(MagicMock, instruction)
        runner.start()
        # The MagicMock.run() method will just return immediately, so the
        # runner should have finished.
        self.assertTrue(runner.finished)

    def test_stop_runner_after_start(self):
        """
        Once the runner starts an instruction, it should also be able to
        stop it.
        """
        expected_result = "a fake result"
        unblock = Event()
        def fake_run(_):
            unblock.wait()
            return expected_result
        def fake_stop():
            unblock.set()
        instruction = MagicMock()
        instruction.run = fake_run
        instruction.stop = fake_stop
        runner = PlutoInstructionRunner(MagicMock, instruction)
        runner.start()
        # Allow enough time for the fake_run method to be invoked by the runner
        sleep(0.1)
        # The run method is currently blocked, so runner can't be finished...
        self.assertFalse(runner.finished)
        # Now stop the runner, which should tell the instruction to stop, in
        # this case, calling fake_stop() which unblocks the fake_run()
        runner.stop()
        # Allow time for the runner to reap the result from the instruction
        sleep(0.1)
        # Verify the runner finished, and that the runner reaped the correct
        # result
        self.assertTrue(runner.finished)
        self.assertEqual(runner.result(), expected_result)

    def test_runnable_raises_exception(self):
        """
        This tests when a run method raises an exception, it can be reaped
        by the runner and the exception re-raised in the context of the callers
        thread.
        """
        def fake_run(_):
            raise Exception()
        instruction = MagicMock()
        instruction.run = fake_run
        runner = PlutoInstructionRunner(MagicMock, instruction)
        runner.start()
        with self.assertRaises(Exception):
            runner.result()

    def test_wait_after_start(self):
        """
        Once the runner starts an instruction, the caller can go away and do
        some more stuff before going back to the runner and waiting for the
        instruction to complete.
        """
        fake_run_time = 0.25
        expected_result = "a fake result"
        def fake_run(_):
            # Block for a defined amount of time before returning
            sleep(fake_run_time)
            return expected_result
        instruction = MagicMock()
        instruction.run = fake_run
        runner = PlutoInstructionRunner(MagicMock, instruction)
        start = timenow()
        runner.start()
        # Allow enough time for the fake_run method to be invoked by the runner
        sleep(0.1)
        # The run method is currently blocked, so runner can't be finished...
        self.assertFalse(runner.finished)
        # Make the runner wait (blocking call) for the instruction to finsh...
        runner.wait()
        # Once the runner has waited, ensure the actual run time matches:
        duration = timenow() - start
        self.assertTrue(runner.finished)
        self.assertEqual(runner.result(), expected_result)
        self.assertEqual(round(duration, 2), fake_run_time)
