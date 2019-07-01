#pylint:disable=missing-docstring
#pylint:enable=missing-docstring

from concurrent.futures import ThreadPoolExecutor
from threading import Event

from pluto.scheduler.instruction import PlutoInstruction
from pluto.scheduler.logger import LOGGER


class Parallel(PlutoInstruction):
    """
    Pluto instruction to run multiple PlutoInstructions simultaneously (i.e. in
    parallel).

    Args:
        master (PlutoInstruction):
            When the master instruction completes, all @others shall be stopped.
        *others ([PlutoInstruction]):
            Other PlutoInstructions that will be executed in parallel.

    Example
        .. code-block::python

            # The following snippet is equivalent to:
            #   Wait for 60 seconds and Repeatedly run a Call instruction.
            #   Once 60 seconds has elapsed, the RepeatForever shall be
            #   stopped.
            Parallel(WaitSeconds(60), [RepeatForever(Call(...))])
    """
    #pylint:disable=too-many-instance-attributes

    def __init__(self, master, *slaves):
        self._master = master
        self._slaves = list(slaves)
        self._stop = None
        self._finished = None
        self._master_future = None
        self._slave_futures = None
        self._result = None
        self._exception = None

    @property
    def description(self):
        return "Parallel: master={} slaves={}".format(
            self._master.description,
            [comp.description for comp in self._slaves])

    def run(self, eventbus):
        """
        Run the Parallel instruction.

        Args:
            eventbus (PlutoEventBus): The evenbus which the instruction can
                use to annonymously interact with registered components.

        Raises:
            Exceptions if the component encountered an error when setting the
            requested variables.

        Returns:
            The result of the master instruction
        """
        LOGGER.info(
            "Parallel: Running master=%s, slaves=%s",
            self._master.description,
            [comp.description for comp in self._slaves])
        self._finished = Event()
        self._stop = Event()
        self._slave_futures = {}
        executor = ThreadPoolExecutor()
        self._master_future = executor.submit(self._master.run, eventbus)
        self._master_future.add_done_callback(self._handle_done)
        for slave in self._slaves:
            future = executor.submit(slave.run, eventbus)
            self._slave_futures[future] = slave
            future.add_done_callback(self._handle_done)
        self._finished.wait()
        if self._exception:
            raise self._exception
        LOGGER.info("Parallel: Finished, master result=%s", self._result)
        return self._result

    def _handle_done(self, future):
        if future == self._master_future:
            self._master_future = None
            self._stop_running()
            try:
                self._result = future.result()
            except Exception as error: #pylint:disable=broad-except
                self._exception = error
        else:
            slave = self._slave_futures[future]
            del self._slave_futures[future]
            try:
                result = future.result()
                LOGGER.info(
                    "Parallel: Slave ##%s## finished, result=%s",
                    slave.description,
                    result)
            except Exception as error: #pylint:disable=broad-except
                self._exception = error
                self._stop_running()
        # Once all instructions have finished, unblock Parallel.run()
        if not (self._master_future or self._slave_futures):
            self._finished.set()

    def _stop_running(self):
        if self._master_future:
            self._master.stop()
        for slave in self._slave_futures.values():
            slave.stop()

    def stop(self):
        """
        Stop the WaitSeconds instruction
        """
        if self._master_future:
            self._master.stop()
