#pylint:disable=missing-docstring
#pylint:enable=missing-docstring

from threading import Event
from logging import INFO as log_level_info
from logging import getLogger

from pluto.application.config import PlutoApplicationConfig
from pluto.event.event import StopEvent, GetComponentEvent, VariableUpdateEvent
from pluto.eventbus.eventbus import PlutoEventBus
from pluto.logger.configure import configure_logger
from pluto.scheduler.scheduler import PlutoScheduler


DEFAULT_LOG_THRESHOLD = log_level_info
LOGGER = getLogger("APP")
SCHEDULER_NAME = "scheduler"


class PlutoApplication:
    """
    Represents a Pluto application
    """
    #pylint: disable=too-few-public-methods

    def __init__(self, config: PlutoApplicationConfig):
        if not isinstance(config, PlutoApplicationConfig):
            raise RuntimeError(
                f"{config} is not an instance of PlutoApplicationConfig")
        configure_logger(config.log_level)
        self._eventbus = PlutoEventBus()
        self._eventbus.register(self)
        self._stop_running = Event()
        self._components = {}
        self._components[SCHEDULER_NAME] = \
            PlutoScheduler(SCHEDULER_NAME, self._eventbus)
        for comp in config.components:
            args = (comp.name, self._eventbus) + comp.args
            self._components[comp.name] = \
                comp.object_class(*args, **comp.kwargs)

    @PlutoEventBus.event_handler(GetComponentEvent)
    def handle_get_component_event(self, event):
        """
        Handle when a GetComponentEvent is posted to the PlutoEventBus

        :note: If the requested component does not exist, the callback shall
            be called with a NoneType object, it's up to the handler to deal
            with any resulting errors
        """
        event.callback(self._components.get(event.component))
        return True

    @PlutoEventBus.event_handler(VariableUpdateEvent)
    def handle_variable_update_event(self, event):
        """
        FIX: Remove this handler, it's just a handler for now
        """
        if self:
            pass
        LOGGER.info("%s.%s=%s", event.component, event.variable, event.value)
        return True

    @PlutoEventBus.event_handler(StopEvent)
    def handle_stop_event(self, _):
        """
        Handle when a StopEvent is posted to the EventBus
        """
        self._stop_running.set()
        return True

    def run(self):
        """
        Run the application.

        Blocks until a StopEvent has been posted to the EventBus
        """
        LOGGER.info("Application Started")
        try:
            self._stop_running.wait()
        except KeyboardInterrupt:
            LOGGER.info("Stopping Application...")
        finally:
            for component_name, component in self._components.items():
                LOGGER.debug("Stopping component[%s]...", component_name)
                component.stop()
        LOGGER.info("Application Stopped")
