#pylint:disable=missing-docstring
#pylint:enable=missing-docstring

from functools import wraps
from concurrent.futures import as_completed as futures_as_completed
from concurrent.futures import wait as futures_wait
from concurrent.futures import ThreadPoolExecutor
from logging import getLogger

from pluto.event.event import PlutoEvent, PlutoRecEvent


LOGGER = getLogger("EventBus")


class PlutoEventBus:
    """
    An EventBus for Pluto components to communicate with one another
    """

    @staticmethod
    def event_handler(event_class):
        """
        Decorates a class method so that the event bus handler is automatically
        registered with the PlutoEventBus. Negates the requirement for a
        PlutoComponent to have to individually register every PlutoEvent handler
        through calling:

        PlutoEventBus.register_handler(self.event_handler, PlutoEvent.__class__)
        """
        def deco(event_handler):
            @wraps(event_handler)
            def inner(*args, **kwargs):
                return event_handler(*args, **kwargs)
            inner.eventbus_pluto_event_class = event_class
            return inner
        return deco

    def __init__(self):
        self._handlers = {}
        self._active_futures = []

    def register(self, instance):
        """
        Register a PlutoComponent with the PlutoEventBus, this API will inspect
        the class for any methods decorated with @PlutoEventBus.Handler,
        automatically registering those methods with the PlutoEventBus.
        """
        for key in dir(instance):
            attr = getattr(instance, key)
            if hasattr(attr, "eventbus_pluto_event_class"):
                self.register_handler(attr.eventbus_pluto_event_class, attr)

    def register_handler(self, cls, handler):
        """
        Registers an event handler.

        param: cls: The type of object that the function handles.
        param: handler: A function that will be called whenever an object of
            type `cls` is published.
        """
        if cls in self._handlers:
            self._handlers[cls].append(handler)
        else:
            self._handlers[cls] = [handler]

    def deregister_handler(self, cls, handler):
        """
        Deregisters an event handler.

        :param: cls: The type of object that the function handles.
        :param: handler: A function previously added as a handler for the given
            class that is to be removed.
        """
        if cls in self._handlers and handler in self._handlers[cls]:
            self._handlers[cls].remove(handler)
        else:
            raise Exception("Handler was not registered")

    def post(self, event: PlutoEvent, wait=False):
        """
        Post a PlutoEvent onto the PlutoEventBus.

        This method gets all registered handlers for `cls(obj)`, and submits a
        call to `handler(obj)` to the executor.

        :param event (PlutoEvent): The event instance to post
        :param wait (bool): If True, waits for all handlers to handle the event

        Returns:
            list(concurrent.futures.Future):
                The list of Futures that represent the asynchronous calls to
                the handlers that received the object
        """

        def event_handler_completed(future):
            """
            Handle when a future completes, remove it from the list of active
            futures. The reason for this is to ensure the PlutoEventBus can only
            be destroyed once all active handlers have completed handling an
            event.
            """
            nonlocal self
            if future in self._active_futures:
                self._active_futures.remove(future)

        if not isinstance(event, PlutoEvent):
            raise Exception(
                "Cannot post object of type %s to PlutoEventBus"%(type(event)))
        handlers = self._handlers.get(type(event), []).copy()
        if isinstance(event, PlutoRecEvent):
            handlers += self._handlers.get(PlutoRecEvent, [])
        futures = []
        if not handlers:
            LOGGER.warning("POST %s [No registered handlers]", event)
        else:
            with ThreadPoolExecutor(max_workers=10) as executor:
                for handler in handlers:
                    future = executor.submit(handler, event)
                    futures.append(future)
                    self._active_futures.append(future)
                    future.add_done_callback(event_handler_completed)
                if wait:
                    for fut in futures_as_completed(futures):
                        # Raise exceptions (if raised by the handler)
                        fut.result()
        return futures

    def stop(self):
        """
        Stop the EventBus
        """
        futures_wait(self._active_futures)
