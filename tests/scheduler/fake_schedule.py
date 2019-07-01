"""
Contains a simple class to represent a PlutoInstruction, used for testing
the Pluto instructions.
"""

from threading import Event

from pluto.scheduler.schedule import PlutoSchedule

class FakeSchedule(PlutoSchedule):
    """
    A fake PlutoInstruction which is used for unit tests.

    Note: this instruction is not serialisable because it contains an Event
    """

    def __init__(self, description, blocking_time=0, exception=None):
        #pylint:disable=super-init-not-called
        #super.__init__(name, description)
        self._blocking_time = blocking_time
        self._exception = exception
        self._eventbus = None
        self._run_count = 0
        self._stop = Event()
        self._finished = Event()

    @property
    def description(self):
        return "A fake instruction"

    @property
    def stopped(self):
        """
        Find out if the instruction was stopped
        """
        return self._stop.is_set()

    @property
    def finished(self):
        """
        Find out if the instruction was finished (i.e. ran to completion)
        """
        return self._finished.is_set()

    def run(self, eventbus):
        self._run_count += 1
        if self._blocking_time:
            self._stop.wait(timeout=self._blocking_time)
        if self._exception:
            raise self._exception
        self._finished.set()

    def stop(self):
        self._stop.set()

    @property
    def eventbus(self):
        """
        Grab the PlutoEventBus instance passed to the FakeInstruction
        """
        return self._eventbus

    @property
    def run_count(self):
        """
        Grab the number of times the fake instruction was run
        """
        return self._run_count
