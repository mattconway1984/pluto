"""
Contains a simple class to represent a Pluto component, used for testing
the Pluto instructions.
"""

from time import sleep


class MyCustomRuntimeError(RuntimeError):
    """
    A custom runtime error
    """


class FakeComponent:
    """
    A class representing a fake PlutoComponent
    """

    #pylint:disable=blacklisted-name
    #pylint:disable=no-self-use
    def __init__(self, name):
        self._name = name
        self._foo = 0
        self._bar = 0
        self._baz = 0
        self._long_a = 0
        self._long_b = 0

    def bang_bang(self):
        """
        A method that goes bang
        """
        raise MyCustomRuntimeError("BANG! A forced exception")

    def simple_method(self):
        """
        A method with no args and no return
        """
        print("Such a simpleton")

    def complex_method(self, foo, bar):
        """
        A method with some args
        """
        print(f"called with bar={bar} foo={foo}")
        return "silly return"

    @property
    def name(self) -> str:
        """
        Get the name of the component
        """
        return self._name

    @property
    def foo(self):
        """
        Get the value held by foo (foo is read only)
        """
        return self._foo

    @property
    def bar(self):
        """
        Get the value held by bar (bar is read-write)
        """
        return self._bar

    @bar.setter
    def bar(self, value):
        """
        Set the value held by bar
        """
        self._bar = value

    @property
    def baz(self):
        """
        Get the value held by baz (baz is read-write)
        """
        return self._baz

    @baz.setter
    def baz(self, value):
        """
        Set the value held by baz
        """
        self._baz = value

    @property
    def bang(self):
        """
        An attribute that causes an exception when it's value is attempted
        to be set or retrieved.
        """
        raise MyCustomRuntimeError("BANG! A forced exception")

    @bang.setter
    def bang(self, value):
        raise MyCustomRuntimeError("BANG! A forced exception")

    @property
    def long_a(self):
        """
        A read-write attribute that takes a long time to set.
        """
        return self._long_a

    @long_a.setter
    def long_a(self, value):
        sleep(value)
        self._long_a = value

    @property
    def long_b(self):
        """
        A read-write attribute that takes a long time to set.
        """
        return self._long_b

    @long_b.setter
    def long_b(self, value):
        sleep(value)
        self._long_b = value
