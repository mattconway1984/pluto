"""
Contains custom run time errors provided by (and used by) the Pluto framework.
"""

class BadParameters(RuntimeError):
    """
    Exception used when parameters passed into an external interface are bad,
    i.e. missing args, wrong type etc.
    """

class LogicError(RuntimeError):
    """
    LogicErrors are a software fault where some logic error has been detected.
    The details for the logic error will be contained within the error.
    """
