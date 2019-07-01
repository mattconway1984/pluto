"""
A demonstration script to run Pluto

This will be removed, and information added to proper documentation.
"""

from pluto.client.client import PlutoClient

if __name__ == "__main__":
    CLIENT = PlutoClient("localhost", 6000)
    CLIENT.list_components()
