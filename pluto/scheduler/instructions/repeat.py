#pylint:disable=missing-docstring
#pylint:enable=missing-docstring

from threading import Event
from time import time as timenow

from pluto.exceptions.exceptions import LogicError
from pluto.scheduler.instruction import PlutoInstruction, PlutoInstructionRunner
from pluto.scheduler.logger import LOGGER


class RepeatFor(PlutoInstruction):
    """
    Pluto instruction to repeat the given PlutoInstruction a fixed number of
    times, any number of times, within a given timespan or indefinitely.

    Args:
        instruction (PlutoInstruction): The instruction to be repeated.
        stop_after (int): Stop repeating after this number of seconds.
        repeat_every (int): (Optional) Repeat every n seconds.

    Examples:
        .. code-block:: python

            # Repeat immediately, stop repeating after 60 seconds.
            RepeatFor(
                instruction=PlutoInstruction(...),
                stop_after=60
            )

            # Repeat every 10 seconds, stop repeating after 60 seconds.
            RepeatFor(
                instruction=PlutoInstruction(...),
                stop_after=60,
                repeat_every=10
            )
    """

    def __init__(self, instruction, seconds, repeat_every=None):
        self._instruction = instruction
        self._seconds = seconds
        self._repeat_every = repeat_every
        self._stop = None
        self._timer = None
        self._start_time = None

    @property
    def description(self):
        # For example:
        # RepeatFor: repeat every 10s for 60s: Call owlhal1.foo(args=[10])
        return "RepeatFor: repeat {}{}: {}".format(
            f"every {self._repeat_every}s " if self._repeat_every else "",
            f"for {self._seconds}s",
            self._instruction.description)

    @property
    def _elapsed(self):
        return round(timenow() - self._start_time, 2)

    def run(self, eventbus):
        self._stop = Event()
        self._timer = Event()
        self._start_time = timenow()
        while not self._stop.is_set():
            LOGGER.info(
                "RepeatFor[%ss/%ss]: Running: %s...",
                self._elapsed,
                self._seconds,
                self._instruction.description)
            runner = PlutoInstructionRunner(eventbus, self._instruction)
            runner.start()
            if self._repeat_every:
                self._timer.wait(self._repeat_every)
                if not runner.finished:
                    runner.stop()
                    if not self._stop.is_set():
                        raise LogicError(
                            f"{self._instruction.description}: Still running! "
                            f"Unable to repeat every {self._repeat_every}s")
            result = runner.result()
            LOGGER.info(
                "RepatFor: Instruction ##%s## Finished: result=%s",
                self._instruction.description,
                result)
            if not self._stop.is_set():
                if self._elapsed >= self._seconds:
                    self._stop.set()
        LOGGER.info(
            "RepeatTimes: Finished, ran for %ss, %ss]",
            self._elapsed,
            self._seconds)

    def stop(self):
        """
        Stop the RepeatFor instruction
        """
        if self._stop is not None:
            LOGGER.info("RepeatFor: Stopping repeated instruction...")
            self._instruction.stop()
            # Stop the instruction and wait for it to actually stop.
            self._stop.set()
            # If running a "repeat every", cancel the wait timer
            self._timer.set()


