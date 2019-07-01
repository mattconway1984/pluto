"""
Unit tests for the Repeat instruction
"""
#pylint:disable=missing-docstring
#pylint: disable=no-self-use

from unittest import TestCase
from unittest.mock import MagicMock
from time import sleep
from time import time as timenow

from fake_instruction import FakeInstruction, SillyError

from pluto.exceptions.exceptions import LogicError
from pluto.scheduler.instruction import PlutoInstructionRunner
from pluto.scheduler.instructions.repeat import (
    RepeatForever,
    RepeatTimes,
    RepeatFor)


class TestRepeatForeverInstruction(TestCase):
    """
    Test suite to test the RepeatForever instruction
    """

    def test_repeat_forever_repeated_instruction_raises_error(self):
        """
        When the repeated instructions run method raises an error, the
        run method of the repeat instruction must not squash that error.
        """
        fake_instruction = FakeInstruction(exception=SillyError())
        instruction = RepeatForever(fake_instruction)
        with self.assertRaises(SillyError):
            instruction.run(MagicMock())
        self.assertEqual(fake_instruction.run_count, 1)

    def test_repeat_forever_every_time_is_too_short(self):
        """
        When the repeated instructions run method takes a longer time to
        execute than the @repeat_every argument passed to the repeat
        instruction, an error is expected
        """
        repeat_every = 0.1
        fake_instruction = FakeInstruction(blocking_time=0.5)
        instruction = RepeatForever(fake_instruction, repeat_every=repeat_every)
        with self.assertRaises(LogicError):
            instruction.run(MagicMock)

    def test_repeat_forever_then_stop(self):
        """
        RepeatForever can only be stopped by calling the stop() method of the
        instruction. This tests that the instruction is repeated as expected
        until the stop() method is called (number of repeats is unimportant).
        """
        stop_after = 0.1
        min_expected_repeats = 10
        fake_instruction = FakeInstruction()
        instruction = RepeatForever(fake_instruction)
        runner = PlutoInstructionRunner(MagicMock(), instruction)
        runner.start()
        sleep(stop_after)
        runner.stop()
        self.assertGreater(fake_instruction.run_count, min_expected_repeats)

    def test_repeat_forever_every_tenth_of_a_second(self):
        """
        RepeatForever has a @repeat_every argument, which specifies how
        frequently the repeated instruction should be repeated. Therefore,
        when a RepeatForever is run for 1 second, repeating every 0.1 seconds,
        the repeated instruction should be executed exactly 10 times.
        """
        repeat_every = 0.1
        repeat_for = 1
        expected_repeats = 10
        fake_instruction = FakeInstruction()
        instruction = RepeatForever(fake_instruction, repeat_every=repeat_every)
        runner = PlutoInstructionRunner(MagicMock(), instruction)
        runner.start()
        sleep(repeat_for)
        runner.stop()
        self.assertEqual(fake_instruction.run_count, expected_repeats)

    def test_forever_times_stop_whilst_waiting_for_every_timer(self):
        """
        When RepeatForever is repeating an instruction every n seconds, there
        should be a period of grace when the instruction has finished executing
        and the RepeatForever is waiting to repeat again. In this instance, if
        the stop() API of the RepeatForever instruction is invoked, the
        instruction should tear down almost immediately.
        """
        repeat_every = 5
        expected_duration = 0.25
        fake_instruction = FakeInstruction()
        instruction = RepeatForever(fake_instruction, repeat_every=repeat_every)
        runner = PlutoInstructionRunner(MagicMock(), instruction)
        start = timenow()
        runner.start()
        sleep(expected_duration)
        runner.stop()
        duration = timenow() - start
        self.assertAlmostEqual(duration, expected_duration, 1)


