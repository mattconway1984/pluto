#pylint:skip-file

from setuptools import setup, find_namespace_packages
import versioneer

setup(
    name="pluto",
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    packages=find_namespace_packages(include=['pluto', 'pluto.*']),
    install_requires=[
        "grpcio",
    ],
    python_requires=">=3.6"
)
