#pylint:disable=missing-docstring
#pylint:enable=missing-docstring


from abc import ABC, abstractmethod, abstractproperty
from concurrent.futures import ThreadPoolExecutor
from threading import Event

from pluto.exceptions.exceptions import LogicError


class PlutoInstructionRunner:
    """
    Run a Pluto instruction inside it's own thread. This provides simple,
    non-blocking APIs to easily run PlutoInstruction objects.

    Args:
        eventbus (PlutoEventBus): The active eventbus to use when running the
            instruction.
        instruction (PlutoInstruction): The instruction instance to run.
    """

    def __init__(self, eventbus, instruction):
        self._eventbus = eventbus
        self._instruction = instruction
        self._future = None
        self._result = None
        self._started = Event()
        self._finished = Event()

    @property
    def finished(self):
        """
        True if the instruction has finished executing.
        """
        return self._finished.is_set()

    def start(self):
        """
        Start running the instruction, this shall run the instruction in it's
        own thread and will return immediately (i.e. it's non-blocking). If a
        callback was registered when the PlutoInstructionRunner was created,
        this callback will be invoked once the instruction has finished.
        """
        if self._started.is_set():
            raise LogicError(f"Already started: {self._instruction.description}")
        self._started.set()
        executor = ThreadPoolExecutor()
        self._future = executor.submit(self._instruction.run, self._eventbus)
        self._future.add_done_callback(self._handle_done)

    def stop(self):
        """
        Stop running the instruction, this API will block until the instruction
        has actually stopped running.

        Returns:
            The result from the instructions run() method (even though it was
            stopped early).
        """
        self._instruction.stop()
        return self.result()

    def wait(self, timeout=None):
        """
        Wait for the instruction to finish running. If the instruction is still
        running, this API will block until the instruction has finished,
        otherwise it shall return immediately.

        Args:
            timeout (int): Give up waiting after this number of seconds.
        """
        if not self._started.is_set():
            raise LogicError("Instruction was not started")
        if timeout:
            self._finished.wait(timeout=timeout)
        else:
            self._finished.wait()

    def result(self):
        """
        Reap the result from the PlutoInstruction objects run() method. If the
        instruction has not yet finished, this API will block until the
        instruction has finished so it's result can be reaped.

        Raises:
            An Exception if the instruction raised an exception whilst it ran
            in a background thread.
        """
        self.wait()
        try:
            raise self._result
        except TypeError:
            pass
        return self._result

    def reset(self):
        """
        Reset the instruction runner so it can re-run the instruction.
        """
        if self._started.is_set() and not self._finished.is_set():
            raise LogicError("Cannot reset whilst running")
        self._future = None
        self._result = None
        self._started = Event()
        self._finished = Event()

    def _handle_done(self, future):
        if future != self._future:
            raise LogicError("Programming error!")
        try:
            self._result = self._future.result()
        except Exception as error: #pylint:disable=broad-except
            self._result = error
        self._future = None
        self._finished.set()


class PlutoInstruction(ABC):
    """
    Base class for Pluto instructions
    """
    #pylint: disable=too-few-public-methods

    @abstractproperty
    def description(self):
        """
        (str): A human readable description to describe the PlutoInstruction.
        """
        return

    @abstractmethod
    def run(self, eventbus):
        """
        An implementation to run the instruction.

        This method will be called by the PlutoScheuler to run an instruction.

        Args:
            eventbus (PlutoEventBus): The evenbus which the instruction can
                use to annonymously interact with registered components.
        """
        return

    @abstractmethod
    def stop(self):
        """
        An implementation to stop the instruction.

        This method will be called by the PlutoScheduler to stop execution of
        the instruction.
        """
        return
