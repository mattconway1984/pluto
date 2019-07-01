#pylint:disable=missing-docstring
#pylint:enable=missing-docstring


from abc import ABC, abstractproperty


class PlutoApplicationConfig(ABC):
    """
    To define the application configuration, an implementation of this
    class must exist
    """

    class Component:
        """
        Represent configuration data for a Pluto component
        """

        def __init__(self, object_class, name, *args, **kwargs):
            self._object_class = object_class
            self._name = name
            self._args = args
            self._kwargs = kwargs

        @property
        def object_class(self):
            """
            Get the class of the component to be constructed
            """
            return self._object_class

        @property
        def name(self):
            """
            Get the components name (must be unique)
            """
            return self._name

        @property
        def args(self):
            """
            Get a list of args used to construct this component
            """
            return self._args

        @property
        def kwargs(self):
            """
            Get a list of kwargs used to construct this component
            """
            return self._kwargs

    @abstractproperty
    def log_level(self):
        """
        Get the log level to use when configuring the PlutoLogger

        :returns (logging.LEVEL): The log level to set
        """
        return

    @abstractproperty
    def components(self):
        """
        Get a list of components that make up the application

        :returns: list[Component] the components to create
        """
        return