class TestRepeatTimesInstruction(TestCase):
    """
    Test suite to test the RepeatTimes instruction
    """

    def test_repeat_times_repeated_instruction_raises_error(self):
        """
        When the repeated instructions run method raises an error, the
        run method of the repeat instruction must not squash that error.
        """
        instruction = RepeatTimes(FakeInstruction(exception=SillyError()), 10)
        with self.assertRaises(SillyError):
            instruction.run(MagicMock())

    def test_repeat_times_every_time_is_too_short(self):
        """
        When the repeated instructions run method takes a longer time to
        execute than the @repeat_every argument passed to the repeat
        instruction, an error is expected
        """
        repeat_every = 0.1
        fake_instruction = FakeInstruction(blocking_time=0.5)
        instruction = RepeatTimes(fake_instruction, 10, repeat_every)
        with self.assertRaises(LogicError):
            instruction.run(MagicMock)

    def test_repeat_times_stop_early(self):
        """
        RepeatTimes can be stopped by calling the stop() method of the
        instruction. This tests that the instruction is repeated as expected
        until the stop() method is called (number of repeats is unimportant).
        """
        stop_after = 0.1
        requested_iterations = 99999999
        min_expected_repeats = 10
        fake_instruction = FakeInstruction()
        instruction = RepeatTimes(fake_instruction, requested_iterations)
        runner = PlutoInstructionRunner(MagicMock(), instruction)
        runner.start()
        sleep(stop_after)
        runner.stop()
        self.assertGreater(fake_instruction.run_count, min_expected_repeats)

    def test_repeat_ten_times(self):
        """
        RepeatTimes has a @iterations argument, which specifies how
        many repeat iterations to perform. This ensures the correct number
        of iterations are completed.
        """
        requested_iterations = 10
        fake_instruction = FakeInstruction()
        instruction = RepeatTimes(fake_instruction, requested_iterations)
        runner = PlutoInstructionRunner(MagicMock(), instruction)
        runner.start()
        runner.wait()
        self.assertEqual(fake_instruction.run_count, requested_iterations)

    def test_repeat_ten_times_every_tenth_of_a_second(self):
        """
        RepeatTimes has a @repeat_every argument, which specifies how
        frequently the repeated instruction should be repeated. Therefore,
        when a RepeatTimes is run for 1 second, repeating every 0.1 seconds,
        the repeated instruction should be executed exactly 10 times.
        """
        repeat_every = 0.1
        requested_iterations = 10
        expected_duration = 1
        fake_instruction = FakeInstruction()
        instruction = RepeatTimes(fake_instruction, requested_iterations, repeat_every=repeat_every)
        runner = PlutoInstructionRunner(MagicMock(), instruction)
        start = timenow()
        runner.start()
        runner.wait()
        duration = timenow() - start
        self.assertEqual(fake_instruction.run_count, requested_iterations)
        self.assertEqual(int(duration), expected_duration)

    def test_repeat_times_stop_whilst_waiting_for_every_timer(self):
        """
        When RepeatTimes is repeating an instruction every n seconds, there
        should be a period of grace when the instruction has finished executing
        and the RepeatTimes is waiting to repeat again. In this instance, if
        the stop() API of the RepeatForever instruction is invoked, the
        instruction should tear down almost immediately.
        """
        requested_iterations = 10
        repeat_every = 5
        expected_duration = 0.25
        fake_instruction = FakeInstruction()
        instruction = RepeatTimes(fake_instruction, requested_iterations, repeat_every=repeat_every)
        runner = PlutoInstructionRunner(MagicMock(), instruction)
        start = timenow()
        runner.start()
        sleep(expected_duration)
        runner.stop()
        duration = timenow() - start
        self.assertAlmostEqual(duration, expected_duration, 1)


class TestRepeatForr(TestCase):
    """
    Test suite to test the RepeatFor instruction
    """

    def test_repeat_forever_repeated_instruction_raises_error(self):
        """
        When the repeated instructions run method raises an error, the
        run method of the repeat instruction must not squash that error.
        """
        instruction = RepeatFor(FakeInstruction(exception=SillyError()), 10)
        with self.assertRaises(SillyError):
            instruction.run(MagicMock())

    def test_repeat_for_every_time_is_too_short(self):
        """
        When the repeated instructions run method takes a longer time to
        execute than the @repeat_every argument passed to the repeat
        instruction, an error is expected
        """
        repeat_every = 0.1
        fake_instruction = FakeInstruction(blocking_time=0.5)
        instruction = RepeatFor(fake_instruction, 10, repeat_every)
        with self.assertRaises(LogicError):
            instruction.run(MagicMock)

    def test_repeat_for_stop_early(self):
        """
        RepeatFor can be stopped by calling the stop() method of the
        instruction. This tests that the instruction is repeated as expected
        until the stop() method is called (number of repeats is unimportant).
        """
        stop_after = 0.1
        requested_seconds = 100
        min_expected_repeats = 10
        fake_instruction = FakeInstruction()
        instruction = RepeatFor(fake_instruction, requested_seconds)
        runner = PlutoInstructionRunner(MagicMock(), instruction)
        runner.start()
        sleep(stop_after)
        runner.stop()
        self.assertGreater(fake_instruction.run_count, min_expected_repeats)

    def test_repeat_one_second(self):
        """
        RepeatFor has a @seconds argument, which specifies how long to run
        the repeat for. This ensures the instruction was repeated for the
        requested seconds.
        """
        requested_seconds = 0.10
        fake_instruction = FakeInstruction()
        instruction = RepeatFor(fake_instruction, requested_seconds)
        runner = PlutoInstructionRunner(MagicMock(), instruction)
        start = timenow()
        runner.start()
        runner.wait()
        duration = timenow() - start
        self.assertEqual(round(duration, 1), round(requested_seconds, 1))

    def test_repeat_for_half_a_second_every_tenth_of_a_second(self):
        """
        RepeatFor has a @repeat_every argument, which specifies how
        frequently the repeated instruction should be repeated. Therefore,
        when a RepeatFor is run for 0.5 seconds, repeating every 0.1 seconds,
        the repeated instruction should be executed exactly 5 times.
        """
        repeat_every = 0.1
        requested_seconds = 0.50
        expected_repeats = 5
        fake_instruction = FakeInstruction()
        instruction = RepeatFor(fake_instruction, requested_seconds, repeat_every=repeat_every)
        runner = PlutoInstructionRunner(MagicMock(), instruction)
        runner.start()
        runner.wait()
        self.assertEqual(fake_instruction.run_count, expected_repeats)

    def test_repeat_for_stop_whilst_waiting_for_every_timer(self):
        """
        When RepeatFor is repeating an instruction every n seconds, there
        should be a period of grace when the instruction has finished executing
        and the RepeatTimes is waiting to repeat again. In this instance, if
        the stop() API of the RepeatFor instruction is invoked, the
        instruction should tear down almost immediately.
        """
        requested_seconds = 10
        repeat_every = 5
        expected_duration = 0.25
        fake_instruction = FakeInstruction()
        instruction = RepeatFor(fake_instruction, requested_seconds, repeat_every=repeat_every)
        runner = PlutoInstructionRunner(MagicMock(), instruction)
        start = timenow()
        runner.start()
        sleep(expected_duration)
        runner.stop()
        duration = timenow() - start
        self.assertAlmostEqual(duration, expected_duration, 1)
