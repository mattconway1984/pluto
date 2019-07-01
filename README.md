# Pluto 

Framework for developing an application based around the idea of running
experimental schedules. A collection of software components may be crafted
which share an event bus for annonymous communication with one another. 
A scheduler is provided to execute a pre-determined list of instructions
in a sequential order.

A delegate component is provided which allows a remote client to easily
interact with, and drive the system, by calling public methods and getting
and/or setting public attributes of registered software components.
