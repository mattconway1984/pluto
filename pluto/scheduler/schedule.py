"""
Contains the PlutoSchedule class which represents a runnable set of instructions
that are logically grouped, and given a name to describe them.
"""

from threading import Event

from pluto.scheduler.instruction import PlutoInstruction
from pluto.scheduler.logger import LOGGER


class PlutoSchedule(PlutoInstruction):
    """
    Represents a set of runnable PlutoInstructions.

    Args:
        description (str): A short one-liner description for the schedule
        instructions (list[PlutoInstruction]): A list of instructions that make
            up the schedule, executed in serial order.
    """
    #pylint: disable=too-few-public-methods

    def __init__(self, description, instructions):
        self._description = description
        self._instructions = instructions
        self._stop = None
        self._index = 0

    @property
    def description(self):
        """
        Get the given name that represents this schedule
        """
        return self._description

    def run(self, eventbus):
        """
        Run each instruction in the schedule.

        Args:
            eventbus (PlutoEventBus): The evenbus which the instruction can
                use to annonymously interact with registered components.
        """
        LOGGER.info("Running schedule: %s", self._description)
        self._stop = Event()
        while self._run_next(eventbus) and not self._stop.is_set():
            continue
        self._stop = None
        self._index = 0
        LOGGER.info("Finished running schedule: %s", self._description)

    def stop(self):
        """
        Stop exection of the schedule.
        """
        if self._stop is not None:
            LOGGER.info(
                "Stopping schedule[%s], index[%s]",
                self._description,
                self._index)
            self._stop.set()
            instruction = self._instructions[self._index]
            instruction.stop()

    def _run_next(self, eventbus):
        result = True
        instruction = self._instructions[self._index]
        instruction.run(eventbus)
        self._index += 1
        if self._index >= len(self._instructions):
            result = False
        return result
