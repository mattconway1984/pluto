#pylint:disable=missing-docstring
#pylint:enable=missing-docstring

from concurrent import futures
from logging import getLogger
from inspect import ismethod

from grpc import server as grpc_server
from pluto.event.event import GetComponentEvent
from pluto.component.component import PlutoComponent
from pluto.delegator.protobuf.delegator_pb2_grpc import add_PlutoDelegatorServicer_to_server
from pluto.delegator.servicer import PlutoDelegatorGrpc


LOGGER = getLogger("DELEGATOR")


class Delegator(PlutoComponent):
    """
    The delegator is responsible for representing all active PlutoComponents
    by allowing them to be controlled via remote access
    """

    version = "0.0.0"

    #pylint: disable=no-self-use
    def list_components(self):
        """
        Retrieve a list of active PlutoComponents
        """
        #pylint: disable=protected-access
        return PlutoComponent._components

    def list_methods(self, component):
        """
        Retrieve a list of methods for an active PlutoComponent
        """
        component_instance = GetComponentEvent.run(self.eventbus, component)
        if component_instance is None:
            raise RuntimeError(f"Component {component} does not exist")
        #pylint: disable=protected-access
        return \
            [attr for attr in component_instance._public_attrs \
                if ismethod(getattr(component_instance, attr))]

    def list_variables(self, component):
        """
        Retrieve a list of variables for an active PlutoComponent
        """
        component_instance = GetComponentEvent.run(self.eventbus, component)
        if component_instance is None:
            raise RuntimeError(f"Component {component} does not exist")
        #pylint: disable=protected-access
        return \
            [attr for attr in component_instance._public_attrs \
                if not ismethod(getattr(component_instance, attr))]

    def call_method(self, component, method, args):
        """
        Call a method on one of the active PlutoComponents
        """
        component_instance = GetComponentEvent.run(self.eventbus, component)
        if component_instance is None:
            raise RuntimeError(f"Component {component} does not exist")
        # This is not pretty, but it works
        bound_method = getattr(component_instance, method)
        decoded_args = []
        if isinstance(type(args), list):
            for arg in args:
                decoded_args.append(arg)
            result = bound_method(*decoded_args)
        elif args is not None and args != "":
            result = bound_method(args)
        else:
            result = bound_method()
        return result

    def set_variable(self, component, variable, value):
        """
        Set a public variabe of one of the active PlutoComponents
        """
        component_instance = GetComponentEvent.run(self.eventbus, component)
        if component_instance is None:
            raise RuntimeError(f"Component {component} does not exist")
        setattr(component_instance, variable, value)

    def get_variable(self, component, variable):
        """
        Get a public variabe of one of the active PlutoComponents
        """
        component_instance = GetComponentEvent.run(self.eventbus, component)
        if component_instance is None:
            raise RuntimeError(f"Component {component} does not exist")
        return getattr(component_instance, variable)

    def __init__(self, name, eventbus, port):
        super().__init__(name, eventbus)
        self._server = grpc_server(futures.ThreadPoolExecutor(max_workers=10))
        self._server.add_insecure_port("localhost:{}".format(port))
        add_PlutoDelegatorServicer_to_server(PlutoDelegatorGrpc(self), self._server)
        self._server.start()

    def stop(self):
        """
        Stop the delegator
        """
        LOGGER.info("TODO: Stop the PlutoDelegator")
        self._server.stop(0)
