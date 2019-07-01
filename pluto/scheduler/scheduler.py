"""
Contains the PlutoScheduler class.
"""

from concurrent.futures import ThreadPoolExecutor
from threading import Event

from pluto.exceptions.exceptions import LogicError
from pluto.component.component import PlutoComponent
from pluto.scheduler.logger import LOGGER
from pluto.scheduler.schedule import PlutoSchedule


class PlutoScheduler(PlutoComponent):
    """
    The PlutoScheduler runs PlutoSchedule objects.

    PlutoSchedule objects are loaded into the PlutoScheduler, the
    PlutoScheduler is responsible for managing execution of the loaded
    PlutoSchedule objects.

    Args:
        name (str): The given name for the PlutoScheduler component
        eventbus (PlutoEventBus): The eventbus.
    """

    def __init__(self, name, eventbus):
        LOGGER.info("Starting PlutoScheduler...")
        self._schedules = []
        self._stopped = Event()
        self._started = Event()
        self._finished = Event()
        self._index = 0
        self._future = None
        super().__init__(name, eventbus)

    def load(self, schedule):
        """
        Load a schedule into the Scheuler.

        If this API is called repeatededly, the order of the schedules is
        important as the schedule will be appended.

        Args:
            schedule (PlutoSchedule): The schedule to load

        Returns:
            (bool) True if the schedule was loaded
        """
        result = True
        if not isinstance(schedule, PlutoSchedule):
            raise Exception(
                f"Cannot load a schedule of type {type(schedule)}")
        self._schedules.append(schedule)
        return result

    def run(self):
        """
        Run all steps of the loaded schedule.

        Invoking this API will cause the scheduler to start executing ALL steps
        of the loaded schedule(s), always starting at the first step.
        """
        if self._started.is_set():
            raise LogicError("Cannot run the Scheduler whilst already running")
        executor = ThreadPoolExecutor()
        self._future = executor.submit(self._run)
        self._future.add_done_callback(self._handle_finished)
        self._started.set()

    def stop(self):
        """
        Stop running the schedule
        """
        schedule = self._schedules[self._index]
        schedule.stop()
        self._stopped.set()
        self._started.clear()

    def wait(self, timeout=0):
        """
        Wait for the scheduler to finish running all loaded schedules

        Args:
            timeout (int): Number of seconds to wait before giving up.
        """
        if timeout:
            self._finished.wait(timeout=timeout)
        else:
            self._finished.wait()

    def reset(self):
        """
        Reset clears the added schedules.
        """
        if not self._started.is_set():
            raise LogicError("Cannot reset scheduler whilst running a schedule")
        LOGGER.info("Reset PlutoScheduler")
        self._schedules = []
        self._stopped.clear()
        self._finished.clear()

    def _run(self):
        LOGGER.info("Running all steps of loaded schedule(s)...")
        self._index = 0
        while self._run_next():
            continue

    def _run_next(self):
        """
        Execute the ONLY the next step (of the loaded schedule).
        """
        result = False
        if not self._stopped.is_set():
            schedule = self._schedules[self._index]
            schedule.run(self._eventbus)
            self._index += 1
            if self._index < len(self._schedules):
                result = True
        return result

    def _handle_finished(self, future):
        if future != self._future:
            raise LogicError("Programming Error!")
        LOGGER.info("Finished running loaded schedules")
        self._started.clear()
        self._stopped.clear()
        self._finished.set()
