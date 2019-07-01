#pylint:disable=missing-docstring
#pylint:enable=missing-docstring

from pluto.delegator.protobuf.delegator_pb2_grpc import PlutoDelegatorServicer
from pluto.delegator.protobuf.delegator_pb2 import (
    ListComponentsResponse,
    ListMethodsResponse,
    ListVariablesResponse,
    CallMethodResponse,
    GetVariableResponse,
    SetVariableResponse,
)


class PlutoDelegatorGrpc(PlutoDelegatorServicer):
    """
    This is the delegator GRPC "servicer" which is responsible for servicing
    remote requests made by clients

    :param delegator (PlutoDelegator): The PlutoDelegator component
    """

    def __init__(self, delegator):
        super().__init__()
        self._delegator = delegator

    def list_components(self, request, context):
        """
        Handle when a remote client makes a request to get a list of
        active PlutoComponents
        """
        response = ListComponentsResponse()
        for component in self._delegator.list_components():
            response.components.append(component)
        return response

    def list_methods(self, request, context):
        """
        Handle when a remote client makes a request to get a list of
        public methods exposed by a PlutoComponent
        """
        response = ListMethodsResponse()
        for method in self._delegator.list_methods(request.component):
            response.methods.append(method)
        return response

    def list_variables(self, request, context):
        """
        Handle when a remote client makes a request to get a list of
        public methods exposed by a PlutoComponent
        """
        response = ListVariablesResponse()
        for variable in self._delegator.list_variables(request.component):
            response.variables.append(variable)
        return response

    def call_method(self, request, context):
        """
        Handle when a remote client makes a request to call a method on
        one of the active PlutoComponents
        """
        response = CallMethodResponse()
        args = []
        for arg in request.args:
            args.append(decode(arg))
        if args != []:
            result = \
                self._delegator.call_method(
                    request.component, request.method, *args)
        else:
            result = \
                self._delegator.call_method(
                    request.component, request.method, None)
        response.result = encode(result)
        return response

    def set_variable(self, request, context):
        """
        Handle when a remote client makes a request to set a variable on one
        of the active PlutoComponents
        """
        response = SetVariableResponse()
        value = decode(request.value)
        self._delegator.set_variable(request.component, request.variable, value)
        return response

    def get_variable(self, request, context):
        """
        Handle when a remote client makes a request to get a variable on one
        of the active PlutoComponents
        """
        response = GetVariableResponse()
        value = self._delegator.get_variable(request.component, request.variable)
        response.value = encode(value)
        return response
