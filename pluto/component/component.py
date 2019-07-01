#pylint:disable=missing-docstring
#pylint:enable=missing-docstring


from abc import ABC, abstractmethod
from threading import Lock

from pluto.eventbus.eventbus import PlutoEventBus
from pluto.event.event import VariableUpdateEvent


class PlutoComponent(ABC):
    """
    Base class for Pluto Components
    """

    _components_guard = Lock()
    _components = []

    def __init__(self, name, eventbus):
        self._name = name
        self._eventbus = eventbus
        with PlutoComponent._components_guard:
            if self.name in PlutoComponent._components:
                raise RuntimeError(
                    f"A Component already exists with name {self.name}")
            PlutoComponent._components.append(self.name)
        eventbus.register(self)

    @property
    def name(self) -> str:
        """
        Retrieve the components name
        """
        return self._name

    @property
    def eventbus(self) -> PlutoEventBus:
        """
        Get the PlutoEventBus object which can be used by the component to
        post events to and listen for posted events
        """
        return self._eventbus

    @abstractmethod
    def stop(self):
        """
        Stop the component
        """
        return

    @property
    def _public_attrs(self):
        """
        Private property to get all the public attributes for the Component
        """
        o_attrs = [attr for attr in dir(self) if not attr.startswith("_")]
        c_attrs = [attr for attr in dir(type(self)) if not attr.startswith("_")]
        return o_attrs + c_attrs

    #pylint: disable=no-self-argument
    def _call_variable_update(func):
        """
        Wrapper to send a notification when a components variable has been
        written to, only sends update notifications for public variables

        @Note: This decorator is only intented to wrap __setattr__ APIs
        """
        def wrapper(*args):
            self, attr, value = args
            #pylint: disable=not-callable
            if func(self, attr, value) and not attr.startswith("_"):
                self.eventbus.post(event=VariableUpdateEvent(self.name, attr, value))
        return wrapper

    @_call_variable_update
    def __setattr__(self, attr, value):
        """
        Sets a "Component" attribute:
            1. Only send a VARIABLE_UPDATE msg for existing attributes
            2. The attribute could be a descriptor, so try manually invoking
               the descriptor protocols __set__() to set the value. If that
               fails, let super() deal with the setattr
        """
        post_update = True
        got_attr = None
        try:
            got_attr = super().__getattribute__(attr)
        except AttributeError:
            post_update = False
        try:
            got_attr.__set__(self, value)
        except AttributeError:
            super().__setattr__(attr, value)
        return post_update

    def __getattribute__(self, attr):
        """
        Gets a "Component" attribute:
            1. Always ask super() to get the value of the attribute
            2. The attribute could be a descirptor, so try manually invoking
               the descriptor protocols __get__() to get the attributes value.
               If that fails, just return the value returned from super()
        """
        got_attr = super().__getattribute__(attr)
        try:
            return got_attr.__get__(self, type(self))
        except AttributeError:
            return got_attr