class RepeatTimes(PlutoInstruction):
    """
    Pluto instruction to repeat the given PlutoInstruction a fixed number of
    times, any number of times, within a given timespan or indefinitely.

    Args:
        instruction (PlutoInstruction): The instruction to be repeated.
        iterations (int): Total number of times to repeat.
        repeat_every (int): (Optional) Repeat every n seconds.

    Examples:
        .. code-block:: python

            # Repeat immediately, stop repeating after 10 iterations.
            RepeatTimes(
                PlutoInstruction(...),
                iterations=10
            )

            # Repeat every 30 seconds, stop repeating after 10 iterations.
            RepeatTimes(
                PlutoInstruction(...),
                iterations=10,
                repeat_every=30
            )
    """

    #pylint:disable=too-many-instance-attributes
    def __init__(self, instruction, iterations, repeat_every=0):
        self._instruction = instruction
        self._iterations = iterations
        self._counter = 1
        self._repeat_every = repeat_every
        self._stop = None
        self._timer = None

    @property
    def description(self):
        # For example:
        # RepeatTimes: repeat(30iterations, every 10s): Call owlhal1.foo(args=[10])
        return "RepeatTimes: repeat({}iterations{}{}".format(
            self._iterations,
            f", {self._repeat_every}secs): " if self._repeat_every else ": ",
            self._instruction.description)

    @property
    def instruction(self):
        """
        Get the PlutoInstruction which shall be repeated - this is required
        for serialisation so the instruction can be created off target, sent
        to a target device and reconstructed on the target.
        """
        return self._instruction

    def run(self, eventbus):
        """
        Run the RepeatTimes instruction.

        Args:
            eventbus (PlutoEventBus): The evenbus which the instruction can
                use to annonymously interact with registered components.

        Raises:
            Exceptions raised by the PlutoInstruction that is being repeated.
        """
        self._stop = Event()
        self._timer = Event()
        while not self._stop.is_set():
            LOGGER.info(
                "RepeatTimes[%s/%s]: Running: %s...",
                self._counter,
                self._iterations,
                self._instruction.description)
            runner = PlutoInstructionRunner(eventbus, self._instruction)
            runner.start()
            if self._repeat_every:
                self._timer.wait(self._repeat_every)
                if not runner.finished:
                    runner.stop()
                    if not self._stop.is_set():
                        raise LogicError(
                            f"{self._instruction.description}: Still running! "
                            f"Unable to repeat every {self._repeat_every}s")
            result = runner.result()
            LOGGER.info(
                "RepatTimes: Instruction ##%s## Finished: result=%s",
                self._instruction.description,
                result)
            if not self._stop.is_set():
                if self._counter < self._iterations:
                    self._counter += 1
                else:
                    self._stop.set()
        LOGGER.info(
            "RepeatTimes: Finished, completed [%s/%s] iterations",
            self._counter,
            self._iterations)

    def stop(self):
        """
        Stop the RepeatTimes instruction
        """
        if self._stop is not None:
            LOGGER.info("RepeatTimes: Stopping repeated instruction...")
            self._instruction.stop()
            # Stop the instruction and wait for it to actually stop.
            self._stop.set()
            # If running a "repeat every", cancel the wait timer
            self._timer.set()


class RepeatForever(PlutoInstruction):
    """
    Pluto instruction to repeat the given PlutoInstruction a fixed number of
    times, any number of times, within a given timespan or indefinitely.

    Args:
        instruction (PlutoInstruction): The instruction to be repeated.
        repeat_every (int): (Optional) Repeat every n seconds.

    Examples:
        .. code-block:: python

            # Repeat immediately, never stop repeating.
            RepeatForever(
                PlutoInstruction(...),
            )

            # Repeat every 30 seconds, never stop repeating.
            RepeatForever(
                PlutoInstruction(...),
                repeat_every=10,
            )
    """

    def __init__(self, instruction, repeat_every=0):
        self._instruction = instruction
        self._repeat_every = repeat_every
        self._stop = None
        self._timer = None

    @property
    def description(self):
        # For example:
        # RepeatForever: repeat(every 10s): Call owlhal1.foo(args=[10])
        return "RepeatForever: repeat{}{}".format(
            f"(every {self._repeat_every}secs): " \
                if self._repeat_every else ": ",
            self._instruction.description)

    @property
    def instruction(self):
        """
        Get the PlutoInstruction which shall be repeated - this is required
        for serialisation so the instruction can be created off target, sent
        to a target device and reconstructed on the target.
        """
        return self._instruction

    def run(self, eventbus):
        """
        Run the RepeatForever instruction.

        Args:
            eventbus (PlutoEventBus): The evenbus which the instruction can
                use to annonymously interact with registered components.

        Raises:
            Exceptions raised by the PlutoInstruction that is being repeated.
        """
        self._stop = Event()
        self._timer = Event()
        while not self._stop.is_set():
            LOGGER.info(
                "RepatForever: Running: %s...",
                self._instruction.description)
            runner = PlutoInstructionRunner(eventbus, self._instruction)
            runner.start()
            if self._repeat_every:
                self._timer.wait(self._repeat_every)
                if not runner.finished:
                    runner.stop()
                    raise LogicError(
                        f"{self._instruction.description}: Still running! "
                        f"Unable to repeat every {self._repeat_every}s")
            result = runner.result()
            LOGGER.info(
                "RepatForever: Instruction %s Finished: result=%s",
                self._instruction.description,
                result)
        LOGGER.info("RepeatForever: FINISHED")

    def stop(self):
        """
        Stop the RepeatForever instruction
        """
        if self._stop is not None:
            LOGGER.info("RepeatForever: Stopping repeated instruction...")
            self._instruction.stop()
            # Stop the instruction and wait for it to actually stop.
            self._stop.set()
            # If running a "repeat every", cancel the wait timer
            self._timer.set()
