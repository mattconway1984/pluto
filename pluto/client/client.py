#pylint:disable=missing-docstring
#pylint:enable=missing-docstring

from json import dumps as json_dumps
from json import loads as json_loads
from json.decoder import JSONDecodeError
from grpc import insecure_channel


import pluto.delegator.protobuf.delegator_pb2_grpc as delegator_pb2_grpc
import pluto.delegator.protobuf.delegator_pb2 as delegator_pb2
from pluto.serialise import encode, decode


class PlutoClient:
    """
    Provides remote access to a PlutoApplication
    """

    def __init__(self, address, port):
        self._channel = insecure_channel(f"{address}:{port}")
        self._stub = delegator_pb2_grpc.PlutoDelegatorStub(self._channel)

    def list_components(self):
        """
        Invoke PlutoDelegator.list_components (remotely)
        """
        response = self._stub.list_components(delegator_pb2.ListComponentsRequest())
        return response.components

    def list_methods(self, comp):
        """
        Invoke PlutoDelegator.list_methods (remotely)
        """
        request = delegator_pb2.ListMethodsRequest(component=comp)
        response = self._stub.list_methods(request)
        return response.methods

    def list_variables(self, comp):
        """
        Invoke PlutoDelegator.list_variables (remotely)
        """
        request = delegator_pb2.ListVariablesRequest(component=comp)
        response = self._stub.list_variables(request)
        return response.variables

    def call_method(self, comp, comp_method, args=None):
        """
        Invoke PlutoDelegator.call_method (remotely)
        """
        if args is None:
            args = []
        if not isinstance(args, list):
            args = [args]
        request = delegator_pb2.CallMethodRequest()
        request.component = comp
        request.method = comp_method
        for arg in args:
            request.args.append(encode(arg)) #pylint:disable=no-member
        response = self._stub.call_method(request)
        if response:
            result = decode(response)
        else:
            result = None
        return result

    def set_variable(self, comp, variable, value):
        """
        Invoke PlutoDelegator.set_variable (remotely)
        """
        request = delegator_pb2.SetVariableRequest()
        request.component = comp
        request.variable = variable
        request.value = encode(value)
        _ = self._stub.set_variable(request)

    def get_variable(self, comp, variable):
        """
        Invoke foo
        """
        request = delegator_pb2.GetVariableRequest()
        request.component = comp
        request.variable = variable
        response = self._stub.get_variable(request)
        return decode(response.value)
